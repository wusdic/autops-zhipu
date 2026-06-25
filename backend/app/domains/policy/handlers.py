"""策略中心领域事件处理器."""
from __future__ import annotations

import logging

from app.common.events import (
    DomainEvent,
    get_event_bus,
    AlertEvents,
    PolicyEvents,
    AutomationEvents,
)

logger = logging.getLogger(__name__)


async def on_alert_created_match_policy(event: DomainEvent) -> None:
    """告警创建时匹配策略."""
    payload = event.payload
    try:
        severity = payload.get("severity", "")
        alert_id = payload.get("alert_id", "")
        asset_ids = payload.get("asset_ids", [])
        if not severity:
            logger.debug("policy: 告警事件缺少severity, 跳过策略匹配")
            return

        from app.infra.database import async_session_factory
        from app.domains.policy.service import PolicyService
        from app.common.jsonutil import parse_json_field

        matched_policies = []
        async with async_session_factory() as session:
            svc = PolicyService(session)
            policies, _ = await svc.list_policies(status="active")
            for policy in policies:
                trigger_type = getattr(policy, "trigger_type", "")
                # trigger_condition / action_chain 以 JSON 字符串存储，必须解析，
                # 否则对字符串调用 .get()/下标会抛异常并被吞掉，策略链路静默失效。
                trigger_cond = parse_json_field(getattr(policy, "trigger_condition", None), {})
                if not isinstance(trigger_cond, dict):
                    trigger_cond = {}
                matched = False
                if trigger_type == "alert_severity":
                    target_sev = trigger_cond.get("severity", "")
                    if target_sev and severity == target_sev:
                        matched = True
                elif trigger_type == "alert_type":
                    target_type = trigger_cond.get("alert_type", "")
                    if target_type and payload.get("context", {}).get("event_type") == target_type:
                        matched = True
                elif trigger_type == "any_alert":
                    matched = True
                if matched:
                    action_chain = parse_json_field(getattr(policy, "action_chain", None), [])
                    if not isinstance(action_chain, list):
                        action_chain = []
                    matched_policies.append({
                        "policy_id": str(policy.id),
                        "policy_name": getattr(policy, "name", ""),
                        "action_chain": action_chain,
                        "requires_approval": getattr(policy, "requires_approval", False),
                        "risk_level": getattr(policy, "risk_level", "low"),
                        "matched_assets": asset_ids,
                        "alert_id": alert_id,
                    })

        if matched_policies:
            bus = get_event_bus()
            for policy_data in matched_policies:
                await bus.publish(DomainEvent(
                    event_type=PolicyEvents.POLICY_TRIGGERED,
                    domain="policy",
                    payload=policy_data,
                    source="policy_engine",
                    correlation_id=event.correlation_id or event.event_id,
                ))
            logger.info("policy: 告警匹配到 %d 条策略 alert_id=%s", len(matched_policies), alert_id)
        else:
            logger.debug("policy: 告警未匹配到策略 alert_id=%s severity=%s", alert_id, severity)
    except Exception as e:
        logger.error("policy: 告警匹配策略失败: %s", e)


async def on_policy_approved_trigger_execution(event: DomainEvent) -> None:
    """策略审批通过时触发执行."""
    payload = event.payload
    try:
        from app.common.jsonutil import parse_json_field

        policy_id = payload.get("policy_id", "")
        action_chain = parse_json_field(payload.get("action_chain"), [])
        if not isinstance(action_chain, list):
            action_chain = []
        asset_ids = payload.get("matched_assets", [])
        alert_id = payload.get("alert_id", "")

        if not policy_id or not action_chain:
            logger.debug("policy: 策略审批通过但缺少执行链, policy_id=%s", policy_id)
            return

        bus = get_event_bus()
        first_action = action_chain[0] if action_chain else {}
        await bus.publish(DomainEvent(
            event_type=AutomationEvents.EXECUTION_CREATED,
            domain="automation",
            payload={
                "execution_type": first_action.get("type", "script"),
                "target_id": first_action.get("target_id"),
                "asset_ids": asset_ids,
                "trigger_source": "policy_approved",
                "policy_id": policy_id,
                "alert_id": alert_id,
                "is_dry_run": False,
                "action_chain": action_chain,
            },
            source="policy_handler",
            correlation_id=event.event_id,
        ))
        logger.info("policy: 策略审批通过触发执行 policy_id=%s", policy_id)
    except Exception as e:
        logger.error("policy: 策略审批通过触发执行失败: %s", e)


async def on_policy_rejected_notify(event: DomainEvent) -> None:
    """策略审批拒绝时记录日志."""
    payload = event.payload
    try:
        policy_id = payload.get("policy_id", "")
        rejected_by = payload.get("rejected_by", "")
        reason = payload.get("reason", "")
        logger.info(
            "policy: 策略审批拒绝 policy_id=%s rejected_by=%s reason=%s",
            policy_id, rejected_by, reason,
        )
    except Exception as e:
        logger.error("policy: 策略拒绝处理失败: %s", e)


def register_handlers() -> None:
    """注册策略领域的事件处理器."""
    bus = get_event_bus()
    bus.subscribe(AlertEvents.ALERT_CREATED, on_alert_created_match_policy)
    bus.subscribe(PolicyEvents.POLICY_APPROVED, on_policy_approved_trigger_execution)
    bus.subscribe(PolicyEvents.POLICY_REJECTED, on_policy_rejected_notify)
    logger.info("policy领域事件处理器已注册 (3个handler)")
