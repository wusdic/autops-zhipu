"""监控补充 API.

采集结果列表、指标趋势、日志源、采集器健康汇总。
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, text
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

        total = (
            await db.execute(select(func.count()).select_from(base.subquery()))
        ).scalar() or 0

        rows = (
            (
                await db.execute(
                    base.order_by(CollectionResult.created_at.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )

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

        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        rows = (
            (
                await db.execute(
                    select(StateSnapshot)
                    .where(
                        StateSnapshot.asset_id == asset_id,
                        StateSnapshot.created_at >= since,
                    )
                    .order_by(StateSnapshot.created_at.asc())
                    .limit(500)
                )
            )
            .scalars()
            .all()
        )

        points = []
        for r in rows:
            data = model_to_dict(r)
            points.append(
                {
                    "timestamp": data.get("created_at"),
                    "value": data.get("metrics", {}).get(metric_type)
                    if isinstance(data.get("metrics"), dict)
                    else None,
                }
            )

        return success(
            {"asset_id": asset_id, "metric_type": metric_type, "points": points}
        )
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
        total = (
            await db.execute(select(func.count()).select_from(base.subquery()))
        ).scalar() or 0

        rows = (
            (await db.execute(base.offset((page - 1) * page_size).limit(page_size)))
            .scalars()
            .all()
        )

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
    """采集器健康：逐采集器返回真实指标（成功率/平均延迟/最近运行/状态）。

    collectors 表本身不记录运行指标，故按 collection_results(status,duration_ms) 经
    collection_jobs.collector_id 聚合计算：
      成功率 = success / 总执行；平均延迟 = avg(duration_ms)；状态由成功率分档。
    无执行记录的采集器成功率/延迟返回 null（前端显示“-”），状态为 unknown。
    同时返回汇总计数供概览使用。
    """
    from app.domains.collector.models import Collector

    collectors = (await db.execute(select(Collector))).scalars().all()
    items: list[dict] = []
    healthy = degraded = down = 0
    for c in collectors:
        agg = (
            await db.execute(
                text(
                    "SELECT COUNT(*) AS total, "
                    "SUM(CASE WHEN cr.status='success' THEN 1 ELSE 0 END) AS ok, "
                    "AVG(cr.duration_ms) AS avg_ms, MAX(cr.completed_at) AS last_run "
                    "FROM collection_results cr "
                    "JOIN collection_jobs cj ON cr.job_id = cj.id "
                    "WHERE cj.collector_id = :cid"
                ),
                {"cid": c.id},
            )
        ).first()
        total = int(agg[0] or 0)
        ok = int(agg[1] or 0)
        avg_ms = float(agg[2]) if agg[2] is not None else None
        last_run = agg[3]
        rate = (ok / total) if total else None
        if rate is None:
            status = "unknown"
        elif rate >= 0.9:
            status = "healthy"
            healthy += 1
        elif rate >= 0.5:
            status = "degraded"
            degraded += 1
        else:
            status = "down"
            down += 1
        items.append({
            "id": c.id,
            "collector_name": c.name,
            "collector_type": c.collector_type,
            "status": status,
            "success_rate": rate,           # 0~1 小数
            "avg_latency": avg_ms,          # 毫秒
            "last_heartbeat": last_run.isoformat() if hasattr(last_run, "isoformat") else last_run,
            "runs_total": total,
            "runs_ok": ok,
            "version": None,                # 采集器无版本字段
            "task_backlog": None,           # 暂无可靠积压来源
        })

    total_c = len(collectors)
    return success({
        "items": items,
        "total": total_c,
        "healthy": healthy,
        "degraded": degraded,
        "down": down,
        "health_rate": round(healthy / max(total_c, 1) * 100, 1),
    })
