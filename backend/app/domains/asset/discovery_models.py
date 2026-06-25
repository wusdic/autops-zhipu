"""资产发现 数据模型."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.database import Base


class DiscoveryTask(Base):
    """发现任务表."""

    __tablename__ = "discovery_tasks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    ip_range: Mapped[str] = mapped_column(String(500), nullable=False)
    ip_mode: Mapped[str] = mapped_column(String(20), default="cidr")
    protocols: Mapped[str | None] = mapped_column(JSON, nullable=True)
    ports: Mapped[str | None] = mapped_column(String(200), nullable=True)
    credential_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    timeout: Mapped[int] = mapped_column(Integer, default=30)
    # 是否自动纳管：开启后建任务即自动启动扫描，扫描完成自动纳管全部存活IP
    auto_onboard: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending/running/completed/failed
    discovered_count: Mapped[int] = mapped_column(Integer, default=0)
    onboarded_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DiscoveryResult(Base):
    """发现结果表."""

    __tablename__ = "discovery_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    task_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    ip: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    hostname: Mapped[str | None] = mapped_column(String(200), nullable=True)
    asset_type: Mapped[str] = mapped_column(String(50), default="linux_server")
    open_ports: Mapped[str | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="discovered"
    )  # discovered/onboarded/ignored
    metadata_: Mapped[str | None] = mapped_column("metadata", JSON, nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    onboarded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    asset_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
