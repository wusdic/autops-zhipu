"""Edge Collector API 端点."""
from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infra.database import get_db
from app.common.crud_service import model_to_dict
from app.common.response import paginate, success
from app.domains.collector.edge.protocol import HeartbeatPayload, RegisterPayload, ResultPayload
from app.domains.collector.edge.manager import EdgeCollectorManager

router = APIRouter(prefix="/edge", tags=["Edge Collector"])


@router.get("")
async def list_edge_collectors(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """列出 Edge 采集器."""
    from app.domains.collector.models import Collector

    base = select(Collector).where(Collector.collector_type == "edge")
    if status:
        base = base.where(Collector.status == status)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
    rows = (
        await db.execute(
            base.order_by(Collector.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size)
        )
    ).scalars().all()
    return paginate([model_to_dict(r) for r in rows], total, page, page_size)


@router.post("/register")
async def register_collector(payload: RegisterPayload, db: AsyncSession = Depends(get_db)):
    """远程采集器注册."""
    mgr = EdgeCollectorManager(db)
    result = await mgr.register(payload)
    await db.commit()
    return success(result)


@router.post("/heartbeat")
async def collector_heartbeat(payload: HeartbeatPayload, db: AsyncSession = Depends(get_db)):
    """采集器心跳上报."""
    mgr = EdgeCollectorManager(db)
    result = await mgr.heartbeat(payload)
    return success(result)


@router.get("/{collector_id}/tasks")
async def get_pending_tasks(collector_id: str, db: AsyncSession = Depends(get_db)):
    """获取待执行任务."""
    mgr = EdgeCollectorManager(db)
    tasks = await mgr.get_pending_tasks(collector_id)
    return success(tasks)


@router.post("/{collector_id}/results")
async def submit_result(collector_id: str, payload: ResultPayload, db: AsyncSession = Depends(get_db)):
    """上报任务结果."""
    mgr = EdgeCollectorManager(db)
    result = await mgr.submit_result(payload)
    await db.commit()
    return success(result)


@router.get("/{collector_id}/status")
async def get_collector_status(collector_id: str, db: AsyncSession = Depends(get_db)):
    """获取采集器状态."""
    mgr = EdgeCollectorManager(db)
    status = await mgr.get_collector_status(collector_id)
    return success(status)


@router.get("/{collector_id}")
async def get_edge_collector(collector_id: str, db: AsyncSession = Depends(get_db)):
    """Edge 采集器详情."""
    from app.domains.collector.models import Collector

    row = (await db.execute(select(Collector).where(Collector.id == collector_id))).scalar_one_or_none()
    if not row:
        from app.common.exceptions import NotFoundError

        raise NotFoundError("采集器不存在")
    return success(model_to_dict(row))


@router.delete("/{collector_id}")
async def delete_edge_collector(collector_id: str, db: AsyncSession = Depends(get_db)):
    """删除/注销 Edge 采集器."""
    from app.domains.collector.models import Collector

    row = (await db.execute(select(Collector).where(Collector.id == collector_id))).scalar_one_or_none()
    if not row:
        from app.common.exceptions import NotFoundError

        raise NotFoundError("采集器不存在")
    await db.delete(row)
    await db.flush()
    return success(message="采集器已删除")
