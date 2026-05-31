"""事件中心领域事件定义."""
from __future__ import annotations

from app.common.events import (
    DomainEvent,
    EventBus,
    get_event_bus,
    EventEvents,
)


async def publish_event_created(event_id: str, event_type: str, **kwargs) -> None:
    """发布事件创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=EventEvents.EVENT_CREATED,
        domain="event",
        payload={"event_id": event_id, "event_type": event_type, **kwargs},
        source="event",
    ))


async def publish_event_deduplicated(event_id: str, original_event_id: str, **kwargs) -> None:
    """发布事件去重事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=EventEvents.EVENT_DEDUPLICATED,
        domain="event",
        payload={"event_id": event_id, "original_event_id": original_event_id, **kwargs},
        source="event",
    ))
