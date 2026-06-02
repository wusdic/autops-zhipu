"""跨进程实时事件桥接 — 基于 Redis Pub/Sub.

架构:
  Worker 进程: handler 执行完后调 publish_realtime() → Redis PUBLISH
  API   进程: 启动时调 start_api_realtime_subscriber() → Redis SUBSCRIBE → WS broadcast

Channel: "autops:realtime"
消息格式: {"type": "<event_type>", "payload": {...}, "timestamp": "..."}
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

CHANNEL = "autops:realtime"

# 全局订阅任务引用
_subscriber_task: asyncio.Task | None = None


async def publish_realtime(event_type: str, payload: dict[str, Any]) -> None:
    """发布实时事件到 Redis channel（Worker 侧调用）."""
    from app.infra.redis_client import get_redis

    try:
        redis = await get_redis()
        msg = json.dumps({
            "type": event_type,
            "payload": payload,
        }, ensure_ascii=False, default=str)
        await redis.publish(CHANNEL, msg)
    except Exception:
        logger.debug("publish_realtime failed (Redis unavailable?): %s", event_type, exc_info=True)


async def _realtime_listener(on_message) -> None:
    """订阅 Redis channel 并回调（API 侧内部使用）."""
    from app.infra.redis_client import get_redis

    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(CHANNEL)
    logger.info("Realtime subscriber listening on channel: %s", CHANNEL)

    try:
        async for msg in pubsub.listen():
            if msg.get("type") != "message":
                continue
            try:
                data = json.loads(msg["data"])
                await on_message(data)
            except Exception:
                logger.exception("Realtime listener: error processing message")
    except asyncio.CancelledError:
        pass
    finally:
        try:
            await pubsub.unsubscribe(CHANNEL)
        except Exception:
            pass
        logger.info("Realtime subscriber stopped")


async def start_api_realtime_subscriber(on_message) -> asyncio.Task:
    """在 API 进程中启动实时事件订阅（lifespan 中调用）.

    Returns:
        订阅任务，可在 shutdown 时 cancel。
    """
    global _subscriber_task
    _subscriber_task = asyncio.create_task(
        _realtime_listener(on_message),
        name="realtime-subscriber",
    )
    return _subscriber_task


async def stop_api_realtime_subscriber() -> None:
    """停止实时事件订阅（shutdown 时调用）."""
    global _subscriber_task
    if _subscriber_task and not _subscriber_task.done():
        _subscriber_task.cancel()
        try:
            await _subscriber_task
        except asyncio.CancelledError:
            pass
    _subscriber_task = None
