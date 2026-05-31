"""通知渠道注册中心."""
from __future__ import annotations
import logging
from typing import Any
from app.integrations.base import NotificationChannel, NotificationPayload

logger = logging.getLogger(__name__)

class NotificationRegistry:
    """通知渠道注册中心."""
    _instance: NotificationRegistry | None = None
    _channels: dict[str, NotificationChannel]

    def __init__(self):
        self._channels = {}

    @classmethod
    def get_instance(cls) -> NotificationRegistry:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, channel: NotificationChannel):
        self._channels[channel.name] = channel

    def get(self, name: str) -> NotificationChannel | None:
        return self._channels.get(name)

    def list_channels(self) -> list[str]:
        return list(self._channels.keys())

    async def broadcast(self, payload: NotificationPayload) -> dict[str, bool]:
        """向所有启用的渠道广播通知."""
        results = {}
        for name, channel in self._channels.items():
            if channel.enabled:
                try:
                    ok = await channel.send(payload)
                    results[name] = ok
                    if ok:
                        logger.info(f"Notification sent via {name}: {payload.title}")
                    else:
                        logger.warning(f"Notification failed via {name}: {payload.title}")
                except Exception as e:
                    results[name] = False
                    logger.error(f"Notification error via {name}: {e}")
        return results
