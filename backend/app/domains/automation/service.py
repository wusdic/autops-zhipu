"""自动化执行中心 Service."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import DuplicateError, NotFoundError
from app.common.repository import BaseRepository
from app.domains.automation.models import Execution, ExecutionStep, Playbook, Script
from app.domains.automation.schemas import ExecutionCreate

# 高危命令黑名单
BLOCKED_COMMANDS = ["rm -rf /", "mkfs.", "dd if=", ":(){ :|:& };:", "format c:"]


class AutomationService:
    """自动化业务逻辑."""

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
        name = kwargs.get("name")
        existing = await self.session.execute(select(Script).where(Script.name == name))
        if existing.scalar():
            raise DuplicateError(f"脚本 '{name}' 已存在")
        content = kwargs.get("content", "")
        if self._check_blocked(content):
            kwargs["is_blocked"] = True
        script = await self.script_repo.create(**kwargs)
        await self.session.flush()
        await self.session.refresh(script)
        return script

    async def list_scripts(
        self, script_type: str | None = None, page: int = 1, page_size: int = 20
    ):
        stmt = select(Script)
        if script_type:
            stmt = stmt.where(Script.script_type == script_type)
        total_result = await self.session.execute(
            select(func.count()).select_from(Script)
        )
        total = total_result.scalar() or 0
        result = await self.session.execute(
            stmt.order_by(Script.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def create_playbook(self, **kwargs) -> Playbook:
        name = kwargs.get("name")
        existing = await self.session.execute(
            select(Playbook).where(Playbook.name == name)
        )
        if existing.scalar():
            raise DuplicateError(f"Playbook '{name}' 已存在")
        pb = await self.playbook_repo.create(**kwargs)
        await self.session.flush()
        await self.session.refresh(pb)
        return pb

    async def list_playbooks(self, page: int = 1, page_size: int = 20):
        total_result = await self.session.execute(
            select(func.count()).select_from(Playbook)
        )
        total = total_result.scalar() or 0
        result = await self.session.execute(
            select(Playbook)
            .order_by(Playbook.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def create_execution(
        self, data: ExecutionCreate, user_id: str | None = None
    ) -> Execution:
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

    async def approve_execution(
        self, exec_id: str, user_id: str | None = None
    ) -> Execution:
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

    async def list_executions(
        self, status: str | None = None, page: int = 1, page_size: int = 20
    ):
        stmt = select(Execution)
        if status:
            stmt = stmt.where(Execution.status == status)
        total_result = await self.session.execute(
            select(func.count()).select_from(Execution)
        )
        total = total_result.scalar() or 0
        result = await self.session.execute(
            stmt.order_by(Execution.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_execution(self, exec_id: str) -> Execution:
        exe = await self.exec_repo.get_by_id(exec_id)
        if not exe:
            raise NotFoundError(f"执行任务 {exec_id} 不存在")
        return exe
