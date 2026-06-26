"""工单中心 API."""

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.response import paginate, success
from app.infra.database import get_db
from app.domains.ticket.schemas import TicketCreate, TicketUpdate, TicketCommentCreate
from app.domains.ticket.service import TicketService


router = APIRouter(prefix="/tickets", tags=["工单中心"])


def _get_svc(db: AsyncSession = Depends(get_db)) -> TicketService:
    return TicketService(db)


@router.get("/stats/overview")
async def ticket_stats(db: AsyncSession = Depends(get_db)):
    """工单统计概览."""
    from sqlalchemy import select, func
    from app.domains.ticket.models import Ticket
    stmt = select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
    result = await db.execute(stmt)
    status_counts = dict(result.all())
    total = sum(status_counts.values())
    return success({
        "total": total,
        "open": status_counts.get("open", 0),
        "in_progress": status_counts.get("in_progress", 0),
        "resolved": status_counts.get("resolved", 0),
        "closed": status_counts.get("closed", 0),
    })


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


def _attachment_dir():
    import os
    import tempfile
    from pathlib import Path

    candidate = os.getenv("AUTOPS_UPLOAD_DIR") or str(Path.cwd() / "data" / "uploads" / "tickets")
    try:
        Path(candidate).mkdir(parents=True, exist_ok=True)
        return Path(candidate)
    except Exception:  # noqa: BLE001
        fb = Path(tempfile.gettempdir()) / "autops_uploads"
        fb.mkdir(parents=True, exist_ok=True)
        return fb


@router.get("/{ticket_id}/attachments")
async def get_attachments(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """获取工单附件列表."""
    from sqlalchemy import text

    rows = (await db.execute(
        text(
            "SELECT id, ticket_id, filename, content_type, size, uploaded_by, created_at "
            "FROM ticket_attachments WHERE ticket_id=:tid ORDER BY created_at DESC"
        ),
        {"tid": ticket_id},
    )).mappings().all()
    items = [dict(r) for r in rows]
    for it in items:
        it["download_url"] = f"/api/v1/tickets/{ticket_id}/attachments/{it['id']}/download"
    return success(items)


@router.post("/{ticket_id}/attachments")
async def upload_attachment(
    ticket_id: str,
    request: Request,
    file: UploadFile = File(...),
    svc: TicketService = Depends(_get_svc),
    db: AsyncSession = Depends(get_db),
):
    """上传工单附件（multipart，真实落盘）."""
    import uuid as _uuid
    from datetime import datetime as _dt, timezone
    from pathlib import Path

    from sqlalchemy import text

    await svc.get_ticket(ticket_id)
    aid = str(_uuid.uuid4())
    safe_name = Path(file.filename or "file").name
    dest = _attachment_dir() / f"{aid}_{safe_name}"
    content = await file.read()
    dest.write_bytes(content)
    uploaded_by = getattr(request.state, "username", "") or getattr(request.state, "user_id", "")
    await db.execute(
        text(
            "INSERT INTO ticket_attachments (id, ticket_id, filename, content_type, size, "
            "storage_path, uploaded_by, created_at) VALUES (:id, :tid, :fn, :ct, :sz, :sp, :by, :ts)"
        ),
        {
            "id": aid, "tid": ticket_id, "fn": safe_name,
            "ct": file.content_type, "sz": len(content), "sp": str(dest),
            "by": uploaded_by, "ts": _dt.now(timezone.utc),
        },
    )
    await db.commit()
    return success({
        "id": aid, "ticket_id": ticket_id, "filename": safe_name,
        "content_type": file.content_type, "size": len(content),
        "download_url": f"/api/v1/tickets/{ticket_id}/attachments/{aid}/download",
    })


@router.get("/{ticket_id}/attachments/{attachment_id}/download")
async def download_attachment(ticket_id: str, attachment_id: str, db: AsyncSession = Depends(get_db)):
    """下载工单附件."""
    from pathlib import Path

    from sqlalchemy import text

    from app.common.exceptions import NotFoundError

    row = (await db.execute(
        text("SELECT * FROM ticket_attachments WHERE id=:id AND ticket_id=:tid"),
        {"id": attachment_id, "tid": ticket_id},
    )).mappings().first()
    if not row or not Path(row["storage_path"]).exists():
        raise NotFoundError("附件不存在")
    return FileResponse(
        row["storage_path"], filename=row["filename"],
        media_type=row.get("content_type") or "application/octet-stream",
    )


@router.delete("/{ticket_id}/attachments/{attachment_id}")
async def delete_attachment(ticket_id: str, attachment_id: str, db: AsyncSession = Depends(get_db)):
    """删除工单附件（含磁盘文件）."""
    from pathlib import Path

    from sqlalchemy import text

    row = (await db.execute(
        text("SELECT storage_path FROM ticket_attachments WHERE id=:id AND ticket_id=:tid"),
        {"id": attachment_id, "tid": ticket_id},
    )).mappings().first()
    if row:
        try:
            p = Path(row["storage_path"])
            if p.exists():
                p.unlink()
        except Exception:  # noqa: BLE001
            pass
        await db.execute(
            text("DELETE FROM ticket_attachments WHERE id=:id"), {"id": attachment_id}
        )
        await db.commit()
    return success(message="附件已删除")


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
