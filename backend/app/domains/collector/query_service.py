"""Collector domain query service — lightweight read-only queries + job creation for cross-domain use."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.collector.models import CollectionJob, Collector


async def get_collection_jobs_by_asset(
    asset_id: str,
    session: AsyncSession,
    limit: int = 10,
) -> list[dict]:
    """获取资产的采集任务列表，返回 dict 列表（不暴露 ORM 对象）."""
    stmt = (
        select(CollectionJob)
        .where(CollectionJob.asset_id == asset_id)
        .order_by(CollectionJob.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    jobs = result.scalars().all()
    return [
        {
            "id": j.id,
            "name": j.name,
            "collector_id": j.collector_id,
            "asset_id": j.asset_id,
            "config_version_id": j.config_version_id,
            "credential_id": j.credential_id,
            "schedule": j.schedule,
            "status": j.status,
            "timeout": j.timeout,
            "last_run_at": j.last_run_at.isoformat() if j.last_run_at else None,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        }
        for j in jobs
    ]


async def create_collection_job_for_asset(
    asset_id: str,
    session: AsyncSession,
    collector_id: str | None = None,
) -> dict:
    """为指定资产创建一个手动采集任务，发布 collector.job_created 事件.

    Returns:
        dict with ``job_id`` and ``status``.
    """
    from app.common.events import DomainEvent, get_event_bus, CollectorEvents

    # Resolve collector_id: use provided value, or fall back to any registered collector
    if not collector_id:
        stmt = select(Collector).limit(1)
        result = await session.execute(stmt)
        collector = result.scalar_one_or_none()
        collector_id = collector.id if collector else "manual"

    job = CollectionJob(
        name=f"manual_{asset_id[:8]}",
        collector_id=collector_id,
        asset_id=asset_id,
        schedule="manual",
        status="active",
    )
    session.add(job)
    await session.flush()
    await session.refresh(job)

    # Publish event via the event bus
    bus = get_event_bus()
    event = DomainEvent(
        event_type=CollectorEvents.JOB_CREATED,
        domain="collector",
        payload={
            "job_id": str(job.id),
            "asset_id": asset_id,
            "collector_id": collector_id,
            "schedule": "manual",
        },
        source="asset.trigger_collection",
    )
    await bus.publish(event)

    return {
        "job_id": str(job.id),
        "status": job.status,
    }
