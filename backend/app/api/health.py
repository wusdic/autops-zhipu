"""健康检查路由."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.infra.database import get_db
from app.infra.redis_client import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    """存活检查."""
    return {"status": "alive"}


@router.get("/ready")
async def ready():
    """就绪检查：DB + Redis."""
    checks = {}

    # 数据库
    try:
        db = await anext(get_db())
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Redis
    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ready" if all_ok else "degraded", "checks": checks}


# Platform status (mounted under /api/v1/platform)
platform_router = APIRouter(prefix="/platform", tags=["平台管理"])


@platform_router.get("/status")
async def platform_status():
    """平台组件状态."""
    from app.common.response import success
    checks = {}

    # 数据库
    try:
        db = await anext(get_db())
        await db.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok"}
    except Exception as e:
        checks["database"] = {"status": "error", "message": str(e)}

    # Redis
    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = {"status": "ok"}
    except Exception as e:
        checks["redis"] = {"status": "error", "message": str(e)}

    all_ok = all(v.get("status") == "ok" for v in checks.values())
    return success({
        "status": "healthy" if all_ok else "degraded",
        "components": checks,
        "version": "1.0.0",
    })
