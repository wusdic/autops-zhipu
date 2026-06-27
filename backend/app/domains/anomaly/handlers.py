"""异常检测领域事件处理器.

监听巡检完成、状态变更等事件，触发异常检测逻辑。
"""
from __future__ import annotations

import logging

from app.common.events import (
    DomainEvent,
    get_event_bus,
    StateEvents,
    AlertEvents,
    InspectionEvents,
    AnomalyEvents,
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
            logger.debug("anomaly: 跳过重复处理 key=%s", key)
            return
        if len(_processed_events) > _MAX_PROCESSED:
            _processed_events.clear()
        _processed_events.add(key)
        return await func(event)
    wrapper.__name__ = func.__name__
    wrapper.__qualname__ = func.__qualname__
    return wrapper


# ---------------------------------------------------------------------------
# 异常处理器
# ---------------------------------------------------------------------------

@idempotent_handler
async def on_state_critical(event: DomainEvent) -> None:
    """状态变为critical时自动创建异常记录."""
    payload = event.payload
    asset_id = payload.get("asset_id")
    new_status = payload.get("new_status", "")
    if new_status != "critical":
        return
    logger.info(
        "anomaly: 检测到critical状态变更 asset_id=%s, 触发异常检测",
        asset_id,
    )
    # 发布异常检测事件
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AnomalyEvents.ANOMALY_DETECTED,
        domain="anomaly",
        payload={
            "source": "state_critical",
            "asset_id": asset_id,
            "severity": "critical",
            "title": f"资产 {asset_id} 状态变为critical",
            "description": payload.get("detail", ""),
        },
    ))


@idempotent_handler
async def on_inspection_anomaly(event: DomainEvent) -> None:
    """巡检发现异常时创建异常记录."""
    payload = event.payload
    task_id = payload.get("task_id")
    anomaly_count = payload.get("anomaly_count", 0)
    logger.info(
        "anomaly: 巡检任务 %s 发现 %d 个异常",
        task_id, anomaly_count,
    )
    # 异常已被巡检中心记录，这里可以触发升级逻辑
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=NotificationEvents.NOTIFICATION_SENT,
        domain="notification",
        payload={
            "type": "alert",
            "title": f"巡检异常: {task_id}",
            "message": f"巡检任务发现 {anomaly_count} 个异常",
            "severity": payload.get("severity", "high"),
        },
    ))


@idempotent_handler
async def on_anomaly_detected(event: DomainEvent) -> None:
    """异常被检测到后，通知告警中心."""
    payload = event.payload
    severity = payload.get("severity", "medium")
    asset_id = payload.get("asset_id")
    logger.info(
        "anomaly: 异常检测完成 asset=%s severity=%s",
        asset_id, severity,
    )
    # 高严重度异常触发告警
    if severity in ("high", "critical"):
        bus = get_event_bus()
        await bus.publish(DomainEvent(
            event_type=AlertEvents.ALERT_CREATED,
            domain="alert",
            payload={
                "source": "anomaly",
                "asset_id": asset_id,
                "severity": severity,
                "title": payload.get("title", "异常检测告警"),
                "description": payload.get("description", ""),
            },
        ))


# ---------------------------------------------------------------------------
# 注册所有处理器
# ---------------------------------------------------------------------------

def register_handlers() -> None:
    """注册异常检测领域所有事件处理器."""
    bus = get_event_bus()
    bus.subscribe(StateEvents.STATE_CRITICAL, on_state_critical)
    bus.subscribe(InspectionEvents.RESULT_ANOMALY_FOUND, on_inspection_anomaly)
    bus.subscribe(AnomalyEvents.ANOMALY_DETECTED, on_anomaly_detected)
    logger.info("anomaly: 事件处理器已注册")
