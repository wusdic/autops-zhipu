"""健康检查路由."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from sqlalchemy import text

from app.infra.database import get_session_factory
from app.infra.redis_client import get_redis

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


async def _check_db() -> bool:
    """检查数据库连通性，正确关闭会话避免连接泄漏."""
    session_factory = get_session_factory()
    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("健康检查：数据库连接失败")
        return False


@router.get("/health")
async def health():
    """存活检查."""
    return {"status": "alive"}


@router.get("/ready")
async def ready():
    """就绪检查：DB + Redis。

    对外只返回 ok/error 状态，不回显异常详情（避免泄漏内部拓扑）。
    """
    checks: dict[str, str] = {}

    checks["database"] = "ok" if await _check_db() else "error"

    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = "ok"
    except Exception:
        logger.exception("健康检查：Redis 连接失败")
        checks["redis"] = "error"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ready" if all_ok else "degraded", "checks": checks}


# Platform status (mounted under /api/v1/platform)
platform_router = APIRouter(prefix="/platform", tags=["平台管理"])


@platform_router.get("/status")
async def platform_status():
    """平台组件状态。

    对外只返回 ok/error 状态，不回显异常详情（避免泄漏内部拓扑）。
    """
    from app.common.response import success

    checks: dict[str, dict] = {}

    checks["database"] = {"status": "ok" if await _check_db() else "error"}

    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = {"status": "ok"}
    except Exception:
        logger.exception("平台状态检查：Redis 连接失败")
        checks["redis"] = {"status": "error"}

    all_ok = all(v.get("status") == "ok" for v in checks.values())
    return success(
        {
            "status": "healthy" if all_ok else "degraded",
            "components": checks,
            "version": "1.0.0",
        }
    )
