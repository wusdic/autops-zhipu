"""认证状态校验 — 用户禁用检查（带短期缓存）+ API Key 解析.

审查 P1-04：此前中间件只解析 JWT，不校验用户当前状态、也不支持 API Key：
- 用户被禁用/删除后，未过期 access token 仍可访问；
- 治理中心创建的 API Key 无法作为真实调用凭证。

为避免每个请求都查库，用户状态用进程内短 TTL 缓存（默认 30s）。
"""

from __future__ import annotations

import hashlib
import json
import logging
import time

logger = logging.getLogger(__name__)

# user_id -> (is_active, expires_at_monotonic)
_user_status_cache: dict[str, tuple[bool, float]] = {}
_USER_STATUS_TTL = 30.0


def invalidate_user_status(user_id: str) -> None:
    """禁用/删除用户后可调用以立即失效缓存（可选）."""
    _user_status_cache.pop(user_id, None)


async def is_user_active(user_id: str) -> bool:
    """用户是否有效（未禁用/未锁定/未删除），带 30s 缓存.

    DB 异常时 fail-open（仅记录日志）：JWT 本身已校验，避免数据库抖动导致全站 401。
    """
    now = time.monotonic()
    cached = _user_status_cache.get(user_id)
    if cached and cached[1] > now:
        return cached[0]

    try:
        from sqlalchemy import select

        from app.domains.governance.models import User
        from app.infra.database import async_session_factory

        async with async_session_factory() as session:
            row = (
                await session.execute(select(User).where(User.id == user_id))
            ).scalar_one_or_none()
        active = bool(row) and row.status == "active" and not row.is_deleted
    except Exception:  # noqa: BLE001
        logger.warning("用户状态校验查询失败，按放行处理 user_id=%s", user_id, exc_info=True)
        return True

    _user_status_cache[user_id] = (active, now + _USER_STATUS_TTL)
    return active


async def resolve_api_key(raw_key: str) -> tuple[str, list[str]] | None:
    """校验 X-API-Key，返回 (user_id, scopes) 或 None.

    Key 形如 ``ak_<hex>``，库内存 sha256(key_hash)。校验状态/过期，并更新 last_used_at。
    """
    if not raw_key or not raw_key.startswith("ak_"):
        return None
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    try:
        from datetime import datetime, timezone

        from sqlalchemy import select

        from app.domains.governance.models import ApiKey
        from app.infra.database import async_session_factory

        async with async_session_factory() as session:
            row = (
                await session.execute(
                    select(ApiKey).where(ApiKey.key_hash == key_hash)
                )
            ).scalar_one_or_none()
            if not row or row.status != "active":
                return None
            if row.expires_at and row.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
                return None
            try:
                scopes = json.loads(row.scope) if row.scope else []
            except (json.JSONDecodeError, ValueError):
                scopes = []
            if not isinstance(scopes, list):
                scopes = []
            # 更新 last_used_at（尽力，不阻断鉴权）
            try:
                row.last_used_at = datetime.now(timezone.utc)
                await session.commit()
            except Exception:  # noqa: BLE001
                await session.rollback()
            return str(row.user_id), scopes
    except Exception:  # noqa: BLE001
        logger.warning("API Key 校验查询失败", exc_info=True)
        return None
