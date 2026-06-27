"""本地开发执行器 — 仅用于开发/测试环境.

生产环境应使用SSH执行器或沙箱执行器。
此执行器会在后端容器本地执行命令，但加上了命令策略校验。
"""

from __future__ import annotations

import asyncio
import logging
import re
import shlex
from datetime import datetime, timezone

from app.domains.automation.command_policy import CommandPolicy
from app.domains.automation.executor.base import ExecutionPlan, ExecutionResult
from app.infra.config import get_config

logger = logging.getLogger(__name__)

_policy = CommandPolicy()

# Shell metacharacters that indicate shell-level chaining/redirection
_SHELL_METACHAR_PATTERN = re.compile(
    r";|&&|\|\||\||>|<|>>|<<|\$\(|`|\n"
)


class LocalDevExecutor:
    """本地开发执行器 — 带命令策略校验."""

    async def dry_run(self, plan: ExecutionPlan) -> ExecutionResult:
        """模拟执行: 只检查命令策略，不实际运行."""
        result = _policy.evaluate(plan.command)
        return ExecutionResult(
            success=result.allowed,
            exit_code=0 if result.allowed else -1,
            stdout=f"[DRY-RUN] Command policy: {result.reason}\n"
                   f"Risk level: {result.risk_level}\n"
                   f"Requires approval: {result.requires_approval}",
            stderr="",
            started_at=datetime.now(timezone.utc).isoformat(),
            completed_at=datetime.now(timezone.utc).isoformat(),
            evidence={
                "policy_result": {
                    "allowed": result.allowed,
                    "risk_level": result.risk_level,
                    "reason": result.reason,
                    "requires_approval": result.requires_approval,
                },
            },
        )

    async def execute(self, plan: ExecutionPlan) -> ExecutionResult:
        """真实执行: 先通过命令策略，再运行."""
        # 0. Production guard — this executor must NEVER run in production
        if get_config().env == "prod":
            raise RuntimeError(
                "LocalDevExecutor is forbidden in production. "
                "Use SSH or sandbox executor."
            )

        # 0.5 Shell metacharacter detection — reject shell-level constructs
        if _SHELL_METACHAR_PATTERN.search(plan.command):
            raise ValueError(
                "Shell metacharacters not allowed. Use structured playbook steps."
            )

        # 1. 命令策略校验
        policy_result = _policy.evaluate(plan.command)
        if not policy_result.allowed:
            logger.warning("Command blocked by policy: %s", policy_result.reason)
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stderr=f"Command blocked: {policy_result.reason}",
                started_at=datetime.now(timezone.utc).isoformat(),
                completed_at=datetime.now(timezone.utc).isoformat(),
            )

        # 2. 执行命令 — NO shell wrapper, split via shlex
        started = datetime.now(timezone.utc)
        try:
            args = shlex.split(plan.command)
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=plan.timeout_seconds,
            )
            completed = datetime.now(timezone.utc)

            return ExecutionResult(
                success=proc.returncode == 0,
                exit_code=proc.returncode,
                stdout=(stdout or b"").decode("utf-8", errors="replace")[:10000],
                stderr=(stderr or b"").decode("utf-8", errors="replace")[:5000],
                started_at=started.isoformat(),
                completed_at=completed.isoformat(),
                evidence={"return_code": proc.returncode},
            )
        except asyncio.TimeoutError:
            proc.kill()
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stderr=f"Execution timeout ({plan.timeout_seconds}s)",
                started_at=started.isoformat(),
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stderr=str(exc)[:5000],
                started_at=started.isoformat(),
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
