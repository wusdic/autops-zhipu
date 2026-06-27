"""工单中心领域事件定义."""
from __future__ import annotations

from app.common.events import (
    DomainEvent,
    get_event_bus,
    TicketEvents,
)


async def publish_ticket_created(ticket_id: str, title: str, **kwargs) -> None:
    """发布工单创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=TicketEvents.TICKET_CREATED,
        domain="ticket",
        payload={"ticket_id": ticket_id, "title": title, **kwargs},
        source="ticket",
    ))


async def publish_ticket_updated(ticket_id: str, **kwargs) -> None:
    """发布工单更新事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=TicketEvents.TICKET_UPDATED,
        domain="ticket",
        payload={"ticket_id": ticket_id, **kwargs},
        source="ticket",
    ))


async def publish_ticket_assigned(ticket_id: str, assignee: str, **kwargs) -> None:
    """发布工单分配事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=TicketEvents.TICKET_ASSIGNED,
        domain="ticket",
        payload={"ticket_id": ticket_id, "assignee": assignee, **kwargs},
        source="ticket",
    ))


async def publish_ticket_status_changed(ticket_id: str, old_status: str, new_status: str, **kwargs) -> None:
    """发布工单状态变更事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=TicketEvents.TICKET_STATUS_CHANGED,
        domain="ticket",
        payload={"ticket_id": ticket_id, "old_status": old_status, "new_status": new_status, **kwargs},
        source="ticket",
    ))


async def publish_ticket_comment_added(ticket_id: str, comment_id: str, **kwargs) -> None:
    """发布工单评论添加事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=TicketEvents.TICKET_COMMENT_ADDED,
        domain="ticket",
        payload={"ticket_id": ticket_id, "comment_id": comment_id, **kwargs},
        source="ticket",
    ))


async def publish_ticket_resolved(ticket_id: str, resolved_by: str, **kwargs) -> None:
    """发布工单解决事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=TicketEvents.TICKET_RESOLVED,
        domain="ticket",
        payload={"ticket_id": ticket_id, "resolved_by": resolved_by, **kwargs},
        source="ticket",
    ))


async def publish_ticket_closed(ticket_id: str, closed_by: str, **kwargs) -> None:
    """发布工单关闭事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=TicketEvents.TICKET_CLOSED,
        domain="ticket",
        payload={"ticket_id": ticket_id, "closed_by": closed_by, **kwargs},
        source="ticket",
    ))


async def publish_ticket_escalated(ticket_id: str, escalation_level: str, **kwargs) -> None:
    """发布工单升级事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=TicketEvents.TICKET_ESCALATED,
        domain="ticket",
        payload={"ticket_id": ticket_id, "escalation_level": escalation_level, **kwargs},
        source="ticket",
    ))


async def publish_ticket_converted_to_knowledge(ticket_id: str, article_id: str, **kwargs) -> None:
    """发布工单转知识事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=TicketEvents.TICKET_CONVERTED_TO_KNOWLEDGE,
        domain="ticket",
        payload={"ticket_id": ticket_id, "article_id": article_id, **kwargs},
        source="ticket",
    ))
