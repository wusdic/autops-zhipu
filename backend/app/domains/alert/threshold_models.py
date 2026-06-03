"""阈值规则模型（独立于告警规则，用于指标阈值检测）."""

from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.database import Base


class ThresholdRule(Base):
    """阈值规则表."""
    __tablename__ = "threshold_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metric_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    # e.g. cpu_usage, memory_usage, disk_usage, response_time
    asset_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # linux_server, windows_server, database, web_service
    condition: Mapped[str] = mapped_column(String(16), nullable=False)
    # gt, gte, lt, lte, eq, neq
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    # 持续时间，0=即时触发
    severity: Mapped[str] = mapped_column(String(16), default="warning")
    # critical, high, warning, info
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_channels: Mapped[str | None] = mapped_column(String(256), nullable=True)
    # JSON array of channel names
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
