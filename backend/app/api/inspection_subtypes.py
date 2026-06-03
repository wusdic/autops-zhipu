"""巡检子类型快捷 API.

提供按 check_type 过滤的巡检结果查询，是 /inspection/results 的语义化快捷方式。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import success, paginate
from app.common.crud_service import model_to_dict
from app.infra.database import get_db

router = APIRouter(tags=["巡检子类型"])

_CHECK_TYPES = {
    "page-checks": "page",
    "config-checks": "config",
    "log-checks": "log",
    "baseline-checks": "baseline",
}


async def _list_by_check_type(
    check_type: str,
    page: int,
    page_size: int,
    status: str | None,
    db: AsyncSession,
):
    """通用按 check_type 查询巡检结果."""
    try:
        from app.domains.inspection.models import InspectionResult

        base = select(InspectionResult)
        # Try check_type filter if column exists
        if hasattr(InspectionResult, 'check_type'):
            base = base.where(InspectionResult.check_type == check_type)
        if status and hasattr(InspectionResult, 'status'):
            base = base.where(InspectionResult.status == status)

        total = (await db.execute(
            select(func.count()).select_from(base.subquery())
        )).scalar() or 0

        rows = (await db.execute(
            base.order_by(InspectionResult.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )).scalars().all()

        items = [model_to_dict(r) for r in rows]
        return paginate(items, total, page, page_size)
    except Exception:
        return paginate([], 0, page, page_size)


@router.get("/page-checks")
async def list_page_checks(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """页面巡检结果."""
    return await _list_by_check_type("page", page, page_size, status, db)


@router.get("/config-checks")
async def list_config_checks(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """配置巡检结果."""
    return await _list_by_check_type("config", page, page_size, status, db)


@router.get("/log-checks")
async def list_log_checks(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """日志巡检结果."""
    return await _list_by_check_type("log", page, page_size, status, db)


@router.get("/baseline-checks")
async def list_baseline_checks(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """基线巡检结果."""
    return await _list_by_check_type("baseline", page, page_size, status, db)
