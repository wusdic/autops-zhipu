"""监控补充 API.

采集结果列表、指标趋势、日志源、采集器健康汇总。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import success, paginate
from app.common.crud_service import model_to_dict
from app.infra.database import get_db

router = APIRouter(tags=["监控补充"])


# ======================================================================
# GET /collection-results — 采集结果列表
# ======================================================================
@router.get("/collection-results")
async def list_collection_results(
    asset_id: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """采集结果列表(聚合所有采集任务结果)."""
    try:
        from app.domains.collector.models import CollectionResult

        base = select(CollectionResult)
        if asset_id:
            base = base.where(CollectionResult.asset_id == asset_id)
        if status:
            base = base.where(CollectionResult.status == status)

        total = (await db.execute(
            select(func.count()).select_from(base.subquery())
        )).scalar() or 0

        rows = (await db.execute(
            base.order_by(CollectionResult.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )).scalars().all()

        items = [model_to_dict(r) for r in rows]
        return paginate(items, total, page, page_size)
    except Exception:
        return paginate([], 0, page, page_size)


# ======================================================================
# GET /metrics/trend/{asset_id} — 指标趋势
# ======================================================================
@router.get("/metrics/trend/{asset_id}")
async def metrics_trend(
    asset_id: str,
    metric_type: str = Query("cpu", description="指标类型: cpu/memory/disk/network"),
    hours: int = Query(24, ge=1, le=168, description="时间范围(小时)"),
    db: AsyncSession = Depends(get_db),
):
    """指标趋势(从状态快照中提取)."""
    try:
        from app.domains.state.models import StateSnapshot

        since = datetime.utcnow() - timedelta(hours=hours)
        rows = (await db.execute(
            select(StateSnapshot)
            .where(StateSnapshot.asset_id == asset_id, StateSnapshot.created_at >= since)
            .order_by(StateSnapshot.created_at.asc())
            .limit(500)
        )).scalars().all()

        points = []
        for r in rows:
            data = model_to_dict(r)
            points.append({
                "timestamp": data.get("created_at"),
                "value": data.get("metrics", {}).get(metric_type) if isinstance(data.get("metrics"), dict) else None,
            })

        return success({"asset_id": asset_id, "metric_type": metric_type, "points": points})
    except Exception:
        return success({"asset_id": asset_id, "metric_type": metric_type, "points": []})


# ======================================================================
# GET /log-sources — 日志源列表
# ======================================================================
@router.get("/log-sources")
async def list_log_sources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """日志源列表(从配置中查询日志相关配置)."""
    try:
        from app.domains.config.models import ConfigDefinition

        base = select(ConfigDefinition).where(
            ConfigDefinition.config_type == "log_source"
        )
        total = (await db.execute(
            select(func.count()).select_from(base.subquery())
        )).scalar() or 0

        rows = (await db.execute(
            base.offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()

        items = [model_to_dict(r) for r in rows]
        return paginate(items, total, page, page_size)
    except Exception:
        # If config_type column doesn't exist, return empty
        return paginate([], 0, page, page_size)


# ======================================================================
# GET /collectors/health — 采集器健康汇总
# ======================================================================
@router.get("/collectors/health")
async def collectors_health_summary(db: AsyncSession = Depends(get_db)):
    """采集器健康汇总."""
    try:
        from app.domains.collector.models import Collector

        total = (await db.execute(
            select(func.count()).select_from(Collector)
        )).scalar() or 0

        online = (await db.execute(
            select(func.count()).select_from(Collector)
            .where(Collector.status == "online")
        )).scalar() or 0

        offline = (await db.execute(
            select(func.count()).select_from(Collector)
            .where(Collector.status == "offline")
        )).scalar() or 0

        error = (await db.execute(
            select(func.count()).select_from(Collector)
            .where(Collector.status == "error")
        )).scalar() or 0

        return success({
            "total": total,
            "online": online,
            "offline": offline,
            "error": error,
            "health_rate": round(online / max(total, 1) * 100, 1),
        })
    except Exception:
        return success({"total": 0, "online": 0, "offline": 0, "error": 0, "health_rate": 0})
