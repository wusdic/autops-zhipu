"""AIops中心领域事件定义."""
from __future__ import annotations

from app.common.events import (
    DomainEvent,
    EventBus,
    get_event_bus,
    AIOpsEvents,
)


async def publish_analysis_requested(analysis_id: str, analysis_type: str, **kwargs) -> None:
    """发布分析请求事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AIOpsEvents.ANALYSIS_REQUESTED,
        domain="aiops",
        payload={"analysis_id": analysis_id, "analysis_type": analysis_type, **kwargs},
        source="aiops",
    ))


async def publish_analysis_completed(analysis_id: str, result: str, **kwargs) -> None:
    """发布分析完成事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AIOpsEvents.ANALYSIS_COMPLETED,
        domain="aiops",
        payload={"analysis_id": analysis_id, "result": result, **kwargs},
        source="aiops",
    ))


async def publish_analysis_failed(analysis_id: str, error: str = "", **kwargs) -> None:
    """发布分析失败事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AIOpsEvents.ANALYSIS_FAILED,
        domain="aiops",
        payload={"analysis_id": analysis_id, "error": error, **kwargs},
        source="aiops",
    ))


async def publish_analysis_degraded(analysis_id: str, reason: str = "", **kwargs) -> None:
    """发布分析降级事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AIOpsEvents.ANALYSIS_DEGRADED,
        domain="aiops",
        payload={"analysis_id": analysis_id, "reason": reason, **kwargs},
        source="aiops",
    ))


async def publish_feedback_submitted(analysis_id: str, feedback: str, **kwargs) -> None:
    """发布反馈提交事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AIOpsEvents.FEEDBACK_SUBMITTED,
        domain="aiops",
        payload={"analysis_id": analysis_id, "feedback": feedback, **kwargs},
        source="aiops",
    ))
