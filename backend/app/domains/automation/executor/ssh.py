"""SSH 执行器 — 生产可用.

通过凭证中心解析目标资产的 SSH 凭据，用 asyncssh 在远端执行脚本/命令。
支持多行脚本（经远端 shell 执行），但仍拦截绝对高危命令与 fork 炸弹。
asyncssh 懒加载：未安装时返回结构化错误而非崩溃。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.domains.automation.command_policy import CommandPolicy
from app.domains.automation.executor.base import ExecutionPlan, ExecutionResult

logger = logging.getLogger(__name__)

_policy = CommandPolicy()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fail(reason: str, started: str) -> ExecutionResult:
    return ExecutionResult(
        success=False, exit_code=-1, stderr=reason,
        started_at=started, completed_at=_now(),
    )


def _hard_blocked(command: str) -> str | None:
    """仅拦截绝对高危：DANGEROUS_COMMANDS 首词 / fork 炸弹。返回拦截原因或 None."""
    if ":(){:|:&}" in command or "fork bomb" in command.lower():
        return "检测到 fork 炸弹模式"
    first_line = next((ln.strip() for ln in command.splitlines() if ln.strip()), "")
    if not first_line:
        return "空命令"
    exe = first_line.split()[0].split("/")[-1]
    if exe in CommandPolicy.DANGEROUS_COMMANDS:
        return f"禁止执行高危命令: {exe}"
    return None


class SSHExecutor:
    """SSH 远程执行器."""

    async def dry_run(self, plan: ExecutionPlan) -> ExecutionResult:
        # dry-run 只做策略评估（按首行），不连远端
        first_line = next((ln for ln in plan.command.splitlines() if ln.strip()), "")
        result = _policy.evaluate(first_line)
        return ExecutionResult(
            success=result.allowed,
            exit_code=0 if result.allowed else -1,
            stdout=f"[DRY-RUN] {result.reason}\nrisk={result.risk_level} "
                   f"approval={result.requires_approval}",
            started_at=_now(), completed_at=_now(),
            evidence={"policy_result": {
                "allowed": result.allowed, "risk_level": result.risk_level,
                "reason": result.reason, "requires_approval": result.requires_approval,
            }},
        )

    async def execute(self, plan: ExecutionPlan) -> ExecutionResult:
        started = _now()
        try:
            import asyncssh  # 懒加载
        except ImportError:
            return _fail("method_unavailable: asyncssh 未安装", started)

        # 绝对高危拦截
        blocked = _hard_blocked(plan.command)
        if blocked:
            logger.warning("SSH 执行被拦截: %s", blocked)
            return _fail(f"Command blocked: {blocked}", started)

        if not plan.asset_id:
            return _fail("缺少目标资产(asset_id)", started)

        # 解析目标资产 + 凭据
        from sqlalchemy import select

        from app.common.credentials import resolve_asset_credential
        from app.domains.asset.models import Asset
        from app.infra.database import async_session_factory

        async with async_session_factory() as session:
            asset = (
                await session.execute(select(Asset).where(Asset.id == plan.asset_id))
            ).scalar_one_or_none()
            if not asset or not asset.ip:
                return _fail("目标资产不存在或无 IP", started)
            cred = await resolve_asset_credential(
                session, plan.asset_id, prefer=["ssh_key", "ssh_password"]
            )
        if cred is None or (not cred.password and not cred.private_key):
            return _fail("目标资产无可用 SSH 凭据", started)

        connect_kwargs: dict = {
            "host": asset.ip,
            "port": asset.port or 22,
            "known_hosts": None,
            "username": cred.username or "root",
        }
        if cred.private_key:
            try:
                connect_kwargs["client_keys"] = [asyncssh.import_private_key(cred.private_key)]
            except Exception as exc:  # noqa: BLE001
                return _fail(f"私钥解析失败: {exc}", started)
        else:
            connect_kwargs["password"] = cred.password

        try:
            import asyncio

            async with asyncio.timeout(plan.timeout_seconds or 300):
                async with asyncssh.connect(**connect_kwargs) as conn:
                    res = await conn.run(plan.command, check=False)
            completed = _now()
            return ExecutionResult(
                success=res.exit_status == 0,
                exit_code=res.exit_status,
                stdout=(res.stdout or "")[:10000],
                stderr=(res.stderr or "")[:5000],
                started_at=started, completed_at=completed,
                evidence={"host": asset.ip, "return_code": res.exit_status},
            )
        except Exception as exc:  # noqa: BLE001
            logger.info("SSH 执行失败 host=%s: %s", asset.ip, exc)
            return _fail(f"ssh_error: {str(exc)[:500]}", started)
