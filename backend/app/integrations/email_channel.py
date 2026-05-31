"""SMTP 邮件通知渠道."""
from __future__ import annotations
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.integrations.base import NotificationChannel, NotificationPayload

logger = logging.getLogger(__name__)

class EmailChannel(NotificationChannel):
    """SMTP 邮件通知."""

    def __init__(
        self,
        smtp_host: str = "",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_pass: str = "",
        from_addr: str = "",
        to_addrs: list[str] | None = None,
        use_tls: bool = True,
        enabled: bool = False,
    ):
        self._host = smtp_host
        self._port = smtp_port
        self._user = smtp_user
        self._pass = smtp_pass
        self._from = from_addr
        self._to = to_addrs or []
        self._tls = use_tls
        self._enabled = enabled

    @property
    def name(self) -> str:
        return "email"

    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self._host) and bool(self._to)

    async def send(self, payload: NotificationPayload) -> bool:
        if not self.enabled:
            return False
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[AUTOPS {payload.severity.upper()}] {payload.title}"
            msg["From"] = self._from
            msg["To"] = ", ".join(self._to)

            body = f"告警: {payload.title}\n严重级别: {payload.severity}"
            if payload.asset_name:
                body += f"\n资产: {payload.asset_name}"
            if payload.alert_id:
                body += f"\n告警ID: {payload.alert_id}"
            if payload.message:
                body += f"\n\n{payload.message}"

            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(self._host, self._port) as server:
                if self._tls:
                    server.starttls()
                if self._user and self._pass:
                    server.login(self._user, self._pass)
                server.sendmail(self._from, self._to, msg.as_string())
            return True
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False
