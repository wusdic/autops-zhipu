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

    async def list_collectors(self, asset_type: str | None = None):
        stmt = select(Collector).order_by(Collector.created_at)
        if asset_type:
            stmt = stmt.where(Collector.collector_type == asset_type)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_job(self, collector_id: str = "", asset_id: str = "", name: str = "", **kw) -> CollectionJob:
        if not name:
            name = kw.pop("job_type", "manual") + "_" + (asset_id or "unknown")[:8]
        job = await self.job_repo.create(name=name, collector_id=collector_id, asset_id=asset_id, **kw)
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def list_jobs(self, asset_id: str | None = None, status: str | None = None,
                        page: int = 1, page_size: int = 20):
        stmt = select(CollectionJob)
        if asset_id:
            stmt = stmt.where(CollectionJob.asset_id == asset_id)
        if status:
            stmt = stmt.where(CollectionJob.status == status)
        total_result = await self.session.execute(
            select(func.count()).select_from(CollectionJob)
        )
        total = total_result.scalar() or 0
        result = await self.session.execute(stmt.order_by(CollectionJob.created_at.desc()).offset((page-1)*page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def list_failed_jobs(self, reason: str | None = None) -> list[CollectionJob]:
        """列出失败的采集作业."""
        stmt = select(CollectionJob).where(CollectionJob.status == "failed")
        result = await self.session.execute(stmt.order_by(CollectionJob.created_at.desc()))
        jobs = list(result.scalars().all())
        if reason:
            jobs = [j for j in jobs if reason in (getattr(j, "error_message", "") or "")]
        return jobs

    async def retry_job(self, job_id: str) -> CollectionJob:
        """重置失败作业为pending状态."""
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            return None
        job.status = "pending"
        job.error_message = None
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def cancel_job(self, job_id: str) -> CollectionJob:
        """取消作业."""
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            return None
        if getattr(job, "status", "") in ("completed", "cancelled"):
            return job
        job.status = "cancelled"
        await self.session.flush()
        await self.session.refresh(job)
        return job

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

    async def get_or_create_builtin_collectors(self) -> list[Collector]:
        """确保内置采集器已注册."""
        builtins = [
            {"name": "ping-collector", "collector_type": "ping", "description": "ICMP Ping 可达性检测"},
            {"name": "tcp-port-collector", "collector_type": "tcp_port", "description": "TCP 端口扫描"},
            {"name": "http-collector", "collector_type": "http", "description": "HTTP/HTTPS 服务检测"},
            {"name": "cert-collector", "collector_type": "certificate", "description": "SSL/TLS 证书检测"},
            {"name": "db-collector", "collector_type": "database", "description": "数据库连接检测"},
        ]
        created = []
        for cfg in builtins:
            existing = await self.session.execute(
                select(Collector).where(Collector.name == cfg["name"])
            )
            if not existing.scalar():
                c = await self.collector_repo.create(
                    name=cfg["name"],
                    collector_type=cfg["collector_type"],
                    description=cfg["description"],
                    is_builtin=True,
                )
                await self.session.flush()
                created.append(c)
        if created:
            await self.session.flush()
        all_cols = await self.session.execute(select(Collector).order_by(Collector.created_at))
        return list(all_cols.scalars().all())
