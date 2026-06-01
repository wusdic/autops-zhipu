"""自动化执行模型."""

from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.database import Base


class Script(Base):
    """脚本库表."""
    __tablename__ = "scripts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    script_type: Mapped[str] = mapped_column(String(16), nullable=False)
    # shell, python, sql, powershell
    content: Mapped[str] = mapped_column(Text, nullable=False)
    parameters: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON: parameter definitions
    timeout: Mapped[int] = mapped_column(Integer, default=300)
    risk_level: Mapped[str] = mapped_column(String(16), default="low")
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    # high-risk command blacklist
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Playbook(Base):
    """Playbook 表."""
    __tablename__ = "playbooks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    steps: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON array of {script_id, params, timeout, on_failure}
    risk_level: Mapped[str] = mapped_column(String(16), default="low")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Execution(Base):
    """执行任务表."""
    __tablename__ = "executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_type: Mapped[str] = mapped_column(String(16), nullable=False)
    # script, playbook
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)
    # script_id or playbook_id
    asset_ids: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON array
    parameters: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    # pending, dry_running, dry_run_completed, awaiting_approval, approved, running,
    # verifying, completed, failed, cancelled, rolling_back, rolled_back, rollback_failed
    trigger_source: Mapped[str] = mapped_column(String(32), nullable=False)
    # manual, policy, aiops
    trigger_source_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    policy_execution_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    is_dry_run: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_level: Mapped[str] = mapped_column(String(16), default="low")
    approved_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class ExecutionStep(Base):
    """执行步骤表."""
    __tablename__ = "execution_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("executions.id"), nullable=False, index=True)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    script_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    parameters: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    # pending, running, completed, failed, skipped, rolled_back
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
