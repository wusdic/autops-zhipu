"""策略模型."""

from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.database import Base


class Policy(Base):
    """策略表."""
    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # event_type, alert_severity, schedule, manual
    trigger_condition: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON: trigger condition expression
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON: asset filter
    action_chain: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON array of action steps
    risk_level: Mapped[str] = mapped_column(String(16), default="low")
    # low, medium, high, critical
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    max_affected_assets: Mapped[int] = mapped_column(Integer, default=10)
    verification_steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON array
    rollback_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON array
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(16), default="draft")
    # draft, active, disabled
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class PolicyExecution(Base):
    """策略执行记录."""
    __tablename__ = "policy_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_id: Mapped[str] = mapped_column(String(36), ForeignKey("policies.id"), nullable=False, index=True)
    policy_version: Mapped[int] = mapped_column(Integer, nullable=False)
    alert_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    trigger_event: Mapped[str | None] = mapped_column(Text, nullable=True)
    matched_assets: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON array of asset IDs
    execution_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    # link to automation execution
    status: Mapped[str] = mapped_column(String(16), default="pending")
    # pending, approved, rejected, executing, completed, failed
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
