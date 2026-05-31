"""外部系统集成."""
from app.integrations.base import NotificationChannel, NotificationPayload
from app.integrations.registry import NotificationRegistry

__all__ = ["NotificationChannel", "NotificationPayload", "NotificationRegistry"]
