"""日志中心领域事件定义."""
from __future__ import annotations

from app.common.events import (
    DomainEvent,
    get_event_bus,
    LogEvents,
)


async def publish_log_entry_created(log_id: str, log_type: str, **kwargs) -> None:
    """发布日志条目创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=LogEvents.LOG_ENTRY_CREATED,
        domain="log",
        payload={"log_id": log_id, "log_type": log_type, **kwargs},
        source="log",
    ))


async def publish_execution_log_stream(execution_id: str, stream_data: str, **kwargs) -> None:
    """发布执行日志流事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=LogEvents.EXECUTION_LOG_STREAM,
        domain="log",
        payload={"execution_id": execution_id, "stream_data": stream_data, **kwargs},
        source="log",
    ))
