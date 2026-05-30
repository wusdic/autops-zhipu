"""自动化执行中心 Service + API."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.exceptions import NotFoundError, DuplicateError
from app.common.repository import BaseRepository
from app.common.response import paginate, success
from app.infra.database import get_db
from app.domains.automation.models import Script, Playbook, Execution, ExecutionStep
from app.domains.automation.schemas import (
    ScriptCreate, PlaybookCreate, ExecutionCreate, ExecutionApprove,
)


# 高危命令黑名单
BLOCKED_COMMANDS = ["rm -rf /", "mkfs.", "dd if=", ":(){ :|:& };:", "format c:"]


class AutomationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.script_repo = BaseRepository(session, Script)
        self.playbook_repo = BaseRepository(session, Playbook)
        self.exec_repo = BaseRepository(session, Execution)
        self.step_repo = BaseRepository(session, ExecutionStep)

    def _check_blocked(self, content: str) -> bool:
        lower = content.lower()
        return any(cmd in lower for cmd in BLOCKED_COMMANDS)

    async def create_script(self, **kwargs) -> Script:
        name = kwargs.get('name')
        existing = await self.session.execute(select(Script).where(Script.name == name))
        if existing.scalar():
            raise DuplicateError(f"脚本 '{name}' 已存在")
        content = kwargs.get('content', '')
        if self._check_blocked(content):
            kwargs['is_blocked'] = True
        script = await self.script_repo.create(**kwargs)
        await self.session.flush()
        await self.session.refresh(script)
        return script

    async def list_scripts(self, script_type: str | None = None, page: int = 1, page_size: int = 20):
        stmt = select(Script)
        if script_type:
            stmt = stmt.where(Script.script_type == script_type)
        total_result = await self.session.execute(select(func.count()).select_from(Script))
        total = total_result.scalar() or 0
        result = await self.session.execute(stmt.order_by(Script.created_at.desc()).offset((page-1)*page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def create_playbook(self, **kwargs) -> Playbook:
        name = kwargs.get('name')
        existing = await self.session.execute(select(Playbook).where(Playbook.name == name))
        if existing.scalar():
            raise DuplicateError(f"Playbook '{name}' 已存在")
        pb = await self.playbook_repo.create(**kwargs)
        await self.session.flush()
        await self.session.refresh(pb)
        return pb

    async def list_playbooks(self, page: int = 1, page_size: int = 20):
        total_result = await self.session.execute(select(func.count()).select_from(Playbook))
        total = total_result.scalar() or 0
        result = await self.session.execute(
            select(Playbook).order_by(Playbook.created_at.desc()).offset((page-1)*page_size).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def create_execution(self, data: ExecutionCreate, user_id: str | None = None) -> Execution:
        # Check risk level
        risk = "low"
        if data.execution_type == "script":
            script = await self.script_repo.get_by_id(data.target_id)
            if script and script.is_blocked:
                raise ValueError("脚本已被阻断，不允许执行")
            if script:
                risk = script.risk_level
        elif data.execution_type == "playbook":
            pb = await self.playbook_repo.get_by_id(data.target_id)
            if pb:
                risk = pb.risk_level

        status = "pending"
        if data.is_dry_run:
            status = "dry_run"
        elif risk in ("high", "critical"):
            status = "awaiting_approval"

        exec_obj = await self.exec_repo.create(
            execution_type=data.execution_type,
            target_id=data.target_id,
            asset_ids=json.dumps(data.asset_ids),
            parameters=data.parameters,
            status=status,
            trigger_source=data.trigger_source,
            trigger_source_id=data.trigger_source_id,
            is_dry_run=data.is_dry_run,
            risk_level=risk,
        )
        await self.session.flush()
        await self.session.refresh(exec_obj)
        return exec_obj

    async def approve_execution(self, exec_id: str, user_id: str | None = None) -> Execution:
        exe = await self.exec_repo.get_by_id(exec_id)
        if not exe:
            raise NotFoundError(f"执行任务 {exec_id} 不存在")
        if exe.status != "awaiting_approval":
            raise ValueError("当前状态不允许审批")
        exe.status = "approved"
        exe.approved_by = user_id
        exe.approved_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(exe)
        return exe

    async def list_executions(self, status: str | None = None, page: int = 1, page_size: int = 20):
        stmt = select(Execution)
        if status:
            stmt = stmt.where(Execution.status == status)
        total_result = await self.session.execute(select(func.count()).select_from(Execution))
        total = total_result.scalar() or 0
        result = await self.session.execute(stmt.order_by(Execution.created_at.desc()).offset((page-1)*page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def get_execution(self, exec_id: str) -> Execution:
        exe = await self.exec_repo.get_by_id(exec_id)
        if not exe:
            raise NotFoundError(f"执行任务 {exec_id} 不存在")
        return exe


router = APIRouter(prefix="/scripts", tags=["脚本库"])
playbook_router = APIRouter(prefix="/playbooks", tags=["Playbook"])
exec_router = APIRouter(prefix="/executions", tags=["执行任务"])


def _get_svc(db: AsyncSession = Depends(get_db)) -> AutomationService:
    return AutomationService(db)


@router.get("")
async def list_scripts(
    script_type: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
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
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    svc: AutomationService = Depends(_get_svc),
):
    items, total = await svc.list_playbooks(page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@playbook_router.post("")
async def create_playbook(data: PlaybookCreate, svc: AutomationService = Depends(_get_svc)):
    pb = await svc.create_playbook(**data.model_dump())
    return success(model_to_dict(pb))


@exec_router.get("")
async def list_executions(
    status: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    svc: AutomationService = Depends(_get_svc),
):
    items, total = await svc.list_executions(status, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@exec_router.post("")
async def create_execution(data: ExecutionCreate, svc: AutomationService = Depends(_get_svc)):
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
