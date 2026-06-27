"""策略中心领域事件定义."""
from __future__ import annotations

from app.common.events import (
    DomainEvent,
    get_event_bus,
    PolicyEvents,
)


async def publish_policy_created(policy_id: str, policy_name: str, **kwargs) -> None:
    """发布策略创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=PolicyEvents.POLICY_CREATED,
        domain="policy",
        payload={"policy_id": policy_id, "policy_name": policy_name, **kwargs},
        source="policy",
    ))


async def publish_policy_updated(policy_id: str, **kwargs) -> None:
    """发布策略更新事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=PolicyEvents.POLICY_UPDATED,
        domain="policy",
        payload={"policy_id": policy_id, **kwargs},
        source="policy",
    ))


async def publish_policy_activated(policy_id: str, activated_by: str, **kwargs) -> None:
    """发布策略激活事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=PolicyEvents.POLICY_ACTIVATED,
        domain="policy",
        payload={"policy_id": policy_id, "activated_by": activated_by, **kwargs},
        source="policy",
    ))


async def publish_policy_triggered(policy_id: str, trigger_event: str, **kwargs) -> None:
    """发布策略触发事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=PolicyEvents.POLICY_TRIGGERED,
        domain="policy",
        payload={"policy_id": policy_id, "trigger_event": trigger_event, **kwargs},
        source="policy",
    ))


async def publish_policy_simulated(policy_id: str, result: str, **kwargs) -> None:
    """发布策略模拟事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=PolicyEvents.POLICY_SIMULATED,
        domain="policy",
        payload={"policy_id": policy_id, "result": result, **kwargs},
        source="policy",
    ))


async def publish_policy_approval_required(policy_id: str, **kwargs) -> None:
    """发布策略审批请求事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=PolicyEvents.POLICY_APPROVAL_REQUIRED,
        domain="policy",
        payload={"policy_id": policy_id, **kwargs},
        source="policy",
    ))


async def publish_policy_approved(policy_id: str, approved_by: str, **kwargs) -> None:
    """发布策略审批通过事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=PolicyEvents.POLICY_APPROVED,
        domain="policy",
        payload={"policy_id": policy_id, "approved_by": approved_by, **kwargs},
        source="policy",
    ))


async def publish_policy_rejected(policy_id: str, rejected_by: str, reason: str = "", **kwargs) -> None:
    """发布策略审批拒绝事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=PolicyEvents.POLICY_REJECTED,
        domain="policy",
        payload={"policy_id": policy_id, "rejected_by": rejected_by, "reason": reason, **kwargs},
        source="policy",
    ))
