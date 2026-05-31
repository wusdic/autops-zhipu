"""AUTOPS 领域间事件处理器注册中心.

在应用启动时将所有领域的 handlers 注册到 EventBus，
建立领域间的联动链路。
"""
from __future__ import annotations

import logging

from app.common.events import (
    EventBus,
    get_event_bus,
    AssetEvents,
    CollectorEvents,
    StateEvents,
    EventEvents,
    AlertEvents,
    PolicyEvents,
    AutomationEvents,
    AIOpsEvents,
    KnowledgeEvents,
    TicketEvents,
    GovernanceEvents,
    LogEvents,
    NotificationEvents,
    ConfigEvents,
)

logger = logging.getLogger(__name__)

_handlers_registered = False


async def on_alert_created_match_policy(event):
    """告警创建后自动匹配策略（通过 PolicyService.match_and_execute 闭环）."""
    try:
        from app.infra.database import async_session_factory
        from app.domains.policy.service import PolicyService

        payload = event.payload
        alert_id = payload.get("alert_id", "")
        event_type = payload.get("event_type", "")
        severity = payload.get("severity", "info")
        asset_ids = payload.get("asset_ids", [])

        async with async_session_factory() as session:
            policy_svc = PolicyService(session)
            match = await policy_svc.match_and_execute(
                event_type=event_type,
                severity=severity,
                asset_ids=asset_ids,
                alert_id=alert_id,
            )
            if match:
                logger.info(f"Policy matched and execution created: {match}")
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to match policy for alert: {e}")


def register_all_handlers() -> None:
    """注册所有领域事件处理器（幂等，只执行一次）."""
    global _handlers_registered
    if _handlers_registered:
        return
    _handlers_registered = True

    bus = get_event_bus()

    # ====== 核心联动链路 ======

    # 1. 状态变更 → 创建事件
    bus.subscribe(StateEvents.STATE_CHANGED, _on_state_changed)
    bus.subscribe(StateEvents.STATE_CRITICAL, _on_state_critical)
    bus.subscribe(StateEvents.STATE_RECOVERED, _on_state_recovered)

    # 2. 事件 → 触发告警规则匹配
    bus.subscribe(EventEvents.EVENT_CREATED, _on_event_created)

    # 3. 告警 → 触发策略匹配
    bus.subscribe(AlertEvents.ALERT_CREATED, _on_alert_created)
    bus.subscribe(AlertEvents.ALERT_CREATED, on_alert_created_match_policy)
    bus.subscribe(AlertEvents.ALERT_ESCALATED, _on_alert_escalated)

    # 4. 策略触发 → 创建自动化执行
    bus.subscribe(PolicyEvents.POLICY_TRIGGERED, _on_policy_triggered)
    bus.subscribe(PolicyEvents.POLICY_APPROVED, _on_policy_approved)

    # 5. 自动化执行完成 → 更新告警/工单
    bus.subscribe(AutomationEvents.EXECUTION_COMPLETED, _on_execution_completed)
    bus.subscribe(AutomationEvents.EXECUTION_FAILED, _on_execution_failed)

    # 6. 工单关闭 → 生成知识草稿
    bus.subscribe(TicketEvents.TICKET_CLOSED, _on_ticket_closed)

    # 7. 采集完成 → 更新状态
    bus.subscribe(CollectorEvents.JOB_COMPLETED, _on_collection_completed)
    bus.subscribe(CollectorEvents.JOB_FAILED, _on_collection_failed)

    # 8. 告警 → 发通知
    bus.subscribe(AlertEvents.ALERT_CREATED, _on_alert_notification)
    bus.subscribe(AlertEvents.ALERT_ESCALATED, _on_alert_notification)
    bus.subscribe(TicketEvents.TICKET_ASSIGNED, _on_ticket_notification)

    # 9. 全局审计日志（通配处理器）
    bus.subscribe_all(_on_any_event_audit)

    # 10. 外部通知渠道
    _register_external_notification_channels()
    bus.subscribe(AlertEvents.ALERT_CREATED, on_alert_created_notify_external)

    logger.info("EventBus: 所有领域事件处理器已注册 (10个联动链路)")


# ============================================================
# 处理器实现
# ============================================================

