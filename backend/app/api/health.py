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
