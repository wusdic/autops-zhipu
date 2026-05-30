"""知识 Schema."""

from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class KnowledgeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    article_type: str = Field(..., max_length=32)
    asset_types: str | None = None
    trigger_events: str | None = None
    diagnosis_steps: str | None = None
    action_steps: str | None = None
    verification_steps: str | None = None
    risk_level: str = "low"
    content: str | None = None
    source: str = "manual"
    source_id: str | None = None
    tags: str | None = None


class KnowledgeUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    action_steps: str | None = None
    verification_steps: str | None = None
    tags: str | None = None
    status: str | None = None


class KnowledgeResponse(BaseModel):
    id: str
    title: str
    article_type: str
    asset_types: str | None = None
    trigger_events: str | None = None
    diagnosis_steps: str | None = None
    action_steps: str | None = None
    verification_steps: str | None = None
    risk_level: str
    content: str | None = None
    status: str
    source: str
    source_id: str | None = None
    tags: str | None = None
    version: int
    published_by: str | None = None
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
