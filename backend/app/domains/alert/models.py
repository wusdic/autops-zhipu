"""告警模型."""

from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, Text, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.database import Base


class AlertRule(Base):
    """告警规则表."""
    __tablename__ = "alert_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_types: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON array of event_type strings
    conditions: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON: condition expression
    severity: Mapped[str] = mapped_column(String(16), default="warning")
    suppress_duration: Mapped[int] = mapped_column(Integer, default=0)
    # seconds, 0=no suppress
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Alert(Base):
    """告警表."""
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    # info, warning, critical
    status: Mapped[str] = mapped_column(String(16), default="firing", nullable=False, index=True)
    # firing, acknowledged, resolved, suppressed
    rule_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("alert_rules.id"), nullable=True)
    event_ids: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON array
    asset_ids: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON array
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON: alert context (metrics, logs, etc.)
    acknowledged_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ticket_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
