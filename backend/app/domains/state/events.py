"""状态中心领域事件定义."""
from __future__ import annotations

from app.common.events import (
    DomainEvent,
    get_event_bus,
    StateEvents,
)


async def publish_snapshot_recorded(asset_id: str, status: str, **kwargs) -> None:
    """发布状态快照记录事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=StateEvents.SNAPSHOT_RECORDED,
        domain="state",
        payload={"asset_id": asset_id, "status": status, **kwargs},
        source="state",
    ))


async def publish_state_changed(asset_id: str, old_status: str, new_status: str, **kwargs) -> None:
    """发布状态变更事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=StateEvents.STATE_CHANGED,
        domain="state",
        payload={"asset_id": asset_id, "old_status": old_status, "new_status": new_status, **kwargs},
        source="state",
    ))


async def publish_state_critical(asset_id: str, status: str, **kwargs) -> None:
    """发布状态紧急检测事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=StateEvents.STATE_CRITICAL,
        domain="state",
        payload={"asset_id": asset_id, "status": status, **kwargs},
        source="state",
    ))


async def publish_state_recovered(asset_id: str, old_status: str, new_status: str, **kwargs) -> None:
    """发布状态恢复事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=StateEvents.STATE_RECOVERED,
        domain="state",
        payload={"asset_id": asset_id, "old_status": old_status, "new_status": new_status, **kwargs},
        source="state",
    ))
