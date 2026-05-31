"""Edge Collector API 端点."""
from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infra.database import get_db
from app.common.response import success
from app.domains.collector.edge.protocol import HeartbeatPayload, RegisterPayload, ResultPayload
from app.domains.collector.edge.manager import EdgeCollectorManager

router = APIRouter(prefix="/edge", tags=["Edge Collector"])


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
