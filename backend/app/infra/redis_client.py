"""AUTOPS Redis 客户端."""

from __future__ import annotations

from redis.asyncio import Redis

from app.infra.config import get_config

_redis: Redis | None = None


async def get_redis() -> Redis:
    """获取 Redis 客户端."""
    global _redis
    if _redis is None:
        config = get_config()
        _redis = Redis.from_url(config.redis.url, decode_responses=True)
    return _redis


async def close_redis():
    """关闭 Redis 连接."""
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None
