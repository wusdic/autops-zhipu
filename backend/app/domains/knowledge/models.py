"""知识库模型."""

from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.database import Base


class KnowledgeArticle(Base):
    """知识文章表."""
    __tablename__ = "knowledge_articles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    article_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # standard_solution, incident_summary, best_practice, draft
    asset_types: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON array
    trigger_events: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON array
    diagnosis_steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON array
    action_steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON array
    verification_steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON array
    risk_level: Mapped[str] = mapped_column(String(16), default="low")
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Markdown content
    status: Mapped[str] = mapped_column(String(16), default="draft")
    # draft, published, archived
    source: Mapped[str] = mapped_column(String(32), default="manual")
    # manual, ticket_closure, ai_generated, import
    source_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON array
    version: Mapped[int] = mapped_column(default=1)
    published_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
