"""自动化中心领域事件定义."""
from __future__ import annotations

from app.common.events import (
    DomainEvent,
    get_event_bus,
    AutomationEvents,
)


async def publish_script_created(script_id: str, script_name: str, **kwargs) -> None:
    """发布脚本创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AutomationEvents.SCRIPT_CREATED,
        domain="automation",
        payload={"script_id": script_id, "script_name": script_name, **kwargs},
        source="automation",
    ))


async def publish_playbook_created(playbook_id: str, playbook_name: str, **kwargs) -> None:
    """发布剧本创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AutomationEvents.PLAYBOOK_CREATED,
        domain="automation",
        payload={"playbook_id": playbook_id, "playbook_name": playbook_name, **kwargs},
        source="automation",
    ))


async def publish_execution_created(execution_id: str, playbook_id: str, **kwargs) -> None:
    """发布执行创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AutomationEvents.EXECUTION_CREATED,
        domain="automation",
        payload={"execution_id": execution_id, "playbook_id": playbook_id, **kwargs},
        source="automation",
    ))


async def publish_execution_approved(execution_id: str, approved_by: str, **kwargs) -> None:
    """发布执行审批通过事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AutomationEvents.EXECUTION_APPROVED,
        domain="automation",
        payload={"execution_id": execution_id, "approved_by": approved_by, **kwargs},
        source="automation",
    ))


async def publish_execution_started(execution_id: str, **kwargs) -> None:
    """发布执行开始事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AutomationEvents.EXECUTION_STARTED,
        domain="automation",
        payload={"execution_id": execution_id, **kwargs},
        source="automation",
    ))


async def publish_execution_step_completed(execution_id: str, step_id: str, **kwargs) -> None:
    """发布执行步骤完成事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AutomationEvents.EXECUTION_STEP_COMPLETED,
        domain="automation",
        payload={"execution_id": execution_id, "step_id": step_id, **kwargs},
        source="automation",
    ))


async def publish_execution_step_failed(execution_id: str, step_id: str, error: str = "", **kwargs) -> None:
    """发布执行步骤失败事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AutomationEvents.EXECUTION_STEP_FAILED,
        domain="automation",
        payload={"execution_id": execution_id, "step_id": step_id, "error": error, **kwargs},
        source="automation",
    ))


async def publish_execution_completed(execution_id: str, **kwargs) -> None:
    """发布执行完成事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AutomationEvents.EXECUTION_COMPLETED,
        domain="automation",
        payload={"execution_id": execution_id, **kwargs},
        source="automation",
    ))


async def publish_execution_failed(execution_id: str, error: str = "", **kwargs) -> None:
    """发布执行失败事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AutomationEvents.EXECUTION_FAILED,
        domain="automation",
        payload={"execution_id": execution_id, "error": error, **kwargs},
        source="automation",
    ))


async def publish_execution_cancelled(execution_id: str, cancelled_by: str = "", **kwargs) -> None:
    """发布执行取消事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AutomationEvents.EXECUTION_CANCELLED,
        domain="automation",
        payload={"execution_id": execution_id, "cancelled_by": cancelled_by, **kwargs},
        source="automation",
    ))


async def publish_execution_rolled_back(execution_id: str, **kwargs) -> None:
    """发布执行回滚事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AutomationEvents.EXECUTION_ROLLED_BACK,
        domain="automation",
        payload={"execution_id": execution_id, **kwargs},
        source="automation",
    ))


async def publish_dry_run_completed(execution_id: str, result: str, **kwargs) -> None:
    """发布试运行完成事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AutomationEvents.DRY_RUN_COMPLETED,
        domain="automation",
        payload={"execution_id": execution_id, "result": result, **kwargs},
        source="automation",
    ))
