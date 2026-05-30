"""自动化执行中心 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.response import paginate, success
from app.domains.automation.schemas import (
    ExecutionCreate,
    PlaybookCreate,
    ScriptCreate,
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


@router.post("")
async def create_script(data: ScriptCreate, svc: AutomationService = Depends(_get_svc)):
    s = await svc.create_script(**data.model_dump())
    return success(model_to_dict(s))


@playbook_router.get("")
async def list_playbooks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: AutomationService = Depends(_get_svc),
):
    items, total = await svc.list_playbooks(page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@playbook_router.post("")
async def create_playbook(
    data: PlaybookCreate, svc: AutomationService = Depends(_get_svc)
):
    pb = await svc.create_playbook(**data.model_dump())
    return success(model_to_dict(pb))


@exec_router.get("")
async def list_executions(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: AutomationService = Depends(_get_svc),
):
    items, total = await svc.list_executions(status, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@exec_router.post("")
async def create_execution(
    data: ExecutionCreate, svc: AutomationService = Depends(_get_svc)
):
    exe = await svc.create_execution(data)
    return success(model_to_dict(exe))


@exec_router.get("/{exec_id}")
async def get_execution(exec_id: str, svc: AutomationService = Depends(_get_svc)):
    exe = await svc.get_execution(exec_id)
    return success(model_to_dict(exe))


@exec_router.post("/{exec_id}/approve")
async def approve_execution(exec_id: str, svc: AutomationService = Depends(_get_svc)):
    exe = await svc.approve_execution(exec_id)
    return success(model_to_dict(exe))