async def _on_state_changed(event) -> None:
    """状态变更 → 在事件中心创建事件."""
    from app.common.events import DomainEvent, EventEvents
    bus = get_event_bus()
    payload = event.payload
    new_event = DomainEvent(
        event_type="state_change",
        domain="event",
        payload={
            "asset_id": payload.get("asset_id"),
            "state_type": payload.get("state_type"),
            "old_status": payload.get("old_status"),
            "new_status": payload.get("new_status"),
            "source_event_id": event.event_id,
        },
        source="state",
        correlation_id=event.event_id,
    )
    # 通过 EventService 创建事件记录
    await _create_event_record(new_event)
    await bus.publish(DomainEvent(
        event_type=EventEvents.EVENT_CREATED,
        domain="event",
        payload={"event_type": "state_change", "asset_id": payload.get("asset_id")},
        source="handler",
        correlation_id=event.event_id,
    ))


async def _on_state_critical(event) -> None:
    """状态变critical → 创建高优先级事件."""
    from app.common.events import DomainEvent, EventEvents
    payload = event.payload
    await _create_event_record(DomainEvent(
        event_type="threshold_exceeded",
        domain="event",
        payload={
            "asset_id": payload.get("asset_id"),
            "state_type": payload.get("state_type"),
            "severity": "critical",
            "source_event_id": event.event_id,
        },
        source="state",
        correlation_id=event.event_id,
        priority=2,
    ))


async def _on_state_recovered(event) -> None:
    """状态恢复 → 创建恢复事件（用于自动resolved告警）."""
    payload = event.payload
    await _create_event_record(DomainEvent(
        event_type="state_recovered",
        domain="event",
        payload={
            "asset_id": payload.get("asset_id"),
            "state_type": payload.get("state_type"),
            "old_status": payload.get("old_status"),
            "new_status": "normal",
            "source_event_id": event.event_id,
        },
        source="state",
        correlation_id=event.event_id,
    ))


async def _on_event_created(event) -> None:
    """事件创建 → 匹配告警规则."""
    from app.common.events import DomainEvent
    payload = event.payload
    matched_alerts = await _match_alert_rules(payload)
    bus = get_event_bus()
    for alert_data in matched_alerts:
        await bus.publish(DomainEvent(
            event_type=AlertEvents.ALERT_CREATED,
            domain="alert",
            payload=alert_data,
            source="alert_engine",
            correlation_id=event.correlation_id or event.event_id,
        ))


async def _on_alert_created(event) -> None:
    """告警创建 → 触发策略匹配."""
    from app.common.events import DomainEvent
    payload = event.payload
    matched_policies = await _match_policies(payload)
    bus = get_event_bus()
    for policy_data in matched_policies:
        await bus.publish(DomainEvent(
            event_type=PolicyEvents.POLICY_TRIGGERED,
            domain="policy",
            payload=policy_data,
            source="policy_engine",
            correlation_id=event.correlation_id or event.event_id,
        ))


async def _on_alert_escalated(event) -> None:
    """告警升级 → 创建工单."""
    from app.common.events import DomainEvent
    payload = event.payload
    await bus.publish(DomainEvent(
        event_type=TicketEvents.TICKET_CREATED,
        domain="ticket",
        payload={
            "title": f"告警升级工单: {payload.get('title', '未知告警')}",
            "ticket_type": "incident",
            "priority": payload.get("severity", "high"),
            "alert_ids": [payload.get("alert_id")],
            "assigned_to": payload.get("escalate_to"),
            "source": "alert_escalation",
        },
        source="handler",
        correlation_id=event.correlation_id or event.event_id,
    ))


async def _on_policy_triggered(event) -> None:
    """策略触发 → 检查是否需要审批/直接执行."""
    from app.common.events import DomainEvent
    payload = event.payload
    bus = get_event_bus()

    requires_approval = payload.get("requires_approval", False)
    if requires_approval:
        await bus.publish(DomainEvent(
            event_type=PolicyEvents.POLICY_APPROVAL_REQUIRED,
            domain="policy",
            payload=payload,
            source="handler",
            correlation_id=event.event_id,
        ))
    else:
        await bus.publish(DomainEvent(
            event_type=AutomationEvents.EXECUTION_CREATED,
            domain="automation",
            payload={
                "execution_type": payload.get("action_chain", [{}])[0].get("type", "script"),
                "target_id": payload.get("action_chain", [{}])[0].get("target_id"),
                "asset_ids": payload.get("matched_assets", []),
                "trigger_source": "policy",
                "policy_id": payload.get("policy_id"),
                "alert_id": payload.get("alert_id"),
                "is_dry_run": False,
            },
            source="handler",
            correlation_id=event.event_id,
        ))


