"""巡检中心领域事件处理器.

监听采集完成、计划触发等事件，驱动巡检执行。
"""
from __future__ import annotations

import logging

from app.common.events import (
    DomainEvent,
    get_event_bus,
    CollectorEvents,
    AnomalyEvents,
    InspectionEvents,
    NotificationEvents,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Idempotency guard
# ---------------------------------------------------------------------------
_processed_events: set[str] = set()
_MAX_PROCESSED = 50_000


def idempotent_handler(func):
    """装饰器: 防止同一事件被同一处理器重复处理."""
    async def wrapper(event):
        key = f"{getattr(event, 'event_id', '')}:{func.__name__}"
        if key in _processed_events:
            logger.debug("inspection: 跳过重复处理 key=%s", key)
            return
        if len(_processed_events) > _MAX_PROCESSED:
            _processed_events.clear()
        _processed_events.add(key)
        return await func(event)
    wrapper.__name__ = func.__name__
    wrapper.__qualname__ = func.__qualname__
    return wrapper


# ---------------------------------------------------------------------------
# 巡检处理器
# ---------------------------------------------------------------------------

@idempotent_handler
async def on_collector_job_completed(event: DomainEvent) -> None:
    """采集任务完成后触发关联巡检检查."""
    payload = event.payload
    job_id = payload.get("job_id")
    collector_type = payload.get("collector_type", "")
    logger.info(
        "inspection: 采集任务 %s 完成 (type=%s), 检查是否需要触发巡检",
        job_id, collector_type,
    )
    # 采集完成后，如果有绑定巡检模板的资产，触发自动巡检
    if payload.get("status") == "success" and payload.get("anomaly_detected"):
        bus = get_event_bus()
        await bus.publish(DomainEvent(
            event_type=InspectionEvents.RESULT_ANOMALY_FOUND,
            domain="inspection",
            payload={
                "source": "collector_job",
                "task_id": job_id,
                "anomaly_count": 1,
                "severity": "medium",
                "detail": payload.get("detail", "采集结果检测到异常"),
            },
        ))


@idempotent_handler
async def on_inspection_task_completed(event: DomainEvent) -> None:
    """巡检任务完成后处理结果."""
    payload = event.payload
    task_id = payload.get("task_id")
    result_summary = payload.get("result_summary", {})
    anomaly_count = result_summary.get("anomaly_count", 0)
    logger.info(
        "inspection: 巡检任务 %s 完成, 异常数=%d",
        task_id, anomaly_count,
    )
    # 如果发现异常，通知异常检测中心
    if anomaly_count > 0:
        bus = get_event_bus()
        await bus.publish(DomainEvent(
            event_type=AnomalyEvents.ANOMALY_DETECTED,
            domain="anomaly",
            payload={
                "source": "inspection_task",
                "task_id": task_id,
                "severity": result_summary.get("max_severity", "medium"),
                "title": f"巡检任务 {task_id} 发现 {anomaly_count} 个异常",
                "anomaly_count": anomaly_count,
            },
        ))


@idempotent_handler
async def on_inspection_task_failed(event: DomainEvent) -> None:
    """巡检任务失败时发送通知."""
    payload = event.payload
    task_id = payload.get("task_id")
    error = payload.get("error", "未知错误")
    logger.warning("inspection: 巡检任务 %s 失败: %s", task_id, error)
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=NotificationEvents.NOTIFICATION_SENT,
        domain="notification",
        payload={
            "type": "system",
            "title": f"巡检任务失败: {task_id}",
            "message": f"错误: {error}",
            "severity": "high",
        },
    ))


@idempotent_handler
async def on_plan_created(event: DomainEvent) -> None:
    """巡检计划创建时发送通知."""
    payload = event.payload
    plan_id = payload.get("plan_id")
    plan_name = payload.get("name", "")
    logger.info("inspection: 巡检计划 %s 已创建: %s", plan_id, plan_name)
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=NotificationEvents.NOTIFICATION_SENT,
        domain="notification",
        payload={
            "type": "info",
            "title": f"巡检计划已创建: {plan_name}",
            "message": f"计划 {plan_name} 已创建，将按计划自动执行巡检。",
        },
    ))


# ---------------------------------------------------------------------------
# 注册所有处理器
# ---------------------------------------------------------------------------

def register_handlers() -> None:
    """注册巡检领域所有事件处理器."""
    bus = get_event_bus()
    bus.subscribe(CollectorEvents.JOB_COMPLETED, on_collector_job_completed)
    bus.subscribe(InspectionEvents.TASK_COMPLETED, on_inspection_task_completed)
    bus.subscribe(InspectionEvents.TASK_FAILED, on_inspection_task_failed)
    bus.subscribe(InspectionEvents.PLAN_CREATED, on_plan_created)
    logger.info("inspection: 事件处理器已注册")
