"""采集器 Service."""

from __future__ import annotations
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import DuplicateError
from app.common.repository import BaseRepository
from app.domains.collector.models import Collector, CollectionJob, CollectionResult


class CollectorService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.collector_repo = BaseRepository(session, Collector)
        self.job_repo = BaseRepository(session, CollectionJob)
        self.result_repo = BaseRepository(session, CollectionResult)

    async def register_collector(self, name: str, collector_type: str, **kw) -> Collector:
        existing = await self.session.execute(
            select(Collector).where(Collector.name == name)
        )
        if existing.scalar():
            raise DuplicateError(f"采集器 '{name}' 已注册")
        collector = await self.collector_repo.create(name=name, collector_type=collector_type, **kw)
        await self.session.flush()
        await self.session.refresh(collector)
        return collector

    async def list_collectors(self):
        result = await self.session.execute(select(Collector).order_by(Collector.created_at))
        return list(result.scalars().all())

    async def create_job(self, name: str, collector_id: str, asset_id: str, **kw) -> CollectionJob:
        job = await self.job_repo.create(name=name, collector_id=collector_id, asset_id=asset_id, **kw)
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def list_jobs(self, asset_id: str | None = None, page: int = 1, page_size: int = 20):
        stmt = select(CollectionJob)
        if asset_id:
            stmt = stmt.where(CollectionJob.asset_id == asset_id)
        total_result = await self.session.execute(select(func.count()).select_from(CollectionJob))
        total = total_result.scalar() or 0
        result = await self.session.execute(stmt.order_by(CollectionJob.created_at.desc()).offset((page-1)*page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def record_result(self, job_id: str, asset_id: str, status: str, **kw):
        now = datetime.now(timezone.utc)
        kw.setdefault('started_at', now)
        kw.setdefault('completed_at', now)
        result = await self.result_repo.create(job_id=job_id, asset_id=asset_id, status=status, **kw)
        await self.session.flush()
        await self.session.refresh(result)
        return result

    async def get_job_results(self, job_id: str, page: int = 1, page_size: int = 20):
        stmt = select(CollectionResult).where(CollectionResult.job_id == job_id).order_by(CollectionResult.created_at.desc())
        total_result = await self.session.execute(
            select(func.count()).select_from(CollectionResult).where(CollectionResult.job_id == job_id)
        )
        total = total_result.scalar() or 0
        result = await self.session.execute(stmt.offset((page-1)*page_size).limit(page_size))
        return list(result.scalars().all()), total
