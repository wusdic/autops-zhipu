"""异常检测 Schema."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AnomalyCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    description: str | None = None
    source: str = Field(..., min_length=1, max_length=128)
    severity: str = Field("medium", description="low|medium|high|critical")
    status: str = Field("open", description="open|acknowledged|resolved|closed")
    asset_id: str | None = None
    assigned_to: str | None = None
    detected_at: datetime | None = None
    meta: dict[str, Any] | None = Field(default=None, alias="metadata")


class AnomalyUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    source: str | None = None
    severity: str | None = None
    status: str | None = None
    asset_id: str | None = None
    assigned_to: str | None = None
    resolved_at: datetime | None = None
    meta: dict[str, Any] | None = Field(default=None, alias="metadata")


class AnomalyResponse(BaseModel):
    id: str
    title: str
    description: str | None = None
    source: str
    severity: str
    status: str
    asset_id: str | None = None
    assigned_to: str | None = None
    detected_at: datetime
    resolved_at: datetime | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class AssignBody(BaseModel):
    assignee_id: str = Field(..., min_length=1)


class EscalateBody(BaseModel):
    target_severity: str | None = Field(
        None, description="Severity to escalate to (default: next level)"
    )
    reason: str | None = None


class ConvertTicketBody(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
