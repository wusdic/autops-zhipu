"""状态模型."""

from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import DateTime, String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.database import Base


class StateSnapshot(Base):
    """状态快照表."""
    __tablename__ = "state_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("assets.id"), nullable=False, index=True)
    state_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # system, disk, cpu, memory, network, service, port, certificate, database, custom
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    # normal, warning, critical, unknown
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON: detailed state data
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class StateChange(Base):
    """状态变更表."""
    __tablename__ = "state_changes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("assets.id"), nullable=False, index=True)
    state_type: Mapped[str] = mapped_column(String(32), nullable=False)
    old_status: Mapped[str] = mapped_column(String(16), nullable=False)
    new_status: Mapped[str] = mapped_column(String(16), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    snapshot_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
