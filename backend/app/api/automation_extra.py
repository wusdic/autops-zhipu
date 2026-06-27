"""自动化补充 API.

自动化统计、审批中心、Dry-run 管理。
全部复用 executions 表，按状态和模式过滤。
"""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import success, paginate
from app.common.crud_service import model_to_dict
from app.infra.database import get_db

router = APIRouter(tags=["自动化补充"])


# ======================================================================
# GET /automation/stats — 自动化统计
# ======================================================================
@router.get("/automation/stats")
async def automation_stats(db: AsyncSession = Depends(get_db)):
    """自动化执行统计."""
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

    pending = (
        await db.execute(
            select(func.count())
            .select_from(Execution)
            .where(Execution.status == "awaiting_approval")
        )
    ).scalar() or 0

    running = (
        await db.execute(
            select(func.count())
            .select_from(Execution)
            .where(Execution.status == "running")
        )
    ).scalar() or 0

    rolling_back = (
        await db.execute(
            select(func.count())
            .select_from(Execution)
            .where(Execution.status == "rolling_back")
        )
    ).scalar() or 0

    return success(
        {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending_approval": pending,
            "running": running,
            "rolling_back": rolling_back,
            "success_rate": round(completed / max(total, 1) * 100, 1),
        }
    )


# ======================================================================
# Approvals — 审批中心
# ======================================================================
approvals_router = APIRouter(prefix="/approvals", tags=["审批中心"])


@approvals_router.get("")
async def list_approvals(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """审批列表(查询 executions).

    默认查询 awaiting_approval 状态（ExecutionStatus 的 canonical 值）；
    传入 status 时按 status 过滤（原实现叠加 AND 导致恒空，已修正）。
    """
    from app.domains.automation.models import Execution

    effective_status = status or "awaiting_approval"
    base = select(Execution).where(Execution.status == effective_status)

    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar() or 0

    rows = (
        (
            await db.execute(
                base.order_by(Execution.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )

    items = [model_to_dict(r) for r in rows]
    return paginate(items, total, page, page_size)


class ApprovalBody(BaseModel):
    comment: str = Field("", max_length=512)


@approvals_router.post("/{approval_id}/approve")
async def approve_execution(
    approval_id: str,
    body: ApprovalBody,
    db: AsyncSession = Depends(get_db),
):
    """审批通过（仅 awaiting_approval 状态可审批）."""
    from app.common.exceptions import ValidationError
    from app.domains.automation.models import Execution

    row = (
        await db.execute(select(Execution).where(Execution.id == approval_id))
    ).scalar_one_or_none()
    if not row:
        return success(None, message="审批记录不存在")
    if row.status != "awaiting_approval":
        raise ValidationError(f"当前状态为 {row.status}，不可审批")

    row.status = "approved"
    row.updated_at = datetime.now(timezone.utc)
    await db.flush()
    # 审批通过后入队，由 ExecutionWorker 领取运行（P1-03）
    from app.common.execution_queue import enqueue

    await enqueue(db, str(row.id))
    await db.refresh(row)
    return success(model_to_dict(row))


@approvals_router.post("/{approval_id}/reject")
async def reject_execution(
    approval_id: str,
    body: ApprovalBody,
    db: AsyncSession = Depends(get_db),
):
    """审批拒绝（仅 awaiting_approval 状态可拒绝）."""
    from app.common.exceptions import ValidationError
    from app.domains.automation.models import Execution

    row = (
        await db.execute(select(Execution).where(Execution.id == approval_id))
    ).scalar_one_or_none()
    if not row:
        return success(None, message="审批记录不存在")
    if row.status != "awaiting_approval":
        raise ValidationError(f"当前状态为 {row.status}，不可拒绝")

    row.status = "rejected"
    row.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(row)
    return success(model_to_dict(row))


# ======================================================================
# Dry-run — 预演管理
# ======================================================================
dryrun_router = APIRouter(prefix="/dry-run", tags=["Dry-run"])


class DryRunCreate(BaseModel):
    execution_id: str = Field(..., description="要预演的执行ID")


@dryrun_router.get("")
async def list_dry_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Dry-run 列表."""
    from app.domains.automation.models import Execution

    base = select(Execution)
    # Check for dry_run mode if column exists
    if hasattr(Execution, "mode"):
        base = base.where(Execution.mode == "dry_run")
    else:
        base = base.where(Execution.status == "dry_running")

    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar() or 0

    rows = (
        (
            await db.execute(
                base.order_by(Execution.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )

    items = [model_to_dict(r) for r in rows]
    return paginate(items, total, page, page_size)


@dryrun_router.post("")
async def create_dry_run(
    data: DryRunCreate,
    db: AsyncSession = Depends(get_db),
):
    """发起 Dry-run(将 execution 标记为 dry_running)."""
    from app.domains.automation.models import Execution

    row = (
        await db.execute(select(Execution).where(Execution.id == data.execution_id))
    ).scalar_one_or_none()
    if not row:
        return success(None, message="执行记录不存在")

    row.status = "dry_running"
    if hasattr(row, "mode"):
        row.mode = "dry_run"
    row.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(row)
    return success(model_to_dict(row))


@dryrun_router.get("/{dryrun_id}")
async def get_dry_run(
    dryrun_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Dry-run 详情."""
    from app.domains.automation.models import Execution

    row = (
        await db.execute(select(Execution).where(Execution.id == dryrun_id))
    ).scalar_one_or_none()
    if not row:
        return success(None, message="Dry-run记录不存在")
    return success(model_to_dict(row))
