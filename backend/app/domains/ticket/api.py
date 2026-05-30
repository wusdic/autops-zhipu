"""工单中心 API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.response import paginate, success
from app.infra.database import get_db
from app.domains.ticket.schemas import TicketCreate, TicketUpdate, TicketCommentCreate
from app.domains.ticket.service import TicketService


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
