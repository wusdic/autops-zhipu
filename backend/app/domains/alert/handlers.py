"""告警中心领域事件处理器."""

from __future__ import annotations

import logging
from collections import OrderedDict

from app.common.events import (
    DomainEvent,
    get_event_bus,
    EventEvents,
    StateEvents,
    AlertEvents,
    AutomationEvents,
    NotificationEvents,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Idempotency guard — 防止同一事件被同一处理器重复处理
# ---------------------------------------------------------------------------
# 用 OrderedDict 实现 LRU 淘汰：达上限时按插入顺序移除最旧条目，
# 而非全量 clear()（后者会在清空窗口内让重放事件被当作新事件重复处理）。
# 注意：多 worker 部署下进程内去重无效，需迁移到 Redis SETNX（后续架构演进）。
_processed_events: OrderedDict[str, None] = OrderedDict()
_MAX_PROCESSED = 50_000  # 防止内存无限增长


def idempotent_handler(func):
    """装饰器: 防止同一事件被同一处理器重复处理."""

    async def wrapper(event):
        key = f"{getattr(event, 'event_id', '')}:{func.__name__}"
        if key in _processed_events:
            logger.debug("alert: 跳过重复处理 key=%s", key)
            return
        # 先执行，成功后再登记幂等键：失败不登记，使 outbox 重试可重新执行。
        result = await func(event)
        if len(_processed_events) >= _MAX_PROCESSED:
            _processed_events.popitem(last=False)
        _processed_events[key] = None
        return result

    wrapper.__name__ = func.__name__
    wrapper.__qualname__ = func.__qualname__
    return wrapper


# ---------------------------------------------------------------------------
# 原有告警领域处理器
# ---------------------------------------------------------------------------


@idempotent_handler
async def on_event_created_match_rules(event: DomainEvent) -> None:
    """事件创建时匹配告警规则."""
    payload = event.payload
    try:
        event_type = payload.get("event_type", "")
        asset_id = payload.get("asset_id")
        if not event_type and not asset_id:
            logger.debug("alert: 事件创建缺少event_type/asset_id, 跳过规则匹配")
            return

        import json as _json

        from app.infra.database import async_session_factory
        from app.domains.alert.service import AlertService
        from app.common.events import AlertEvents as _AE

        from app.common.jsonutil import parse_json_field

        # 规则命中必须先落库 Alert，再发布带真实 alert_id 的 ALERT_CREATED 事件，
        # 否则下游（策略/AI/通知）拿到的是空 alert_id 的"虚拟告警"，关联查询断裂、
        # 告警列表也查不到这些规则触发的告警。
        matched_alerts: list[dict] = []
        async with async_session_factory() as session:
            svc = AlertService(session)
            rules = await svc.list_rules(enabled=True)
            for rule in rules:
                # event_types / asset_ids 以 JSON 字符串存储，需解析后再匹配，
                # 否则 isinstance(..., list) 恒为 False，导致规则过滤条件失效。
                rule_types = parse_json_field(rule.event_types, [])
                rule_assets = parse_json_field(rule.asset_ids, [])
                if not isinstance(rule_types, list):
                    rule_types = []
                if not isinstance(rule_assets, list):
                    rule_assets = []
                type_match = event_type in rule_types or not rule_types
                asset_match = asset_id in rule_assets if rule_assets else True
                if type_match and asset_match:
                    asset_list = [asset_id] if asset_id else []
                    alert = await svc.create_alert(
                        title=f"[规则触发] {rule.name}",
                        severity=rule.severity,
                        rule_id=str(rule.id),
                        event_ids=_json.dumps([event.event_id]),
                        asset_ids=_json.dumps(asset_list),
                        context=_json.dumps(payload, ensure_ascii=False, default=str),
                    )
                    matched_alerts.append(
                        {
                            "alert_id": str(alert.id),
                            "title": alert.title,
                            "severity": alert.severity,
                            "rule_id": str(rule.id),
                            "event_ids": [event.event_id],
                            "asset_ids": asset_list,
                            "context": payload,
                        }
                    )
            await session.commit()

        if matched_alerts:
            bus = get_event_bus()
            for alert_data in matched_alerts:
                await bus.publish(
                    DomainEvent(
                        event_type=_AE.ALERT_CREATED,
                        domain="alert",
                        payload=alert_data,
                        source="alert_engine",
                        correlation_id=event.correlation_id or event.event_id,
                    )
                )
            logger.info("alert: 事件创建匹配并落库 %d 条告警", len(matched_alerts))
        else:
            logger.debug("alert: 事件创建未匹配到告警规则 event_type=%s", event_type)
    except Exception as e:
        logger.error("alert: 事件创建匹配告警规则失败: %s", e)


@idempotent_handler
async def on_state_recovered_auto_resolve(event: DomainEvent) -> None:
    """状态恢复时自动resolve关联告警."""
    payload = event.payload
    try:
        asset_id = payload.get("asset_id")
        new_status = payload.get("new_status", "")
        if not asset_id or new_status != "normal":
            return

        from app.infra.database import async_session_factory
        from app.domains.alert.service import AlertService

        from app.common.jsonutil import parse_json_field

        async with async_session_factory() as session:
            svc = AlertService(session)
            # list_alerts 不支持 asset_id 过滤且返回 (items, total)，
            # 这里取未恢复告警后在内存按资产过滤（asset_ids 为 JSON 字符串）。
            firing_alerts, _ = await svc.list_alerts(status="firing", page_size=200)
            active_alerts = [
                a
                for a in firing_alerts
                if asset_id in parse_json_field(a.asset_ids, [])
            ]
            resolved_count = 0
            for alert in active_alerts:
                try:
                    await svc.resolve(alert_id=str(alert.id), user_id="system")
                    resolved_count += 1
                except Exception as e:
                    logger.warning(
                        "alert: 自动resolve告警失败 alert_id=%s: %s",
                        str(alert.id),
                        e,
                    )
            await session.commit()
            logger.info(
                "alert: 状态恢复自动resolve %d 条告警 asset_id=%s",
                resolved_count,
                asset_id,
            )
    except Exception as e:
        logger.error("alert: 状态恢复自动resolve告警失败: %s", e)


@idempotent_handler
async def on_event_deduplicated_suppress(event: DomainEvent) -> None:
    """事件去重时抑制重复告警."""
    payload = event.payload
    try:
        original_event_id = payload.get("original_event_id", "")
        if not original_event_id:
            return
        logger.info(
            "alert: 事件去重, 跳过重复告警 original_event_id=%s",
            original_event_id,
        )
    except Exception as e:
        logger.error("alert: 事件去重抑制告警失败: %s", e)


# ---------------------------------------------------------------------------
# 从 common/event_handlers.py 迁移的处理器
# ---------------------------------------------------------------------------


@idempotent_handler
async def on_alert_notification(event) -> None:
    """告警/升级 → 发送通知."""
    payload = event.payload
    bus = get_event_bus()
    await bus.publish(
        DomainEvent(
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
        )
    )


@idempotent_handler
async def on_execution_completed_resolve(event) -> None:
    """自动化执行完成 → 更新告警."""
    payload = event.payload
    # 更新告警状态为 resolved（如果有关联告警）
    alert_id = payload.get("alert_id")
    if alert_id:
        await _resolve_alert(
            alert_id, "auto_resolved", event.payload.get("execution_id", "")
        )


@idempotent_handler
async def on_alert_created_notify_external(event):
    """告警创建后发送外部通知."""
    try:
        from app.integrations.registry import NotificationRegistry
        from app.integrations.base import NotificationPayload

        payload = event.payload
        severity = payload.get("severity", "info")
        if severity in ("critical", "warning"):
            registry = NotificationRegistry.get_instance()
            await registry.broadcast(
                NotificationPayload(
                    title=payload.get("title", "New Alert"),
                    severity=severity,
                    alert_id=payload.get("alert_id"),
                    asset_name=payload.get("asset_name"),
                    message=payload.get("detail"),
                )
            )
    except Exception as e:
        logger.error("External notification failed: %s", e)


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# 注册入口
# ---------------------------------------------------------------------------


def register_handlers() -> None:
    """注册告警领域的事件处理器."""
    bus = get_event_bus()

    # 原有handlers
    bus.subscribe(EventEvents.EVENT_CREATED, on_event_created_match_rules)
    bus.subscribe(StateEvents.STATE_RECOVERED, on_state_recovered_auto_resolve)
    bus.subscribe(EventEvents.EVENT_DEDUPLICATED, on_event_deduplicated_suppress)

    # 从 event_handlers 迁移
    bus.subscribe(AlertEvents.ALERT_CREATED, on_alert_notification)
    bus.subscribe(AlertEvents.ALERT_ESCALATED, on_alert_notification)
    bus.subscribe(AutomationEvents.EXECUTION_COMPLETED, on_execution_completed_resolve)

    # 外部通知
    _register_external_notification_channels()
    bus.subscribe(AlertEvents.ALERT_CREATED, on_alert_created_notify_external)

    logger.info("alert领域事件处理器已注册 (含idempotency)")
