"""通知规则模型."""

from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.database import Base


class NotificationRule(Base):
    """通知规则表."""
    __tablename__ = "notification_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # alert.created, alert.escalated, execution.completed, execution.failed, ticket.created, etc.
    target_type: Mapped[str] = mapped_column(String(32), default="user")
    # user, role, channel
    target_ids: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON array of user_ids / role_ids / channel_ids
    channels: Mapped[str] = mapped_column(String(256), nullable=False)
    # JSON array: ["email", "sms", "webhook", "in_app"]
    severity_filter: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # JSON array of severities to match, null = all
    quiet_hours_start: Mapped[str | None] = mapped_column(String(5), nullable=True)
    # HH:MM format
    quiet_hours_end: Mapped[str | None] = mapped_column(String(5), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
