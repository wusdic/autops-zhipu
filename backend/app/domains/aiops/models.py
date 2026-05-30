"""AIops 模型."""

from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.database import Base


class AIAnalysis(Base):
    """AI 分析记录表."""
    __tablename__ = "ai_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # root_cause, remediation, log_interpretation, anomaly_detection
    alert_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    asset_ids: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON array
    input_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON: full context fed to AI
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_causes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON array of {cause, confidence}
    recommended_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON array
    raw_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    # pending, running, completed, failed, degraded
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 1-5
    feedback_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
