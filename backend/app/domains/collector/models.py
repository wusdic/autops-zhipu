"""采集器模型."""

from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.database import Base


class Collector(Base):
    """采集器注册表."""
    __tablename__ = "collectors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    collector_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # ssh, wmi, http, tcp, database, certificate, snmp
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    config_schema: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CollectionJob(Base):
    """采集任务表."""
    __tablename__ = "collection_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    collector_id: Mapped[str] = mapped_column(String(36), ForeignKey("collectors.id"), nullable=False, index=True)
    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("assets.id"), nullable=False, index=True)
    config_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    credential_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("credentials.id"), nullable=True)
    schedule: Mapped[str] = mapped_column(String(64), default="manual")
    # cron expression or "manual"
    status: Mapped[str] = mapped_column(String(16), default="active")
    # active, paused, disabled
    timeout: Mapped[int] = mapped_column(Integer, default=300)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class CollectionResult(Base):
    """采集结果表."""
    __tablename__ = "collection_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("collection_jobs.id"), nullable=False, index=True)
    asset_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    # success, failed, timeout, partial
    result_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # connection, auth, timeout, parse, unknown
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
