"""通知渠道抽象基类."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

@dataclass
class NotificationPayload:
    """通知负载."""
    title: str
    severity: str = "info"
    alert_id: str | None = None
    asset_name: str | None = None
    message: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

class NotificationChannel(ABC):
    """通知渠道抽象基类."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def enabled(self) -> bool:
        ...

    @abstractmethod
    async def send(self, payload: NotificationPayload) -> bool:
        ...
