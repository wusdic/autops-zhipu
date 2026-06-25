"""自动化中心领域事件处理器."""
from __future__ import annotations

import logging

from app.common.events import (
    DomainEvent,
    get_event_bus,
    PolicyEvents,
    AutomationEvents,
)

logger = logging.getLogger(__name__)


async def on_policy_triggered_create_execution(event: DomainEvent) -> None:
    """策略触发时创建自动化执行."""
    payload = event.payload
    try:
        from app.common.jsonutil import parse_json_field

        policy_id = payload.get("policy_id", "")
        action_chain = parse_json_field(payload.get("action_chain"), [])
        if not isinstance(action_chain, list):
            action_chain = []
        requires_approval = payload.get("requires_approval", False)
        asset_ids = payload.get("matched_assets", [])
        alert_id = payload.get("alert_id", "")

        if not policy_id or not action_chain:
            logger.debug("automation: 策略触发但缺少执行链, policy_id=%s", policy_id)
            return

        bus = get_event_bus()

        if requires_approval:
            await bus.publish(DomainEvent(
                event_type=PolicyEvents.POLICY_APPROVAL_REQUIRED,
                domain="policy",
                payload=payload,
                source="automation_handler",
                correlation_id=event.event_id,
            ))
            logger.info("automation: 策略需审批, 已发送审批请求 policy_id=%s", policy_id)
            return

        first_action = action_chain[0] if action_chain else {}
        await bus.publish(DomainEvent(
            event_type=AutomationEvents.EXECUTION_CREATED,
            domain="automation",
            payload={
                "execution_type": first_action.get("type", "script"),
                "target_id": first_action.get("target_id"),
                "asset_ids": asset_ids,
                "trigger_source": "policy_triggered",
                "policy_id": policy_id,
                "alert_id": alert_id,
                "is_dry_run": False,
                "action_chain": action_chain,
            },
            source="automation_handler",
            correlation_id=event.event_id,
        ))
        logger.info("automation: 策略触发创建执行 policy_id=%s", policy_id)
    except Exception as e:
        logger.error("automation: 策略触发创建执行失败: %s", e)


async def on_step_completed_write_log(event: DomainEvent) -> None:
    """执行步骤完成时写入日志."""
    payload = event.payload
    try:
        execution_id = payload.get("execution_id", "")
        step_id = payload.get("step_id", "")
        if not execution_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.automation.service import AutomationService

        async with async_session_factory() as session:
            svc = AutomationService(session)
            await svc.append_execution_log(
                execution_id=execution_id,
                log_entry={
                    "step_id": step_id,
                    "status": "completed",
                    "output": payload.get("output", ""),
                    "timestamp": event.timestamp,
                },
            )
            await session.commit()
        logger.info(
            "automation: 步骤完成写入日志 execution_id=%s step_id=%s",
            execution_id, step_id,
        )
    except Exception as e:
        logger.error("automation: 步骤完成写入日志失败: %s", e)


async def on_step_failed_write_log(event: DomainEvent) -> None:
    """执行步骤失败时写入日志."""
    payload = event.payload
    try:
        execution_id = payload.get("execution_id", "")
        step_id = payload.get("step_id", "")
        error = payload.get("error", "")
        if not execution_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.automation.service import AutomationService

        async with async_session_factory() as session:
            svc = AutomationService(session)
            await svc.append_execution_log(
                execution_id=execution_id,
                log_entry={
                    "step_id": step_id,
                    "status": "failed",
                    "error": error,
                    "timestamp": event.timestamp,
                },
            )
            await session.commit()
        logger.info(
            "automation: 步骤失败写入日志 execution_id=%s step_id=%s error=%s",
            execution_id, step_id, error,
        )
    except Exception as e:
        logger.error("automation: 步骤失败写入日志失败: %s", e)


def register_handlers() -> None:
    """注册自动化领域的事件处理器."""
    bus = get_event_bus()
    bus.subscribe(PolicyEvents.POLICY_TRIGGERED, on_policy_triggered_create_execution)
    bus.subscribe(AutomationEvents.EXECUTION_STEP_COMPLETED, on_step_completed_write_log)
    bus.subscribe(AutomationEvents.EXECUTION_STEP_FAILED, on_step_failed_write_log)
    logger.info("automation领域事件处理器已注册 (3个handler)")
