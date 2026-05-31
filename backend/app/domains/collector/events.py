"""采集中心领域事件定义."""
from __future__ import annotations

from app.common.events import (
    DomainEvent,
    EventBus,
    get_event_bus,
    CollectorEvents,
)


async def publish_collector_registered(collector_id: str, collector_name: str, **kwargs) -> None:
    """发布采集器注册事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=CollectorEvents.COLLECTOR_REGISTERED,
        domain="collector",
        payload={"collector_id": collector_id, "collector_name": collector_name, **kwargs},
        source="collector",
    ))


async def publish_collector_health_changed(collector_id: str, old_health: str, new_health: str, **kwargs) -> None:
    """发布采集器健康状态变更事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=CollectorEvents.COLLECTOR_HEALTH_CHANGED,
        domain="collector",
        payload={"collector_id": collector_id, "old_health": old_health, "new_health": new_health, **kwargs},
        source="collector",
    ))


async def publish_job_created(job_id: str, collector_id: str, **kwargs) -> None:
    """发布采集任务创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=CollectorEvents.JOB_CREATED,
        domain="collector",
        payload={"job_id": job_id, "collector_id": collector_id, **kwargs},
        source="collector",
    ))


async def publish_job_completed(job_id: str, collector_id: str, **kwargs) -> None:
    """发布采集任务完成事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=CollectorEvents.JOB_COMPLETED,
        domain="collector",
        payload={"job_id": job_id, "collector_id": collector_id, **kwargs},
        source="collector",
    ))


async def publish_job_failed(job_id: str, collector_id: str, error: str = "", **kwargs) -> None:
    """发布采集任务失败事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=CollectorEvents.JOB_FAILED,
        domain="collector",
        payload={"job_id": job_id, "collector_id": collector_id, "error": error, **kwargs},
        source="collector",
    ))


async def publish_job_timeout(job_id: str, collector_id: str, **kwargs) -> None:
    """发布采集任务超时事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=CollectorEvents.JOB_TIMEOUT,
        domain="collector",
        payload={"job_id": job_id, "collector_id": collector_id, **kwargs},
        source="collector",
    ))
