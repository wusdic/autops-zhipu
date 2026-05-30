"""事件模型."""

from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import DateTime, String, Text, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.database import Base


class Event(Base):
    """事件表."""
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    # state_change, threshold_exceeded, service_down, port_unreachable, cert_expiring, collector_offline
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    # collector, automation, system, manual
    source_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    asset_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("assets.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(16), default="info")
    # info, warning, critical
    fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    is_deduplicated: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
