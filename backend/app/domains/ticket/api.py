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


@router.get("/{ticket_id}/attachments")
async def get_attachments(ticket_id: str, svc: TicketService = Depends(_get_svc)):
    """获取工单附件列表."""
    await svc.get_ticket(ticket_id)
    # Stub: return empty list until attachment model is implemented
    return success([])


from pydantic import BaseModel as _BaseModel


class AttachmentUpload(_BaseModel):
    filename: str
    content_type: str | None = None
    size: int | None = None


@router.post("/{ticket_id}/attachments")
async def upload_attachment(
    ticket_id: str, body: AttachmentUpload, svc: TicketService = Depends(_get_svc),
):
    """上传工单附件（stub）."""
    await svc.get_ticket(ticket_id)
    import uuid as _uuid
    from datetime import datetime as _dt
    return success({
        "id": str(_uuid.uuid4()),
        "ticket_id": ticket_id,
        "filename": body.filename,
        "content_type": body.content_type,
        "size": body.size,
        "uploaded_at": _dt.utcnow().isoformat(),
    })


@router.post("/{ticket_id}/convert-knowledge")
async def convert_ticket_to_knowledge(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """工单关闭后转知识草稿."""
    from app.domains.knowledge.service import KnowledgeService
    from app.domains.knowledge.schemas import KnowledgeCreate
    import json

    ticket_svc = TicketService(db)
    draft = await ticket_svc.convert_to_knowledge_draft(ticket_id)

    knowledge_svc = KnowledgeService(db)
    article = await knowledge_svc.create_article(KnowledgeCreate(
        title=draft["title"],
        article_type=draft.get("article_type", "runbook"),
        content=json.dumps(draft.get("context", {}), ensure_ascii=False),
        source=draft.get("source", "ticket"),
        source_id=draft.get("source_id", ticket_id),
    ))
    return success({"article_id": article.id, "title": article.title, "status": "draft"})
