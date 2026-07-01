"""事件中心 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.response import paginate, success
from app.domains.event.schemas import EventCreate
from app.domains.event.service import EventService
from app.infra.database import get_db

router = APIRouter(prefix="/events", tags=["事件中心"])


def _get_svc(db: AsyncSession = Depends(get_db)) -> EventService:
    return EventService(db)


@router.get("")
async def list_events(
    event_type: str | None = None, asset_id: str | None = None,
    severity: str | None = None, page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: EventService = Depends(_get_svc),
):
    items, total = await svc.list_events(event_type, asset_id, severity, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@router.get("/stats/by-type")
async def event_counts_by_type(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """按事件类型统计近 N 天事件数（供“规则缺口分析”等使用，真实聚合）."""
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import text

    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (await db.execute(
        text(
            "SELECT event_type, COUNT(*) AS c FROM events "
            "WHERE created_at >= :since GROUP BY event_type"
        ),
        {"since": since},
    )).all()
    return success({r[0]: int(r[1]) for r in rows})


@router.post("")
async def create_event(data: EventCreate, svc: EventService = Depends(_get_svc)):
    event = await svc.create_event(**data.model_dump())
    return success(model_to_dict(event))


@router.get("/{event_id}")
async def get_event(event_id: str, svc: EventService = Depends(_get_svc)):
    event = await svc.get_event(event_id)
    return success(model_to_dict(event))
