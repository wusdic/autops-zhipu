"""巡检域数据模型."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON, Boolean, DateTime, ForeignKey, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.database import Base


class InspectionTemplate(Base):
    """巡检模板."""

    __tablename__ = "inspection_templates"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    check_items: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class InspectionPlan(Base):
    """巡检计划."""

    __tablename__ = "inspection_plans"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    template_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("inspection_templates.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    cron_expression: Mapped[str] = mapped_column(String(128), nullable=False)
    target_assets: Mapped[list | None] = mapped_column(JSON, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class InspectionTask(Base):
    """巡检任务."""

    __tablename__ = "inspection_tasks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    plan_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("inspection_plans.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    template_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("inspection_templates.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    status: Mapped[str] = mapped_column(
        String(16), default="pending", nullable=False, index=True,
    )  # pending, running, completed, failed
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class InspectionResult(Base):
    """巡检结果."""

    __tablename__ = "inspection_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("inspection_tasks.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    asset_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    check_item: Mapped[str] = mapped_column(String(256), nullable=False)
    # 巡检分类：baseline / resource / service / config / security / log / page
    check_type: Mapped[str] = mapped_column(
        String(32), default="baseline", nullable=False, index=True,
    )
    status: Mapped[str] = mapped_column(
        String(16), default="pass", nullable=False, index=True,
    )  # pass, fail, warning
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class InspectionRule(Base):
    """巡检规则（页面/配置/日志/基线/API 检查规则）.

    可单独管理，并可被巡检执行器按 asset_type + 可解析的条件转化为检查项。
    """

    __tablename__ = "inspection_rules"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    check_target: Mapped[str | None] = mapped_column(String(256), nullable=True)
    condition: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    asset_types: Mapped[list | None] = mapped_column(JSON, nullable=True)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class InspectionReport(Base):
    """巡检报告."""

    __tablename__ = "inspection_reports"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("inspection_tasks.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    report_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
