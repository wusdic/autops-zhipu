"""日志模型."""

from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.database import Base


class ExecutionLog(Base):
    """执行日志表."""
    __tablename__ = "execution_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("executions.id"), nullable=False, index=True)
    step_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    stream_type: Mapped[str] = mapped_column(String(8), nullable=False)
    # stdout, stderr
    content: Mapped[str] = mapped_column(Text, nullable=False)
    offset: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
