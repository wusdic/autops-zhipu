"""工单中心 Service + API."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.exceptions import NotFoundError
from app.common.repository import BaseRepository
from app.common.response import paginate, success
from app.infra.database import get_db
from app.domains.ticket.models import Ticket, TicketComment
from app.domains.ticket.schemas import TicketCreate, TicketUpdate, TicketCommentCreate


class TicketService:
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


router = APIRouter(prefix="/tickets", tags=["工单中心"])


def _get_svc(db: AsyncSession = Depends(get_db)) -> TicketService:
    return TicketService(db)


@router.get("")
async def list_tickets(
    status: str | None = None, ticket_type: str | None = None,
    assigned_to: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    svc: TicketService = Depends(_get_svc),
):
    items, total = await svc.list_tickets(status, ticket_type, assigned_to, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@router.post("")
async def create_ticket(data: TicketCreate, svc: TicketService = Depends(_get_svc)):
    t = await svc.create_ticket(data)
    return success(model_to_dict(t))


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str, svc: TicketService = Depends(_get_svc)):
    t = await svc.get_ticket(ticket_id)
    return success(model_to_dict(t))


@router.put("/{ticket_id}")
async def update_ticket(ticket_id: str, data: TicketUpdate, svc: TicketService = Depends(_get_svc)):
    t = await svc.update_ticket(ticket_id, data)
    return success(model_to_dict(t))


@router.post("/{ticket_id}/comments")
async def add_comment(ticket_id: str, data: TicketCommentCreate, svc: TicketService = Depends(_get_svc)):
    comment = await svc.add_comment(ticket_id, "system", data.content)
    return success(model_to_dict(comment))


@router.get("/{ticket_id}/comments")
async def get_comments(ticket_id: str, svc: TicketService = Depends(_get_svc)):
    comments = await svc.get_comments(ticket_id)
    return success([model_to_dict(c) for c in comments])
