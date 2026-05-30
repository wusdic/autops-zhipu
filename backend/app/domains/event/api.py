"""事件中心 Service + API."""

from __future__ import annotations

import hashlib
import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.repository import BaseRepository
from app.common.response import paginate, success
from app.infra.database import get_db
from app.domains.event.models import Event
from app.domains.event.schemas import EventCreate


class EventService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BaseRepository(session, Event)

    async def create_event(self, **kwargs) -> Event:
        # Generate fingerprint for dedup
        fp_data = f"{kwargs.get('event_type')}:{kwargs.get('asset_id')}:{kwargs.get('source')}:{kwargs.get('title')}"
        fingerprint = hashlib.md5(fp_data.encode()).hexdigest()
        kwargs.setdefault('fingerprint', fingerprint)
        event = await self.repo.create(**kwargs)
        await self.session.flush()
        await self.session.refresh(event)
        return event

    async def list_events(
        self, event_type: str | None = None, asset_id: str | None = None,
        severity: str | None = None, page: int = 1, page_size: int = 20,
    ):
        stmt = select(Event)
        count_stmt = select(func.count()).select_from(Event)
        if event_type:
            stmt = stmt.where(Event.event_type == event_type)
            count_stmt = count_stmt.where(Event.event_type == event_type)
        if asset_id:
            stmt = stmt.where(Event.asset_id == asset_id)
            count_stmt = count_stmt.where(Event.asset_id == asset_id)
        if severity:
            stmt = stmt.where(Event.severity == severity)
            count_stmt = count_stmt.where(Event.severity == severity)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0
        result = await self.session.execute(stmt.order_by(Event.created_at.desc()).offset((page-1)*page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def get_event(self, event_id: str) -> Event:
        event = await self.repo.get_by_id(event_id)
        if not event:
            from app.common.exceptions import NotFoundError
            raise NotFoundError(f"事件 {event_id} 不存在")
        return event


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


@router.post("")
async def create_event(data: EventCreate, svc: EventService = Depends(_get_svc)):
    event = await svc.create_event(**data.model_dump())
    return success(model_to_dict(event))


@router.get("/{event_id}")
async def get_event(event_id: str, svc: EventService = Depends(_get_svc)):
    event = await svc.get_event(event_id)
    return success(model_to_dict(event))
