"""自动化执行中心 Service.

重构要点:
1. 使用 Executor Adapter 而非直接 /bin/bash
2. 并发锁正确解析 JSON 字符串
3. 命令策略校验由 CommandPolicy 处理
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import DuplicateError, NotFoundError
from app.common.repository import BaseRepository
from app.domains.automation.models import Execution, ExecutionStep, Playbook, Script, ExecutionStatus
from app.domains.automation.schemas import ExecutionCreate
from app.domains.automation.command_policy import CommandPolicy
from app.domains.automation.executor.local_dev import LocalDevExecutor

_policy = CommandPolicy()
_executor = LocalDevExecutor()


class AutomationService:
    """自动化业务逻辑."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.script_repo = BaseRepository(session, Script)
        self.playbook_repo = BaseRepository(session, Playbook)
        self.exec_repo = BaseRepository(session, Execution)
        self.step_repo = BaseRepository(session, ExecutionStep)

    # ============= 脚本管理 =============

    async def create_script(self, **kwargs) -> Script:
        name = kwargs.get("name")
        existing = await self.session.execute(select(Script).where(Script.name == name))
        if existing.scalar():
            raise DuplicateError(f"脚本 '{name}' 已存在")
        content = kwargs.get("content", "")
        policy_result = _policy.evaluate(content)
        if not policy_result.allowed:
            kwargs["is_blocked"] = True
        elif policy_result.requires_approval:
            kwargs["risk_level"] = policy_result.risk_level
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
        result = await self.session.execute(
            stmt.order_by(Script.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def update_script(self, script_id: str, **kwargs) -> Script:
        script = await self.script_repo.get_by_id(script_id)
        if not script:
            raise NotFoundError(f"脚本 {script_id} 不存在")
        content = kwargs.get("content")
        if content:
            policy_result = _policy.evaluate(content)
            if not policy_result.allowed:
                kwargs["is_blocked"] = True
        for key, value in kwargs.items():
            if value is not None and hasattr(script, key):
                setattr(script, key, value)
        await self.session.flush()
        await self.session.refresh(script)
        return script

    async def delete_script(self, script_id: str) -> None:
        script = await self.script_repo.get_by_id(script_id)
        if not script:
            raise NotFoundError(f"脚本 {script_id} 不存在")
        await self.session.delete(script)
        await self.session.flush()

    # ============= Playbook 管理 =============

    async def create_playbook(self, **kwargs) -> Playbook:
        name = kwargs.get("name")
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
            select(Playbook).order_by(Playbook.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_playbook(self, playbook_id: str) -> Playbook:
        pb = await self.playbook_repo.get_by_id(playbook_id)
        if not pb:
            raise NotFoundError(f"Playbook {playbook_id} 不存在")
        return pb

    async def update_playbook(self, playbook_id: str, **kwargs) -> Playbook:
        pb = await self.playbook_repo.get_by_id(playbook_id)
        if not pb:
            raise NotFoundError(f"Playbook {playbook_id} 不存在")
        for key, value in kwargs.items():
            if value is not None and hasattr(pb, key):
                setattr(pb, key, value)
        await self.session.flush()
        await self.session.refresh(pb)
        return pb

    async def delete_playbook(self, playbook_id: str) -> None:
        pb = await self.playbook_repo.get_by_id(playbook_id)
        if not pb:
            raise NotFoundError(f"Playbook {playbook_id} 不存在")
        await self.session.delete(pb)
        await self.session.flush()

    # ============= 执行管理 =============

    async def create_execution(self, data: ExecutionCreate, user_id: str | None = None) -> Execution:
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

        status = ExecutionStatus.PENDING
        if not data.is_dry_run and risk in ("high", "critical"):
            status = ExecutionStatus.AWAITING_APPROVAL

        if not data.is_dry_run and data.asset_ids:
            if await self._check_concurrent_lock(data.asset_ids):
                raise ValueError("目标资产有正在运行的执行任务，请等待完成后再试")

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
        if exe.status != ExecutionStatus.AWAITING_APPROVAL:
            raise ValueError("当前状态不允许审批")
        exe.status = ExecutionStatus.APPROVED
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
        result = await self.session.execute(
            stmt.order_by(Execution.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_execution(self, exec_id: str) -> Execution:
        exe = await self.exec_repo.get_by_id(exec_id)
        if not exe:
            raise NotFoundError(f"执行任务 {exec_id} 不存在")
        return exe

    async def cancel_execution(self, exec_id: str) -> Execution:
        exe = await self.exec_repo.get_by_id(exec_id)
        if not exe:
            raise NotFoundError(f"执行任务 {exec_id} 不存在")
        if exe.status not in (ExecutionStatus.PENDING, ExecutionStatus.AWAITING_APPROVAL, ExecutionStatus.APPROVED, ExecutionStatus.RUNNING):
            raise ValueError("当前状态不允许取消")
        exe.status = ExecutionStatus.CANCELLED
        exe.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(exe)
        return exe

    async def rollback_execution(self, exec_id: str, user_id: str = "") -> Execution:
        """回滚执行 — 执行 Playbook 中定义的回滚步骤.

        状态流: rolling_back → 执行回滚步骤 → rolled_back / rollback_failed
        """
        execution = await self.get_execution(exec_id)
        if execution.status not in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.DRY_RUN_COMPLETED, ExecutionStatus.DRY_RUN_FAILED):
            raise ValueError("只能回滚已完成或失败的执行")

        # 收集回滚步骤
        rollback_steps: list[dict] = []

        if execution.execution_type == "playbook":
            pb = await self.playbook_repo.get_by_id(execution.target_id)
            if pb:
                # playbook.steps 是 JSON 字符串, 解析后查找 rollback_steps 或 steps 中含 rollback 的
                try:
                    steps_data = json.loads(pb.steps) if isinstance(pb.steps, str) else pb.steps
                except (json.JSONDecodeError, TypeError):
                    steps_data = []

                if isinstance(steps_data, list):
                    for step in steps_data:
                        if isinstance(step, dict) and step.get("rollback"):
                            rollback_steps.append(step)

        if not rollback_steps:
            raise ValueError("No rollback plan defined for this execution")

        execution.status = ExecutionStatus.ROLLING_BACK
        await self.session.flush()

        from app.domains.automation.executor.base import ExecutionPlan

        all_success = True
        for idx, rb_step in enumerate(rollback_steps):
            step_name = rb_step.get("name", f"rollback_step_{idx + 1}")
            command = rb_step.get("rollback", rb_step.get("command", ""))

            await self.append_execution_log(
                str(execution.id),
                {
                    "step_id": step_name,
                    "status": "running",
                    "message": f"Executing rollback step {idx + 1}/{len(rollback_steps)}: {step_name}",
                },
            )

            plan = ExecutionPlan(
                execution_id=str(execution.id),
                command=str(command),
                timeout_seconds=rb_step.get("timeout", 300),
            )

            try:
                result = await _executor.execute(plan)
                step_status = ExecutionStatus.COMPLETED if result.success else ExecutionStatus.FAILED
                if not result.success:
                    all_success = False

                await self.append_execution_log(
                    str(execution.id),
                    {
                        "step_id": step_name,
                        "status": step_status,
                        "stdout": result.stdout[:5000] if result.stdout else "",
                        "stderr": result.stderr[:2000] if result.stderr else "",
                        "exit_code": result.exit_code,
                    },
                )
            except Exception as exc:
                all_success = False
                await self.append_execution_log(
                    str(execution.id),
                    {
                        "step_id": step_name,
                        "status": "failed",
                        "error": str(exc),
                    },
                )

        execution.status = ExecutionStatus.ROLLED_BACK if all_success else ExecutionStatus.ROLLBACK_FAILED
        execution.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(execution)
        return execution

    async def append_execution_log(self, execution_id: str, log_entry: dict) -> None:
        exe = await self.exec_repo.get_by_id(execution_id)
        if not exe:
            return
        result = await self.session.execute(
            select(func.count()).select_from(ExecutionStep).where(
                ExecutionStep.execution_id == execution_id
            )
        )
        step_num = (result.scalar() or 0) + 1
        step = ExecutionStep(
            execution_id=execution_id,
            step_number=step_num,
            name=log_entry.get("step_id", "log"),
            status=log_entry.get("status", "info"),
            result=json.dumps(log_entry, ensure_ascii=False, default=str),
        )
        self.session.add(step)
        await self.session.flush()

    async def run_execution(self, exec_id: str) -> Execution:
        """执行脚本/命令 — 通过 Executor Adapter.

        状态机:
          Normal:   pending/approved → running → completed / failed
          Dry-run:  pending/approved → dry_running → dry_run_completed / dry_run_failed
        """
        exe = await self.exec_repo.get_by_id(exec_id)
        if not exe:
            raise NotFoundError(f"执行任务 {exec_id} 不存在")
        if exe.status not in (ExecutionStatus.PENDING, ExecutionStatus.APPROVED):
            raise ValueError(f"当前状态 {exe.status} 不允许执行")

        is_dry = getattr(exe, "is_dry_run", False)

        # Set appropriate intermediate status
        exe.status = ExecutionStatus.DRY_RUNNING if is_dry else ExecutionStatus.RUNNING
        exe.started_at = datetime.now(timezone.utc)
        await self.session.flush()

        # 加载脚本内容
        content = ""
        if exe.execution_type == "script":
            script = await self.script_repo.get_by_id(exe.target_id)
            content = script.content if script else ""
        elif exe.execution_type == "playbook":
            pb = await self.playbook_repo.get_by_id(exe.target_id)
            content = pb.steps if pb else ""

        if not content:
            exe.status = "dry_run_failed" if is_dry else "failed"
            exe.error_message = "无执行内容"
            exe.completed_at = datetime.now(timezone.utc)
            await self.session.flush()
            return exe

        # 通过 Executor 执行
        from app.domains.automation.executor.base import ExecutionPlan
        plan = ExecutionPlan(
            execution_id=str(exe.id),
            command=content if isinstance(content, str) else str(content),
            timeout_seconds=300,
        )

        if is_dry:
            result = await _executor.dry_run(plan)
        else:
            result = await _executor.execute(plan)

        exe.result = result.stdout[:10000] if result.stdout else None
        exe.error_message = result.stderr[:5000] if result.stderr else None

        if not result.success:
            if is_dry:
                exe.status = ExecutionStatus.DRY_RUN_FAILED
            else:
                # policy 阻断也归为 failed（blocked 不在合法状态枚举中）
                exe.status = ExecutionStatus.FAILED
                if "blocked" in (result.stderr or "").lower():
                    exe.error_message = f"Command blocked by policy: {result.stderr[:4000]}"
        else:
            exe.status = ExecutionStatus.DRY_RUN_COMPLETED if is_dry else ExecutionStatus.COMPLETED

        exe.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(exe)
        return exe

    async def _check_concurrent_lock(self, asset_ids: list[str]) -> bool:
        """检查资产是否有正在运行的执行 — 使用 ExecutionStatus.LOCK_HOLDING 统一判断."""
        result = await self.session.execute(
            select(Execution).where(
                Execution.status.in_(list(ExecutionStatus.LOCK_HOLDING)),
            )
        )
        running = result.scalars().all()
        for exe in running:
            exe_assets = []
            raw = exe.asset_ids
            if isinstance(raw, list):
                exe_assets = raw
            elif isinstance(raw, str):
                try:
                    exe_assets = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    exe_assets = []
            if isinstance(exe_assets, list) and set(asset_ids) & set(exe_assets):
                return True
        return False
