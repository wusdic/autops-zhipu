"""采集器 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import paginate, success
from app.common.crud_service import model_to_dict
from app.infra.database import get_db
from app.domains.collector.service import CollectorService
from app.domains.collector.schemas import CollectorCreate, CollectionJobCreate

router = APIRouter(prefix="/collectors", tags=["采集器"])
job_router = APIRouter(prefix="/collection-jobs", tags=["采集任务"])


def _get_svc(db: AsyncSession = Depends(get_db)) -> CollectorService:
    return CollectorService(db)


@router.get("")
async def list_collectors(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    svc: CollectorService = Depends(_get_svc),
):
    items = await svc.list_collectors()
    return paginate([model_to_dict(i) for i in items], len(items), page, page_size)


@router.post("")
async def register_collector(data: CollectorCreate, svc: CollectorService = Depends(_get_svc)):
    c = await svc.register_collector(**data.model_dump())
    return success(model_to_dict(c))


@job_router.get("")
async def list_jobs(
    asset_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: CollectorService = Depends(_get_svc),
):
    items, total = await svc.list_jobs(asset_id=asset_id, page=page, page_size=page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@job_router.post("")
async def create_job(data: CollectionJobCreate, svc: CollectorService = Depends(_get_svc)):
    job = await svc.create_job(**data.model_dump())
    return success(model_to_dict(job))


@job_router.post("/trigger")
async def trigger_collection(db: AsyncSession = Depends(get_db)):
    """手动触发一次全量采集周期.

    不在 API 进程内直接跑（API 进程无 CAP_NET_RAW、scheduler 未启动，ping 会全失败）。
    改为发 FULL_SCAN_REQUESTED 事件，由 Worker 进程消费执行（与 P1-07 发现一致）。
    """
    from app.common.events import CollectorEvents, DomainEvent, get_event_bus

    await get_event_bus().publish(
        DomainEvent(
            domain="collector",
            event_type=CollectorEvents.FULL_SCAN_REQUESTED,
            payload={},
            source="collector_api",
        ),
        session=db,
    )
    return success({"message": "Collection cycle requested (via worker)"})


@job_router.get("/{job_id}/results")
async def get_job_results(
    job_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: CollectorService = Depends(_get_svc),
):
    items, total = await svc.get_job_results(job_id, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)
