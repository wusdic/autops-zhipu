"""日志中心 Service + API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.repository import BaseRepository
from app.common.response import paginate, success
from app.infra.database import get_db
from app.domains.log.models import ExecutionLog


class LogService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BaseRepository(session, ExecutionLog)

    async def append_log(self, execution_id: str, stream_type: str, content: str, step_id: str | None = None, offset: int = 0) -> ExecutionLog:
        log = await self.repo.create(
            execution_id=execution_id, step_id=step_id,
            stream_type=stream_type, content=content, offset=offset,
        )
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def get_logs(self, execution_id: str, step_id: str | None = None, page: int = 1, page_size: int = 50):
        stmt = select(ExecutionLog).where(ExecutionLog.execution_id == execution_id)
        if step_id:
            stmt = stmt.where(ExecutionLog.step_id == step_id)
        total_result = await self.session.execute(
            select(func.count()).select_from(ExecutionLog).where(ExecutionLog.execution_id == execution_id)
        )
        total = total_result.scalar() or 0
        result = await self.session.execute(stmt.order_by(ExecutionLog.created_at.asc()).offset((page-1)*page_size).limit(page_size))
        return list(result.scalars().all()), total


router = APIRouter(prefix="/logs", tags=["日志中心"])


def _get_svc(db: AsyncSession = Depends(get_db)) -> LogService:
    return LogService(db)


@router.get("/execution/{execution_id}")
async def get_execution_logs(
    execution_id: str, step_id: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    svc: LogService = Depends(_get_svc),
):
    items, total = await svc.get_logs(execution_id, step_id, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@router.post("/execution/{execution_id}")
async def append_log(
    execution_id: str, stream_type: str, content: str,
    step_id: str | None = None, offset: int = 0,
    svc: LogService = Depends(_get_svc),
):
    log = await svc.append_log(execution_id, stream_type, content, step_id, offset)
    return success(model_to_dict(log))


@router.get("/execution/{exec_id}/step/{step_id}")
async def get_step_logs(
    exec_id: str, step_id: str,
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    svc: LogService = Depends(_get_svc),
):
    """获取执行任务指定步骤的日志."""
    items, total = await svc.get_logs(exec_id, step_id, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)
