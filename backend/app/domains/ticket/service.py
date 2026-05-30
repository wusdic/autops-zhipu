"""工单中心 Service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.common.repository import BaseRepository
from app.domains.ticket.models import Ticket, TicketComment
from app.domains.ticket.schemas import TicketCreate, TicketUpdate


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