async def _on_policy_approved(event) -> None:
    """策略审批通过 → 创建执行."""
    from app.common.events import DomainEvent
    payload = event.payload
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AutomationEvents.EXECUTION_CREATED,
        domain="automation",
        payload={
            "execution_type": payload.get("action_chain", [{}])[0].get("type", "script"),
            "target_id": payload.get("action_chain", [{}])[0].get("target_id"),
            "asset_ids": payload.get("matched_assets", []),
            "trigger_source": "policy",
            "policy_id": payload.get("policy_id"),
            "alert_id": payload.get("alert_id"),
            "is_dry_run": False,
        },
        source="handler",
        correlation_id=event.event_id,
    ))


async def _on_execution_completed(event) -> None:
    """自动化执行完成 → 记录到资产时间线 + 更新告警."""
    payload = event.payload
    # 更新告警状态为 resolved（如果有关联告警）
    alert_id = payload.get("alert_id")
    if alert_id:
        await _resolve_alert(alert_id, "auto_resolved", event.payload.get("execution_id"))


async def _on_execution_failed(event) -> None:
    """自动化执行失败 → 创建工单."""
    from app.common.events import DomainEvent
    payload = event.payload
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=TicketEvents.TICKET_CREATED,
        domain="ticket",
        payload={
            "title": f"自动化执行失败: {payload.get('execution_id', '未知')}",
            "ticket_type": "incident",
            "priority": "high",
            "execution_ids": [payload.get("execution_id")],
            "source": "automation_failure",
        },
        source="handler",
        correlation_id=event.event_id,
    ))


async def _on_ticket_closed(event) -> None:
    """工单关闭 → 生成知识草稿."""
    from app.common.events import DomainEvent
    payload = event.payload
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=KnowledgeEvents.DRAFT_CREATED,
        domain="knowledge",
        payload={
            "title": f"工单总结: {payload.get('title', '未知工单')}",
            "article_type": "incident_summary",
            "source": "ticket_closure",
            "source_id": payload.get("ticket_id"),
            "context": payload.get("context", {}),
        },
        source="handler",
        correlation_id=event.event_id,
    ))


async def _on_collection_completed(event) -> None:
    """采集完成 → 更新状态快照."""
    payload = event.payload
    # 结果数据用于更新状态快照
    await _update_state_from_collection(payload)


async def _on_collection_failed(event) -> None:
    """采集失败 → 记录到日志 + 可选通知."""
    payload = event.payload
    logger.warning(
        "采集失败: job_id=%s asset_id=%s error=%s",
        payload.get("job_id"), payload.get("asset_id"), payload.get("error")
    )


async def _on_alert_notification(event) -> None:
    """告警/升级 → 发送通知."""
    from app.common.events import DomainEvent
    payload = event.payload
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=NotificationEvents.NOTIFICATION_SENT,
        domain="notification",
        payload={
            "type": "alert",
            "title": payload.get("title", "告警通知"),
            "message": f"告警: {payload.get('title', '')} 严重度: {payload.get('severity', '')}",
            "ref_id": payload.get("alert_id"),
        },
        source="handler",
        correlation_id=event.event_id,
    ))


async def _on_ticket_notification(event) -> None:
    """工单分配 → 发送通知."""
    from app.common.events import DomainEvent
    payload = event.payload
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=NotificationEvents.NOTIFICATION_SENT,
        domain="notification",
        payload={
            "type": "ticket",
            "title": f"工单分配: {payload.get('title', '')}",
            "message": f"您被分配了工单: {payload.get('title', '')}",
            "ref_id": payload.get("ticket_id"),
            "user_id": payload.get("assigned_to"),
        },
        source="handler",
        correlation_id=event.event_id,
    ))


async def _on_any_event_audit(event) -> None:
    """全局审计: 记录所有事件到审计日志."""
    logger.debug(
        "AUDIT event_id=%s type=%s domain=%s source=%s",
        event.event_id, event.event_type, event.domain, event.source
    )


# ============================================================
# 辅助函数 — 调用各领域 Service
# ============================================================

async def _create_event_record(event) -> None:
    """在事件中心创建事件记录."""
    try:
        from app.infra.database import async_session_factory
        from app.domains.event.service import EventService
        async with async_session_factory() as session:
            svc = EventService(session)
            await svc.create_event(
                event_type=event.payload.get("event_type") or event.event_type,
                source=event.source or event.domain,
                asset_id=event.payload.get("asset_id"),
                severity=event.payload.get("severity", "info"),
                details=event.payload,
            )
            await session.commit()
    except Exception as e:
        logger.error("创建事件记录失败: %s", e)


