"""Webhook 通知渠道."""
from __future__ import annotations
import hashlib
import hmac
import json
import logging
import httpx
from app.integrations.base import NotificationChannel, NotificationPayload

logger = logging.getLogger(__name__)

class WebhookChannel(NotificationChannel):
    """通用 Webhook 通知渠道."""

    def __init__(self, url: str = "", secret: str | None = None, enabled: bool = False):
        self._url = url
        self._secret = secret
        self._enabled = enabled

    @property
    def name(self) -> str:
        return "webhook"

    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self._url)

    async def send(self, payload: NotificationPayload) -> bool:
        if not self.enabled:
            return False
        data = {
            "title": payload.title,
            "severity": payload.severity,
            "alert_id": payload.alert_id,
            "asset_name": payload.asset_name,
            "message": payload.message,
        }
        headers = {"Content-Type": "application/json"}
        if self._secret:
            sign = hmac.new(self._secret.encode(), json.dumps(data).encode(), hashlib.sha256).hexdigest()
            headers["X-Signature"] = sign
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(self._url, json=data, headers=headers)
                return r.status_code in (200, 201, 204)
        except Exception as e:
            logger.error(f"Webhook send failed: {e}")
            return False
