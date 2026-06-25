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

    @staticmethod
    def _generate_fingerprint(
        event_type: str, source: str, asset_id: str | None, title: str
    ) -> str:
        """生成事件指纹用于去重."""
        key = f"{event_type}|{source}|{asset_id or ''}|{title}"
        return hashlib.md5(key.encode()).hexdigest()

    async def _find_duplicate(self, fingerprint: str, minutes: int = 5):
        """查找指定时间窗口内的重复事件."""
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        q = (
            select(Event)
            .where(Event.fingerprint == fingerprint, Event.created_at >= cutoff)
            .order_by(Event.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def create_event(self, **kwargs) -> Event:
        """创建事件，支持5分钟窗口内自动去重.

        创建成功后发布 ``event.created`` 领域事件（命中去重则发布
        ``event.deduplicated``），驱动后续告警规则匹配链路。outbox 写入复用
        当前 session，与事件落库保持同一事务，保证一致性。
        """
        from app.common.events import DomainEvent, EventEvents, get_event_bus

        fingerprint = self._generate_fingerprint(
            event_type=kwargs.get("event_type", ""),
            source=kwargs.get("source", ""),
            asset_id=kwargs.get("asset_id"),
            title=kwargs.get("title", ""),
        )
        kwargs.setdefault("fingerprint", fingerprint)

        # 查找5分钟内相同指纹的事件
        dup = await self._find_duplicate(fingerprint)
        if dup:
            dup.is_deduplicated = True
            await self.session.flush()
            await self.session.refresh(dup)
            await get_event_bus().publish(
                DomainEvent(
                    event_type=EventEvents.EVENT_DEDUPLICATED,
                    domain="event",
                    payload={
                        "event_id": str(dup.id),
                        "original_event_id": str(dup.id),
                        "event_type": dup.event_type,
                        "asset_id": dup.asset_id,
                    },
                    source="event",
                ),
                session=self.session,
            )
            return dup

        event = await self.repo.create(**kwargs)
        await self.session.flush()
        await self.session.refresh(event)
        await get_event_bus().publish(
            DomainEvent(
                event_type=EventEvents.EVENT_CREATED,
                domain="event",
                payload={
                    "event_id": str(event.id),
                    "event_type": event.event_type,
                    "asset_id": event.asset_id,
                    "severity": event.severity,
                    "source": event.source,
                },
                source="event",
            ),
            session=self.session,
        )
        return event

    async def list_events(
        self,
        event_type: str | None = None,
        asset_id: str | None = None,
        severity: str | None = None,
        page: int = 1,
        page_size: int = 20,
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
        result = await self.session.execute(
            stmt.order_by(Event.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_event(self, event_id: str) -> Event:
        event = await self.repo.get_by_id(event_id)
        if not event:
            from app.common.exceptions import NotFoundError

            raise NotFoundError(f"事件 {event_id} 不存在")
        return event
