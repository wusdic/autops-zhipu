"""工单中心 Service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.common.repository import BaseRepository
from app.domains.ticket.models import Ticket, TicketComment
from app.domains.ticket.schemas import TicketCreate, TicketUpdate


# 工单状态机：定义合法的状态转换
TICKET_TRANSITIONS = {
    "open": ["assigned", "closed"],
    "assigned": ["in_progress", "closed"],
    "in_progress": ["pending_approval", "resolved", "closed"],
    "pending_approval": ["resolved", "rejected", "in_progress"],
    "resolved": ["closed"],
    "closed": [],  # 终态
    "rejected": ["in_progress", "closed"],
}


class TicketService:
    """工单业务逻辑."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.ticket_repo = BaseRepository(session, Ticket)
        self.comment_repo = BaseRepository(session, TicketComment)

    async def create_ticket(self, data: TicketCreate, user_id: str | None = None) -> Ticket:
        ticket = await self.ticket_repo.create(**data.model_dump(), created_by=user_id)
        await self.session.flush()
        await self.session.refresh(ticket)
        return ticket

    async def transition_ticket(self, ticket_id: str, new_status: str, user_id: str = "") -> Ticket:
        """验证状态转换是否合法并执行转换."""
        ticket = await self.get_ticket(ticket_id)
        current = ticket.status
        allowed = TICKET_TRANSITIONS.get(current, [])
        if new_status not in allowed:
            raise ValueError(f"不允许的状态转换: {current} → {new_status}")
        return await self.update_ticket(ticket_id, TicketUpdate(status=new_status), user_id=user_id)

    async def create_from_alert(self, alert_id: str, title: str, severity: str, context: dict = None, user_id: str = "") -> Ticket:
        """从告警自动创建工单."""
        priority_map = {"critical": "critical", "warning": "high", "info": "medium"}
        priority = priority_map.get(severity, "medium")
        ticket = await self.create_ticket(TicketCreate(
            title=title,
            ticket_type="incident",
            priority=priority,
            context=context or {},
            alert_ids=[alert_id],
        ), user_id=user_id or "system")
        return ticket

    async def convert_to_knowledge_draft(self, ticket_id: str) -> dict:
        """工单关闭时转知识草稿."""
        ticket = await self.get_ticket(ticket_id)
        if ticket.status != "closed":
            raise ValueError("只有已关闭的工单才能转为知识草稿")
        return {
            "title": f"工单总结: {ticket.title}",
            "article_type": "incident_summary",
            "source": "ticket_closure",
            "source_id": str(ticket.id),
            "context": ticket.context or {},
        }

    async def list_tickets(
        self, status: str | None = None, ticket_type: str | None = None,
        assigned_to: str | None = None, page: int = 1, page_size: int = 20,
    ):
        stmt = select(Ticket)
        count_stmt = select(func.count()).select_from(Ticket)
        if status:
            stmt = stmt.where(Ticket.status == status)
            count_stmt = count_stmt.where(Ticket.status == status)
        if ticket_type:
            stmt = stmt.where(Ticket.ticket_type == ticket_type)
            count_stmt = count_stmt.where(Ticket.ticket_type == ticket_type)
        if assigned_to:
            stmt = stmt.where(Ticket.assigned_to == assigned_to)
            count_stmt = count_stmt.where(Ticket.assigned_to == assigned_to)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0
        result = await self.session.execute(stmt.order_by(Ticket.created_at.desc()).offset((page-1)*page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def get_ticket(self, ticket_id: str) -> Ticket:
        t = await self.ticket_repo.get_by_id(ticket_id)
        if not t:
            raise NotFoundError(f"工单 {ticket_id} 不存在")
        return t

    async def update_ticket(self, ticket_id: str, data: TicketUpdate, user_id: str | None = None) -> Ticket:
        t = await self.get_ticket(ticket_id)
        update_data = data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            if v is not None:
                setattr(t, k, v)
        if data.status == "resolved":
            t.resolved_by = user_id
            t.resolved_at = datetime.now(timezone.utc)
        elif data.status == "closed":
            t.closed_by = user_id
            t.closed_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(t)
        return t

    async def add_comment(self, ticket_id: str, user_id: str, content: str) -> TicketComment:
        comment = await self.comment_repo.create(ticket_id=ticket_id, user_id=user_id, content=content)
        await self.session.flush()
        await self.session.refresh(comment)
        return comment

    async def get_comments(self, ticket_id: str):
        result = await self.session.execute(
            select(TicketComment).where(TicketComment.ticket_id == ticket_id).order_by(TicketComment.created_at)
        )
        return list(result.scalars().all())
