"""工单中心领域事件处理器."""
from __future__ import annotations

import logging

from app.common.events import (
    DomainEvent,
    get_event_bus,
    AlertEvents,
    AutomationEvents,
    TicketEvents,
    KnowledgeEvents,
    NotificationEvents,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Idempotency guard — 防止同一事件被同一处理器重复处理
# ---------------------------------------------------------------------------
_processed_events: set[str] = set()
_MAX_PROCESSED = 50_000


def idempotent_handler(func):
    """装饰器: 防止同一事件被同一处理器重复处理."""
    async def wrapper(event):
        key = f"{getattr(event, 'event_id', '')}:{func.__name__}"
        if key in _processed_events:
            logger.debug("ticket: 跳过重复处理 key=%s", key)
            return
        if len(_processed_events) > _MAX_PROCESSED:
            _processed_events.clear()
        _processed_events.add(key)
        return await func(event)
    wrapper.__name__ = func.__name__
    wrapper.__qualname__ = func.__qualname__
    return wrapper


# ---------------------------------------------------------------------------
# 原有工单领域处理器
# ---------------------------------------------------------------------------

@idempotent_handler
async def on_alert_escalated_create_ticket(event: DomainEvent) -> None:
    """告警升级时自动创建工单."""
    payload = event.payload
    try:
        alert_id = payload.get("alert_id", "")
        title = payload.get("title", "未知告警")
        severity = payload.get("severity", "high")
        escalate_to = payload.get("escalate_to", "")
        escalation_level = payload.get("escalation_level", "")
        if not alert_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.ticket.service import TicketService

        ticket_id = None
        async with async_session_factory() as session:
            svc = TicketService(session)
            ticket = await svc.create_ticket(
                title=f"告警升级工单: {title}",
                ticket_type="incident",
                priority=severity,
                alert_ids=[alert_id],
                assigned_to=escalate_to,
                source="alert_escalation",
                details={
                    "escalation_level": escalation_level,
                    "source_event_id": event.event_id,
                },
            )
            ticket_id = str(getattr(ticket, "id", ""))
            await session.commit()

        if ticket_id:
            bus = get_event_bus()
            await bus.publish(DomainEvent(
                event_type=TicketEvents.TICKET_CREATED,
                domain="ticket",
                payload={
                    "ticket_id": ticket_id,
                    "title": f"告警升级工单: {title}",
                    "source": "alert_escalation",
                    "alert_id": alert_id,
                },
                source="ticket_handler",
                correlation_id=event.correlation_id or event.event_id,
            ))
        logger.info(
            "ticket: 告警升级创建工单 alert_id=%s ticket_id=%s",
            alert_id, ticket_id,
        )
    except Exception as e:
        logger.error("ticket: 告警升级创建工单失败: %s", e)


@idempotent_handler
async def on_execution_failed_create_ticket(event: DomainEvent) -> None:
    """自动化执行失败时自动创建工单."""
    payload = event.payload
    try:
        execution_id = payload.get("execution_id", "")
        error = payload.get("error", "")
        policy_id = payload.get("policy_id", "")
        if not execution_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.ticket.service import TicketService

        ticket_id = None
        async with async_session_factory() as session:
            svc = TicketService(session)
            ticket = await svc.create_ticket(
                title=f"自动化执行失败: {execution_id}",
                ticket_type="incident",
                priority="high",
                execution_ids=[execution_id],
                source="automation_failure",
                details={
                    "error": error,
                    "policy_id": policy_id,
                    "asset_ids": payload.get("asset_ids", []),
                    "source_event_id": event.event_id,
                },
            )
            ticket_id = str(getattr(ticket, "id", ""))
            await session.commit()

        if ticket_id:
            bus = get_event_bus()
            await bus.publish(DomainEvent(
                event_type=TicketEvents.TICKET_CREATED,
                domain="ticket",
                payload={
                    "ticket_id": ticket_id,
                    "title": f"自动化执行失败: {execution_id}",
                    "source": "automation_failure",
                    "execution_id": execution_id,
                },
                source="ticket_handler",
                correlation_id=event.event_id,
            ))
        logger.info(
            "ticket: 自动化失败创建工单 execution_id=%s ticket_id=%s",
            execution_id, ticket_id,
        )
    except Exception as e:
        logger.error("ticket: 自动化失败创建工单失败: %s", e)


@idempotent_handler
async def on_alert_acknowledged_link_ticket(event: DomainEvent) -> None:
    """告警确认时关联到已有工单."""
    payload = event.payload
    try:
        alert_id = payload.get("alert_id", "")
        acknowledged_by = payload.get("acknowledged_by", "")
        if not alert_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.ticket.service import TicketService

        async with async_session_factory() as session:
            svc = TicketService(session)
            # 查找关联该告警的工单
            tickets = await svc.list_tickets(alert_ids=[alert_id], status="open")
            for ticket in tickets:
                try:
                    await svc.add_comment(
                        ticket_id=str(ticket.id),
                        content=f"关联告警已确认 by {acknowledged_by}",
                        user_id="system",
                    )
                except Exception as e:
                    logger.warning("ticket: 添加工单评论失败: %s", e)
            await session.commit()
        logger.info("ticket: 告警确认关联工单完成 alert_id=%s", alert_id)
    except Exception as e:
        logger.error("ticket: 告警确认关联工单失败: %s", e)


# ---------------------------------------------------------------------------
# 从 common/event_handlers.py 迁移的处理器
# ---------------------------------------------------------------------------

@idempotent_handler
async def on_ticket_closed_create_knowledge(event) -> None:
    """工单关闭 → 生成知识草稿."""
    payload = event.payload
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=KnowledgeEvents.DRAFT_CREATED,
        domain="knowledge",
        payload={
            "title": f"工单总结: {payload.get('title', '未知工单')}",
            "article_type": "incident_summary",
            "source": "ticket_closure",
            "source_id": payload.get("ticket_id"),
            "context": payload.get("context", {}),
        },
        source="handler",
        correlation_id=event.event_id,
    ))


@idempotent_handler
async def on_ticket_notification(event) -> None:
    """工单分配 → 发送通知."""
    payload = event.payload
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=NotificationEvents.NOTIFICATION_SENT,
        domain="notification",
        payload={
            "type": "ticket",
            "title": f"工单分配: {payload.get('title', '')}",
            "message": f"您被分配了工单: {payload.get('title', '')}",
            "ref_id": payload.get("ticket_id"),
            "user_id": payload.get("assigned_to"),
        },
        source="handler",
        correlation_id=event.event_id,
    ))


# ---------------------------------------------------------------------------
# 注册入口
# ---------------------------------------------------------------------------

def register_handlers() -> None:
    """注册工单领域的事件处理器."""
    bus = get_event_bus()

    # 原有handlers
    bus.subscribe(AlertEvents.ALERT_ESCALATED, on_alert_escalated_create_ticket)
    bus.subscribe(AutomationEvents.EXECUTION_FAILED, on_execution_failed_create_ticket)
    bus.subscribe(AlertEvents.ALERT_ACKNOWLEDGED, on_alert_acknowledged_link_ticket)

    # 从 event_handlers 迁移
    bus.subscribe(TicketEvents.TICKET_CLOSED, on_ticket_closed_create_knowledge)
    bus.subscribe(TicketEvents.TICKET_ASSIGNED, on_ticket_notification)

    logger.info("ticket领域事件处理器已注册 (含idempotency)")
