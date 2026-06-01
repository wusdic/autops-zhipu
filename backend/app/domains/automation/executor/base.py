"""执行器抽象基类."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel


class ExecutionPlan(BaseModel):
    """执行计划."""
    execution_id: str
    trace_id: str = ""
    asset_id: str = ""
    command: str
    working_dir: str | None = None
    timeout_seconds: int = 300
    env_vars: dict[str, str] = {}


class ExecutionResult(BaseModel):
    """执行结果."""
    success: bool
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    started_at: str = ""
    completed_at: str = ""
    evidence: dict = {}


class Executor(Protocol):
    """执行器协议 — 所有执行器必须实现此接口."""

    async def dry_run(self, plan: ExecutionPlan) -> ExecutionResult:
        """模拟执行 (不产生真实变更)."""
        ...

    async def execute(self, plan: ExecutionPlan) -> ExecutionResult:
        """真实执行."""
        ...
