"""通知中心领域事件定义."""
from __future__ import annotations

from app.common.events import (
    DomainEvent,
    get_event_bus,
    NotificationEvents,
)


async def publish_notification_sent(notification_id: str, channel: str, recipient: str, **kwargs) -> None:
    """发布通知发送事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=NotificationEvents.NOTIFICATION_SENT,
        domain="notification",
        payload={"notification_id": notification_id, "channel": channel, "recipient": recipient, **kwargs},
        source="notification",
    ))


async def publish_notification_read(notification_id: str, read_by: str, **kwargs) -> None:
    """发布通知已读事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=NotificationEvents.NOTIFICATION_READ,
        domain="notification",
        payload={"notification_id": notification_id, "read_by": read_by, **kwargs},
        source="notification",
    ))
