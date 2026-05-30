"""事件中心 Service."""

from __future__ import annotations

import hashlib

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.repository import BaseRepository
from app.domains.event.models import Event


class EventService:
    """事件业务逻辑."""

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
