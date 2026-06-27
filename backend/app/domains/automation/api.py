"""自动化执行中心 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth_dependency import require_admin
from app.common.crud_service import model_to_dict
from app.common.response import paginate, success
from app.domains.automation.schemas import (
    ExecutionCreate,
    PlaybookCreate,
    PlaybookUpdate,
    ScriptCreate,
    ScriptUpdate,
)
from app.domains.automation.service import AutomationService
from app.infra.database import get_db

router = APIRouter(prefix="/scripts", tags=["脚本库"])
playbook_router = APIRouter(prefix="/playbooks", tags=["Playbook"])
exec_router = APIRouter(prefix="/executions", tags=["执行任务"])


def _get_svc(db: AsyncSession = Depends(get_db)) -> AutomationService:
    return AutomationService(db)


@router.get("")
async def list_scripts(
    script_type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: AutomationService = Depends(_get_svc),
):
    items, total = await svc.list_scripts(script_type, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@router.post("", dependencies=[Depends(require_admin)])
async def create_script(data: ScriptCreate, svc: AutomationService = Depends(_get_svc)):
    s = await svc.create_script(**data.model_dump())
    return success(model_to_dict(s))


@router.put("/{script_id}")
async def update_script(
    script_id: str, data: ScriptUpdate, svc: AutomationService = Depends(_get_svc)
):
    s = await svc.update_script(script_id, **data.model_dump(exclude_unset=True))
    return success(model_to_dict(s))


@router.delete("/{script_id}", dependencies=[Depends(require_admin)])
async def delete_script(script_id: str, svc: AutomationService = Depends(_get_svc)):
    await svc.delete_script(script_id)
    return success(message="脚本已删除")


@playbook_router.get("")
async def list_playbooks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: AutomationService = Depends(_get_svc),
):
    items, total = await svc.list_playbooks(page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@playbook_router.post("", dependencies=[Depends(require_admin)])
async def create_playbook(
    data: PlaybookCreate, svc: AutomationService = Depends(_get_svc)
):
    pb = await svc.create_playbook(**data.model_dump())
    return success(model_to_dict(pb))


@playbook_router.get("/{playbook_id}")
async def get_playbook(playbook_id: str, svc: AutomationService = Depends(_get_svc)):
    pb = await svc.get_playbook(playbook_id)
    return success(model_to_dict(pb))


@playbook_router.put("/{playbook_id}")
async def update_playbook(
    playbook_id: str, data: PlaybookUpdate, svc: AutomationService = Depends(_get_svc)
):
    pb = await svc.update_playbook(playbook_id, **data.model_dump(exclude_unset=True))
    return success(model_to_dict(pb))


@playbook_router.delete("/{playbook_id}", dependencies=[Depends(require_admin)])
async def delete_playbook(playbook_id: str, svc: AutomationService = Depends(_get_svc)):
    await svc.delete_playbook(playbook_id)
    return success(message="Playbook 已删除")


@exec_router.get("")
async def list_executions(
    status: str | None = None,
    trigger_source: str | None = None,
    risk_level: str | None = None,
    search: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    stats: bool = False,
    trend: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: AutomationService = Depends(_get_svc),
):
    """执行列表（支持筛选）+ 统计卡片(stats) + 趋势(trend=7d)。"""
    if stats:
        return success(await svc.execution_stats())
    if trend:
        days = 7
        digits = "".join(ch for ch in trend if ch.isdigit())
        if digits:
            days = max(1, min(int(digits), 90))
        return success({"trend": await svc.execution_trend(days)})
    items, total = await svc.list_executions(
        status=status, page=page, page_size=page_size,
        trigger_source=trigger_source, risk_level=risk_level,
        search=search, start_time=start_time, end_time=end_time,
    )
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@exec_router.post("")
async def create_execution(
    data: ExecutionCreate, svc: AutomationService = Depends(_get_svc)
):
    """创建执行任务并入队（非待审批者由 ExecutionWorker 领取运行）."""
    from app.common.execution_queue import enqueue
    from app.domains.automation.models import ExecutionStatus

    exe = await svc.create_execution(data)
    if exe.status in (ExecutionStatus.PENDING, ExecutionStatus.APPROVED):
        await enqueue(svc.session, str(exe.id))
    return success(model_to_dict(exe))


@exec_router.get("/{exec_id}")
async def get_execution(exec_id: str, svc: AutomationService = Depends(_get_svc)):
    exe = await svc.get_execution(exec_id)
    return success(model_to_dict(exe))


@exec_router.post("/{exec_id}/approve", dependencies=[Depends(require_admin)])
async def approve_execution(exec_id: str, svc: AutomationService = Depends(_get_svc)):
    """审批通过并入队执行（P1-03：审批后必须续跑）."""
    from app.common.execution_queue import enqueue

    exe = await svc.approve_execution(exec_id)
    await enqueue(svc.session, str(exe.id))
    return success(model_to_dict(exe))


@exec_router.post("/{exec_id}/retry")
async def retry_execution(exec_id: str, svc: AutomationService = Depends(_get_svc)):
    """以相同参数重新发起执行（克隆并入队）."""
    from app.common.execution_queue import enqueue
    from app.domains.automation.models import ExecutionStatus

    exe = await svc.retry_execution(exec_id)
    if exe.status in (ExecutionStatus.PENDING, ExecutionStatus.APPROVED):
        await enqueue(svc.session, str(exe.id))
    return success(model_to_dict(exe))


@exec_router.post("/{exec_id}/cancel", dependencies=[Depends(require_admin)])
async def cancel_execution(exec_id: str, svc: AutomationService = Depends(_get_svc)):
    exe = await svc.cancel_execution(exec_id)
    return success(model_to_dict(exe))


@exec_router.post("/{exec_id}/rollback", dependencies=[Depends(require_admin)])
async def rollback_execution(exec_id: str, svc: AutomationService = Depends(_get_svc)):
    exe = await svc.rollback_execution(exec_id)
    return success(model_to_dict(exe))


@exec_router.get("/{exec_id}/verification")
async def get_execution_verification(
    exec_id: str, svc: AutomationService = Depends(_get_svc)
):
    """获取执行任务验证信息."""
    exe = await svc.get_execution(exec_id)
    return success(
        {
            "execution_id": exe.id,
            "status": exe.status,
            "risk_level": exe.risk_level,
            "is_dry_run": exe.is_dry_run,
            "verified": exe.status in ("approved", "completed", "running"),
        }
    )
