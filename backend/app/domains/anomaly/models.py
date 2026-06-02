"""异常检测模型."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.database import Base


class Anomaly(Base):
    """异常检测结果表."""

    __tablename__ = "anomalies"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    # detector / rule / ml_model / external
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    # low, medium, high, critical
    status: Mapped[str] = mapped_column(
        String(16), default="open", nullable=False, index=True
    )
    # open, acknowledged, resolved, closed
    asset_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    assigned_to: Mapped[str | None] = mapped_column(String(36), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # additional metadata: scores, indicators, etc.
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
