"""钉钉机器人通知渠道."""
from __future__ import annotations
import hashlib
import hmac
import base64
import time
import logging
import urllib.parse
import httpx
from app.integrations.base import NotificationChannel, NotificationPayload

logger = logging.getLogger(__name__)

class DingTalkChannel(NotificationChannel):
    """钉钉机器人 Webhook 通知."""

    SEVERITY_EMOJI = {
        "critical": "🔴",
        "warning": "🟡",
        "info": "🔵",
    }

    def __init__(self, webhook_url: str = "", secret: str | None = None, at_mobiles: list[str] | None = None, enabled: bool = False):
        self._webhook_url = webhook_url
        self._secret = secret
        self._at_mobiles = at_mobiles or []
        self._enabled = enabled

    @property
    def name(self) -> str:
        return "dingtalk"

    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self._webhook_url)

    def _build_url(self) -> str:
        url = self._webhook_url
        if self._secret:
            ts = str(round(time.time() * 1000))
            string_to_sign = f"{ts}\n{self._secret}"
            hmac_code = hmac.new(self._secret.encode(), string_to_sign.encode(), hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            url = f"{url}&timestamp={ts}&sign={sign}"
        return url

    async def send(self, payload: NotificationPayload) -> bool:
        if not self.enabled:
            return False
        emoji = self.SEVERITY_EMOJI.get(payload.severity, "ℹ️")
        text = f"{emoji} **[{payload.severity.upper()}]** {payload.title}"
        if payload.asset_name:
            text += f"\n资产: {payload.asset_name}"
        if payload.message:
            text += f"\n{payload.message}"
        
        body = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"[{payload.severity.upper()}] {payload.title}",
                "text": text
            }
        }
        if self._at_mobiles:
            body["at"] = {"atMobiles": self._at_mobiles, "isAtAll": False}

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(self._build_url(), json=body)
                result = r.json()
                return result.get("errcode") == 0
        except Exception as e:
            logger.error(f"DingTalk send failed: {e}")
            return False
