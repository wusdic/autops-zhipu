"""事件 Schema."""

from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    event_type: str = Field(..., max_length=32)
    source: str = Field(..., max_length=32)
    source_id: str | None = None
    asset_id: str | None = None
    title: str = Field(..., min_length=1, max_length=256)
    detail: str | None = None
    raw_data: str | None = None
    severity: str = "info"


class EventResponse(BaseModel):
    id: str
    event_type: str
    source: str
    source_id: str | None = None
    asset_id: str | None = None
    title: str
    detail: str | None = None
    severity: str
    fingerprint: str | None = None
    is_deduplicated: bool
    created_at: datetime
