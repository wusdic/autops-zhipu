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
    """巡检发现异常 → 作为检测源，发布 ANOMALY_DETECTED（由 on_anomaly_detected 落库）."""
    payload = event.payload
    task_id = payload.get("task_id")
    anomaly_count = payload.get("anomaly_count", 0)
    logger.info(
        "anomaly: 巡检任务 %s 发现 %d 个异常",
        task_id, anomaly_count,
    )
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AnomalyEvents.ANOMALY_DETECTED,
        domain="anomaly",
        payload={
            "source": "inspection",
            "asset_id": payload.get("asset_id"),
            "severity": payload.get("severity", "high"),
            "title": f"巡检任务 {task_id} 发现 {anomaly_count} 个异常",
            "description": payload.get("description", ""),
        },
    ))


@idempotent_handler
async def on_alert_created_converge(event: DomainEvent) -> None:
    """告警 → 异常 的【正向收敛】：高/严重告警收敛为待处置异常案例。

    这是单向链路 Event → Alert →(收敛)→ Anomaly → Incident 的关键一环；
    异常域不再反向通知告警中心（已移除旧的 on_anomaly_detected→ALERT_CREATED）。
    """
    payload = event.payload
    severity = payload.get("severity", "medium")
    if severity not in ("high", "critical"):
        return
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AnomalyEvents.ANOMALY_DETECTED,
        domain="anomaly",
        payload={
            "source": "alert",
            "alert_id": payload.get("alert_id"),
            "asset_id": (payload.get("asset_ids") or [None])[0]
            if isinstance(payload.get("asset_ids"), list) else payload.get("asset_id"),
            "severity": severity,
            "title": payload.get("title", "告警收敛异常"),
            "description": payload.get("description", ""),
        },
    ))


@idempotent_handler
async def on_anomaly_detected(event: DomainEvent) -> None:
    """异常被检测到 → 落库为待处置异常案例（单向链路的终点持久化）.

    取代旧的"反向通知告警中心"逻辑，改为真正持久化 Anomaly 行，
    使 Event→Alert→Anomaly→Incident 单向闭环可被下游（故障工作台/工单）消费。
    """
    payload = event.payload
    severity = payload.get("severity", "medium")
    asset_id = payload.get("asset_id")
    source = payload.get("source", "unknown")

    from app.infra.database import async_session_factory
    from app.domains.anomaly.service import AnomalyService

    try:
        async with async_session_factory() as session:
            svc = AnomalyService(session)
            await svc.create_anomaly(
                title=payload.get("title", "检测到异常"),
                description=payload.get("description", ""),
                source=source,
                severity=severity,
                asset_id=asset_id,
                status="new",
                meta={k: v for k, v in payload.items()
                      if k in ("alert_id", "task_id", "detail")},
            )
            await session.commit()
        logger.info("anomaly: 已落库异常 source=%s asset=%s severity=%s", source, asset_id, severity)
    except Exception as e:
        logger.error("anomaly: 异常落库失败 source=%s: %s", source, e)


# ---------------------------------------------------------------------------
# 注册所有处理器
# ---------------------------------------------------------------------------

def register_handlers() -> None:
    """注册异常检测领域所有事件处理器（单向链路）.

    Event → Alert（告警引擎，alert/handlers）→(收敛)→ Anomaly → Incident
    - 检测源：StateCritical / 巡检异常 → ANOMALY_DETECTED
    - 收敛源：ALERT_CREATED(高/严重) → ANOMALY_DETECTED
    - 落库：ANOMALY_DETECTED → 持久化 Anomaly
    - 不再有 Anomaly→Alert 的反向链路（消除双向纠缠）
    """
    bus = get_event_bus()
    bus.subscribe(StateEvents.STATE_CRITICAL, on_state_critical)
    bus.subscribe(InspectionEvents.RESULT_ANOMALY_FOUND, on_inspection_anomaly)
    bus.subscribe(AlertEvents.ALERT_CREATED, on_alert_created_converge)
    bus.subscribe(AnomalyEvents.ANOMALY_DETECTED, on_anomaly_detected)
    logger.info("anomaly: 事件处理器已注册（单向 Event→Alert→Anomaly→Incident）")