async def _match_alert_rules(event_payload: dict) -> list[dict]:
    """匹配告警规则，返回匹配到的告警数据列表."""
    try:
        from app.infra.database import async_session_factory
        from app.domains.alert.service import AlertService
        async with async_session_factory() as session:
            svc = AlertService(session)
            rules = await svc.list_rules(enabled_only=True)
            results = []
            event_type = event_payload.get("event_type", "")
            asset_id = event_payload.get("asset_id")
            for rule in rules:
                # 简单匹配: 检查event_type是否在rule的event_types中
                rule_types = rule.event_types if isinstance(rule.event_types, list) else []
                if event_type in rule_types or not rule_types:
                    results.append({
                        "title": f"[规则触发] {rule.name}",
                        "severity": rule.severity,
                        "rule_id": str(rule.id),
                        "event_ids": [],
                        "asset_ids": [asset_id] if asset_id else [],
                        "context": event_payload,
                    })
            return results
    except Exception as e:
        logger.error("匹配告警规则失败: %s", e)
        return []


async def _match_policies(alert_payload: dict) -> list[dict]:
    """匹配策略，返回匹配到的策略数据列表."""
    try:
        from app.infra.database import async_session_factory
        from app.domains.policy.service import PolicyService
        async with async_session_factory() as session:
            svc = PolicyService(session)
            policies, _ = await svc.list_policies(status="active")
            results = []
            severity = alert_payload.get("severity", "")
            for policy in policies:
                trigger_type = policy.trigger_type
                matched = False
                if trigger_type == "alert_severity" and severity:
                    trigger_cond = policy.trigger_condition or {}
                    target_sev = trigger_cond.get("severity", "")
                    if target_sev and severity == target_sev:
                        matched = True
                elif trigger_type == "event_type":
                    trigger_cond = policy.trigger_condition or {}
                    target_type = trigger_cond.get("event_type", "")
                    if target_type and alert_payload.get("event_type") == target_type:
                        matched = True
                if matched:
                    results.append({
                        "policy_id": str(policy.id),
                        "policy_name": policy.name,
                        "action_chain": policy.action_chain or [],
                        "requires_approval": policy.requires_approval,
                        "risk_level": policy.risk_level,
                        "matched_assets": alert_payload.get("asset_ids", []),
                        "alert_id": alert_payload.get("alert_id") or alert_payload.get("rule_id"),
                    })
            return results
    except Exception as e:
        logger.error("匹配策略失败: %s", e)
        return []


async def _resolve_alert(alert_id: str, reason: str, execution_id: str = "") -> None:
    """自动解决告警."""
    try:
        from app.infra.database import async_session_factory
        from app.domains.alert.service import AlertService
        async with async_session_factory() as session:
            svc = AlertService(session)
            await svc.resolve(alert_id=alert_id, user_id="system")
            await session.commit()
    except Exception as e:
        logger.error("自动解决告警失败: %s", e)


async def _update_state_from_collection(payload: dict) -> None:
    """采集结果 → 更新状态快照."""
    try:
        from app.infra.database import async_session_factory
        from app.domains.state.service import StateService
        from app.domains.state.schemas import StateSnapshotCreate
        async with async_session_factory() as session:
            svc = StateService(session)
            result_data = payload.get("result_data", {})
            asset_id = payload.get("asset_id")
            if asset_id and result_data:
                # 根据采集结果创建状态快照
                for state_type, value in result_data.items():
                    if isinstance(value, dict) and "status" in value:
                        await svc.record_snapshot(StateSnapshotCreate(
                            asset_id=asset_id,
                            state_type=state_type,
                            status=value["status"],
                            value=value,
                        ))
                await session.commit()
    except Exception as e:
        logger.error("更新状态快照失败: %s", e)


def _register_external_notification_channels() -> None:
    """注册外部通知渠道."""
    from app.integrations.registry import NotificationRegistry
    from app.integrations.webhook import WebhookChannel
    from app.integrations.dingtalk import DingTalkChannel
    from app.integrations.email_channel import EmailChannel

    notif_registry = NotificationRegistry.get_instance()
    notif_registry.register(WebhookChannel(enabled=False))
    notif_registry.register(DingTalkChannel(enabled=False))
    notif_registry.register(EmailChannel(enabled=False))


async def on_alert_created_notify_external(event):
    """告警创建后发送外部通知."""
    try:
        from app.integrations.registry import NotificationRegistry
        from app.integrations.base import NotificationPayload
        payload = event.payload
        severity = payload.get("severity", "info")
        if severity in ("critical", "warning"):
            registry = NotificationRegistry.get_instance()
            await registry.broadcast(NotificationPayload(
                title=payload.get("title", "New Alert"),
                severity=severity,
                alert_id=payload.get("alert_id"),
                asset_name=payload.get("asset_name"),
                message=payload.get("detail"),
            ))
    except Exception as e:
        logger.error(f"External notification failed: {e}")
