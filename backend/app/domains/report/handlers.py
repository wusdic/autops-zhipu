"""报表中心领域事件处理器.

监听工单关闭、自动化完成等事件，触发报告生成。
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.common.events import (
    DomainEvent,
    get_event_bus,
    TicketEvents,
    AutomationEvents,
    ReportEvents,
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
            logger.debug("report: 跳过重复处理 key=%s", key)
            return
        if len(_processed_events) > _MAX_PROCESSED:
            _processed_events.clear()
        _processed_events.add(key)
        return await func(event)
    wrapper.__name__ = func.__name__
    wrapper.__qualname__ = func.__qualname__
    return wrapper


# ---------------------------------------------------------------------------
# 报表处理器
# ---------------------------------------------------------------------------

@idempotent_handler
async def on_ticket_closed(event: DomainEvent) -> None:
    """工单关闭时触发事后报告生成."""
    payload = event.payload
    ticket_id = payload.get("ticket_id")
    logger.info(
        "report: 工单 %s 已关闭, 检查是否需要生成事后报告",
        ticket_id,
    )
    # 如果工单关联了告警或异常，触发报告生成
    if payload.get("has_anomaly") or payload.get("has_alert"):
        bus = get_event_bus()
        await bus.publish(DomainEvent(
            event_type=ReportEvents.REPORT_GENERATION_REQUESTED,
            domain="report",
            payload={
                "source": "ticket_closure",
                "ticket_id": ticket_id,
                "report_type": "incident_summary",
                "title": f"事后报告 - 工单 {ticket_id}",
            },
        ))


@idempotent_handler
async def on_automation_completed(event: DomainEvent) -> None:
    """自动化执行完成后记录执行报告."""
    payload = event.payload
    execution_id = payload.get("execution_id")
    policy_id = payload.get("policy_id")
    logger.info(
        "report: 自动化执行 %s 完成 (policy=%s)",
        execution_id, policy_id,
    )
    # 自动化完成后可以生成执行报告
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=ReportEvents.REPORT_GENERATION_REQUESTED,
        domain="report",
        payload={
            "source": "automation_completion",
            "execution_id": execution_id,
            "report_type": "execution_summary",
            "title": f"执行报告 - {execution_id}",
        },
    ))


@idempotent_handler
async def on_report_generation_requested(event: DomainEvent) -> None:
    """报告生成请求处理."""
    payload = event.payload
    report_type = payload.get("report_type", "unknown")
    source = payload.get("source", "")
    logger.info(
        "report: 报告生成请求 type=%s source=%s",
        report_type, source,
    )
    # 标记生成开始
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=ReportEvents.REPORT_GENERATION_STARTED,
        domain="report",
        payload={
            "report_type": report_type,
            "source": source,
            "requested_at": datetime.now(timezone.utc).isoformat(),
        },
    ))


@idempotent_handler
async def on_report_generation_completed(event: DomainEvent) -> None:
    """报告生成完成后发送通知."""
    payload = event.payload
    report_type = payload.get("report_type", "")
    title = payload.get("title", "报告")
    logger.info("report: 报告生成完成 type=%s", report_type)
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=NotificationEvents.NOTIFICATION_SENT,
        domain="notification",
        payload={
            "type": "info",
            "title": f"报告已生成: {title}",
            "message": f"{report_type} 类型的报告已生成完成。",
        },
    ))


@idempotent_handler
async def on_report_generation_failed(event: DomainEvent) -> None:
    """报告生成失败时发送告警通知."""
    payload = event.payload
    error = payload.get("error", "未知错误")
    logger.error("report: 报告生成失败: %s", error)
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=NotificationEvents.NOTIFICATION_SENT,
        domain="notification",
        payload={
            "type": "system",
            "title": "报告生成失败",
            "message": f"错误: {error}",
            "severity": "high",
        },
    ))


# ---------------------------------------------------------------------------
# 注册所有处理器
# ---------------------------------------------------------------------------

def register_handlers() -> None:
    """注册报表领域所有事件处理器."""
    bus = get_event_bus()
    bus.subscribe(TicketEvents.TICKET_CLOSED, on_ticket_closed)
    bus.subscribe(AutomationEvents.EXECUTION_COMPLETED, on_automation_completed)
    bus.subscribe(ReportEvents.REPORT_GENERATION_REQUESTED, on_report_generation_requested)
    bus.subscribe(ReportEvents.REPORT_GENERATION_COMPLETED, on_report_generation_completed)
    bus.subscribe(ReportEvents.REPORT_GENERATION_FAILED, on_report_generation_failed)
    logger.info("report: 事件处理器已注册")
