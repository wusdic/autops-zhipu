"""自动化执行队列 — 持久化领取/续租/心跳/幂等重试.

设计动机（审查 P0-03/P1-03/P2-5）：
此前 EXECUTION_CREATED 事件在 outbox handler 中用 `asyncio.create_task` 后台跑，
进程退出即丢任务、异常不会触发重试。改为：
- handler/审批/API 同步把执行入队（`enqueue`），失败抛错触发 outbox 重试；
- 独立的 ExecutionWorker 用 `lease_one` 领取、`heartbeat` 续租、`complete`/`fail`
  收尾，崩溃后租约过期自动回收重投，超过 max_attempts 进 failed。

仅依赖原生 SQL（与 outbox 一致），available_at/lease_expires_at 在 Python 侧算好
传参，避免方言相关的 DATE_ADD。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# 非终态状态（用于幂等去重）
_ACTIVE = ("queued", "leased")


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def enqueue(
    session: AsyncSession, execution_id: str, max_attempts: int = 3
) -> bool:
    """把执行任务入队（幂等：已有未完成队列项则跳过）。

    复用调用方事务（不自行 commit），失败由调用方回滚/重试。
    返回 True 表示新入队，False 表示已存在跳过。
    """
    exists = (
        await session.execute(
            text(
                "SELECT id FROM execution_queue "
                "WHERE execution_id = :eid AND status IN ('queued', 'leased') LIMIT 1"
            ),
            {"eid": execution_id},
        )
    ).first()
    if exists:
        return False
    now = _now()
    await session.execute(
        text(
            "INSERT INTO execution_queue "
            "(id, execution_id, status, attempts, max_attempts, available_at, "
            " created_at, updated_at) "
            "VALUES (:id, :eid, 'queued', 0, :mx, :now, :now, :now)"
        ),
        {
            "id": str(uuid.uuid4()),
            "eid": execution_id,
            "mx": max_attempts,
            "now": now,
        },
    )
    return True


async def lease_one(
    session: AsyncSession, owner: str, lease_seconds: int = 300
) -> dict | None:
    """领取一条可用队列项（先回收过期租约）。

    使用 FOR UPDATE SKIP LOCKED 避免多 Worker 抢同一行。
    返回 {queue_id, execution_id, attempts, max_attempts} 或 None。
    """
    # 0. 回收过期租约（崩溃/超时的任务重新可领）
    await session.execute(
        text(
            "UPDATE execution_queue "
            "SET status='queued', lease_owner=NULL, lease_expires_at=NULL "
            "WHERE status='leased' AND lease_expires_at < :now"
        ),
        {"now": _now()},
    )
    await session.commit()

    # 1. 领取一条 queued 且到期可用的任务
    row = (
        await session.execute(
            text(
                "SELECT id, execution_id, attempts, max_attempts "
                "FROM execution_queue "
                "WHERE status='queued' AND available_at <= :now "
                "ORDER BY available_at ASC, created_at ASC "
                "LIMIT 1 FOR UPDATE SKIP LOCKED"
            ),
            {"now": _now()},
        )
    ).first()
    if not row:
        await session.commit()
        return None

    expires = _now() + timedelta(seconds=lease_seconds)
    await session.execute(
        text(
            "UPDATE execution_queue "
            "SET status='leased', lease_owner=:o, lease_expires_at=:exp, "
            "    heartbeat_at=:now, attempts=attempts+1, updated_at=:now "
            "WHERE id=:id"
        ),
        {"o": owner, "exp": expires, "now": _now(), "id": row.id},
    )
    await session.commit()
    return {
        "queue_id": row.id,
        "execution_id": row.execution_id,
        "attempts": (row.attempts or 0) + 1,
        "max_attempts": row.max_attempts or 3,
    }


async def heartbeat(
    session: AsyncSession, queue_id: str, owner: str, lease_seconds: int = 300
) -> None:
    """续租：延长 lease_expires_at，证明任务仍在执行。"""
    expires = _now() + timedelta(seconds=lease_seconds)
    await session.execute(
        text(
            "UPDATE execution_queue "
            "SET lease_expires_at=:exp, heartbeat_at=:now, updated_at=:now "
            "WHERE id=:id AND lease_owner=:o"
        ),
        {"exp": expires, "now": _now(), "id": queue_id, "o": owner},
    )
    await session.commit()


async def complete(session: AsyncSession, queue_id: str) -> None:
    """标记任务完成。"""
    await session.execute(
        text(
            "UPDATE execution_queue "
            "SET status='done', lease_owner=NULL, lease_expires_at=NULL, updated_at=:now "
            "WHERE id=:id"
        ),
        {"now": _now(), "id": queue_id},
    )
    await session.commit()


async def fail(
    session: AsyncSession,
    queue_id: str,
    error: str,
    attempts: int,
    max_attempts: int,
    backoff_base: int = 10,
) -> bool:
    """任务失败：未达上限则指数退避重投，否则进 failed。

    返回 True 表示已重投，False 表示已进入 failed 终态。
    """
    err = (error or "")[:4000]
    if attempts < max_attempts:
        delay = (2 ** attempts) * backoff_base
        available_at = _now() + timedelta(seconds=delay)
        await session.execute(
            text(
                "UPDATE execution_queue "
                "SET status='queued', lease_owner=NULL, lease_expires_at=NULL, "
                "    available_at=:avail, last_error=:e, updated_at=:now "
                "WHERE id=:id"
            ),
            {"avail": available_at, "e": err, "now": _now(), "id": queue_id},
        )
        await session.commit()
        logger.info(
            "execution_queue: %s 重投 attempt=%d/%d delay=%ds",
            queue_id, attempts, max_attempts, delay,
        )
        return True
    await session.execute(
        text(
            "UPDATE execution_queue "
            "SET status='failed', lease_owner=NULL, lease_expires_at=NULL, "
            "    last_error=:e, updated_at=:now "
            "WHERE id=:id"
        ),
        {"e": err, "now": _now(), "id": queue_id},
    )
    await session.commit()
    logger.warning("execution_queue: %s 超过最大重试，标记 failed", queue_id)
    return False
