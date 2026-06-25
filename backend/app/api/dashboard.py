"""Dashboard 聚合统计 API.

从各域表聚合数据，提供首页指挥台所需的统计信息。
全部只读，不写不修改任何表。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import success
from app.infra.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["首页指挥台"])


# ======================================================================
# GET /dashboard/stats — 总览统计
# ======================================================================
@router.get("/stats")
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    """首页总览统计."""
    from app.domains.alert.models import Alert
    from app.domains.anomaly.models import Anomaly
    from app.domains.asset.models import Asset
    from app.domains.automation.models import Execution
    from app.domains.ticket.models import Ticket

    # 资产统计
    asset_total = (
        await db.execute(
            select(func.count()).select_from(Asset).where(Asset.is_deleted == False)
        )
    ).scalar() or 0

    # 告警统计
    alert_open = (
        await db.execute(
            select(func.count()).select_from(Alert).where(Alert.status == "open")
        )
    ).scalar() or 0

    # 异常统计
    anomaly_open = (
        await db.execute(
            select(func.count())
            .select_from(Anomaly)
            .where(Anomaly.status.in_(["new", "confirmed", "analyzing"]))
        )
    ).scalar() or 0

    # 执行统计
    exec_pending = (
        await db.execute(
            select(func.count())
            .select_from(Execution)
            .where(Execution.status == "pending_approval")
        )
    ).scalar() or 0

    # 工单统计
    ticket_open = (
        await db.execute(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.status.in_(["open", "in_progress"]))
        )
    ).scalar() or 0

    return success(
        {
            "asset_total": asset_total,
            "alert_open": alert_open,
            "anomaly_open": anomaly_open,
            "execution_pending_approval": exec_pending,
            "ticket_open": ticket_open,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


# ======================================================================
# GET /dashboard/asset-discovery — 资产发现概况
# ======================================================================
@router.get("/asset-discovery")
async def asset_discovery_summary(db: AsyncSession = Depends(get_db)):
    """资产发现概况."""
    from app.domains.asset.discovery_models import DiscoveryResult, DiscoveryTask
    from app.domains.asset.models import Asset

    asset_total = (
        await db.execute(
            select(func.count()).select_from(Asset).where(Asset.is_deleted == False)
        )
    ).scalar() or 0

    today = datetime.now(timezone.utc).date()
    today_start = datetime(today.year, today.month, today.day)

    new_today = (
        await db.execute(
            select(func.count())
            .select_from(Asset)
            .where(Asset.is_deleted == False, Asset.created_at >= today_start)
        )
    ).scalar() or 0

    discovery_tasks = (
        await db.execute(select(func.count()).select_from(DiscoveryTask))
    ).scalar() or 0

    pending_results = (
        await db.execute(
            select(func.count())
            .select_from(DiscoveryResult)
            .where(DiscoveryResult.status == "pending")
        )
    ).scalar() or 0

    # 按类型分布
    type_dist_rows = (
        await db.execute(
            select(Asset.asset_type, func.count().label("count"))
            .where(Asset.is_deleted == False)
            .group_by(Asset.asset_type)
        )
    ).all()
    type_distribution = {r[0]: r[1] for r in type_dist_rows}

    return success(
        {
            "asset_total": asset_total,
            "new_today": new_today,
            "discovery_tasks_total": discovery_tasks,
            "pending_confirmation": pending_results,
            "type_distribution": type_distribution,
        }
    )


# ======================================================================
# GET /dashboard/inspection — 巡检概况
# ======================================================================
@router.get("/inspection")
async def inspection_summary(db: AsyncSession = Depends(get_db)):
    """巡检概况."""
    try:
        from app.domains.inspection.models import InspectionResult, InspectionTask

        task_total = (
            await db.execute(select(func.count()).select_from(InspectionTask))
        ).scalar() or 0
        task_completed = (
            await db.execute(
                select(func.count())
                .select_from(InspectionTask)
                .where(InspectionTask.status == "completed")
            )
        ).scalar() or 0
        task_failed = (
            await db.execute(
                select(func.count())
                .select_from(InspectionTask)
                .where(InspectionTask.status == "failed")
            )
        ).scalar() or 0

        # 异常项统计
        abnormal_items = (
            (
                await db.execute(
                    select(func.count())
                    .select_from(InspectionResult)
                    .where(InspectionResult.status == "abnormal")
                )
            ).scalar()
            if hasattr(InspectionResult, "status")
            else 0
        )

        success_rate = round(task_completed / max(task_total, 1) * 100, 1)
    except Exception:
        task_total, task_completed, task_failed, abnormal_items, success_rate = (
            0,
            0,
            0,
            0,
            0,
        )

    return success(
        {
            "task_total": task_total,
            "task_completed": task_completed,
            "task_failed": task_failed,
            "abnormal_items": abnormal_items,
            "success_rate": success_rate,
        }
    )


# ======================================================================
# GET /dashboard/anomaly — 异常概况
# ======================================================================
@router.get("/anomaly")
async def anomaly_summary(db: AsyncSession = Depends(get_db)):
    """异常概况."""
    from app.domains.anomaly.models import Anomaly

    total = (await db.execute(select(func.count()).select_from(Anomaly))).scalar() or 0

    # 按严重级别统计
    severity_rows = (
        await db.execute(
            select(Anomaly.severity, func.count().label("count")).group_by(
                Anomaly.severity
            )
        )
    ).all()
    severity_distribution = {r[0]: r[1] for r in severity_rows}

    # 按状态统计
    status_rows = (
        await db.execute(
            select(Anomaly.status, func.count().label("count")).group_by(Anomaly.status)
        )
    ).all()
    status_distribution = {r[0]: r[1] for r in status_rows}

    # 今日新增
    today = datetime.now(timezone.utc).date()
    today_start = datetime(today.year, today.month, today.day)
    new_today = (
        await db.execute(
            select(func.count())
            .select_from(Anomaly)
            .where(Anomaly.created_at >= today_start)
        )
    ).scalar() or 0

    return success(
        {
            "total": total,
            "new_today": new_today,
            "severity_distribution": severity_distribution,
            "status_distribution": status_distribution,
        }
    )


# ======================================================================
# GET /dashboard/automation — 自动化概况
# ======================================================================
@router.get("/automation")
async def automation_summary(db: AsyncSession = Depends(get_db)):
    """自动化概况."""
    from app.domains.automation.models import Execution

    total = (
        await db.execute(select(func.count()).select_from(Execution))
    ).scalar() or 0

    completed = (
        await db.execute(
            select(func.count())
            .select_from(Execution)
            .where(Execution.status == "completed")
        )
    ).scalar() or 0

    failed = (
        await db.execute(
            select(func.count())
            .select_from(Execution)
            .where(Execution.status == "failed")
        )
    ).scalar() or 0

    pending_approval = (
        await db.execute(
            select(func.count())
            .select_from(Execution)
            .where(Execution.status == "pending_approval")
        )
    ).scalar() or 0

    running = (
        await db.execute(
            select(func.count())
            .select_from(Execution)
            .where(Execution.status == "running")
        )
    ).scalar() or 0

    success_rate = round(completed / max(total, 1) * 100, 1)

    return success(
        {
            "total_executions": total,
            "completed": completed,
            "failed": failed,
            "pending_approval": pending_approval,
            "running": running,
            "success_rate": success_rate,
        }
    )


# ======================================================================
# GET /dashboard/report — 报告概况
# ======================================================================
@router.get("/report")
async def report_summary(db: AsyncSession = Depends(get_db)):
    """报告概况."""
    try:
        from app.domains.report.models import ReportTask

        total = (
            await db.execute(select(func.count()).select_from(ReportTask))
        ).scalar() or 0
        completed = (
            await db.execute(
                select(func.count())
                .select_from(ReportTask)
                .where(ReportTask.status == "completed")
            )
        ).scalar() or 0
        failed = (
            await db.execute(
                select(func.count())
                .select_from(ReportTask)
                .where(ReportTask.status == "failed")
            )
        ).scalar() or 0
    except Exception:
        total, completed, failed = 0, 0, 0

    return success(
        {
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
        }
    )


# ======================================================================
# GET /dashboard/platform-health — 平台健康概况
# ======================================================================
@router.get("/platform-health")
async def platform_health_summary(db: AsyncSession = Depends(get_db)):
    """平台各组件健康状态."""
    checks = {}

    # DB check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy", "message": "连接正常"}
    except Exception:
        logger.exception("platform-health: 数据库检查失败")
        checks["database"] = {"status": "unhealthy", "message": "连接异常"}

    # Redis check
    try:
        from app.infra.redis_client import get_redis

        redis = await get_redis()
        if redis:
            await redis.ping()
            checks["redis"] = {"status": "healthy", "message": "连接正常"}
        else:
            checks["redis"] = {"status": "degraded", "message": "未配置"}
    except Exception:
        logger.exception("platform-health: Redis 检查失败")
        checks["redis"] = {"status": "unhealthy", "message": "连接异常"}

    # API check (self)
    checks["api_server"] = {"status": "healthy", "message": "运行中"}

    # 综合状态
    all_healthy = all(c["status"] == "healthy" for c in checks.values())
    overall = "healthy" if all_healthy else "degraded"

    return success(
        {
            "overall": overall,
            "components": checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


# ======================================================================
# GET /dashboard/my-pending — 我的待办
# ======================================================================
@router.get("/my-pending")
async def my_pending_items(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """聚合当前用户的待办事项.

    user_id 从认证上下文 request.state.user_id 获取（由 AuthMiddleware 注入），
    不再接受客户端传入的 user_id 查询参数，避免越权查看他人待办（IDOR）。
    """
    from app.domains.anomaly.models import Anomaly
    from app.domains.automation.models import Execution
    from app.domains.ticket.models import Ticket

    user_id = getattr(request.state, "user_id", "")
    if not user_id:
        return success(
            {
                "pending_approvals": 0,
                "pending_anomalies": 0,
                "pending_tickets": 0,
                "total": 0,
            }
        )

    # 待审批执行
    pending_approvals = (
        await db.execute(
            select(func.count())
            .select_from(Execution)
            .where(Execution.status == "pending_approval")
        )
    ).scalar() or 0

    # 待处理异常(分派给我)
    pending_anomalies = (
        await db.execute(
            select(func.count())
            .select_from(Anomaly)
            .where(
                Anomaly.assigned_to == user_id, Anomaly.status.in_(["new", "confirmed"])
            )
        )
    ).scalar() or 0

    # 待处理工单
    pending_tickets = (
        await db.execute(
            select(func.count())
            .select_from(Ticket)
            .where(
                Ticket.assigned_to == user_id,
                Ticket.status.in_(["open", "in_progress"]),
            )
        )
    ).scalar() or 0

    return success(
        {
            "pending_approvals": pending_approvals,
            "pending_anomalies": pending_anomalies,
            "pending_tickets": pending_tickets,
            "total": pending_approvals + pending_anomalies + pending_tickets,
        }
    )
