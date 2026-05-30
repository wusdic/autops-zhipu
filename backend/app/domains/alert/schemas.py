"""告警 Schema."""

from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class AlertRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    event_types: str = Field(..., description="""JSON array""")
    conditions: str = Field(..., description="""JSON condition expression""")
    severity: str = "warning"
    suppress_duration: int = 0
    enabled: bool = True


class AlertCreateBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    severity: str = Field(..., max_length=16)
    context: str | None = None
    asset_ids: str | None = None
    event_ids: str | None = None
    rule_id: str | None = None


class AlertAcknowledge(BaseModel):
    pass


class AlertResponse(BaseModel):
    id: str
    title: str
    severity: str
    status: str
    rule_id: str | None = None
    event_ids: str | None = None
    asset_ids: str | None = None
    context: str | None = None
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    ticket_id: str | None = None
    created_at: datetime
    updated_at: datetime


class AlertRuleResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    event_types: str
    conditions: str
    severity: str
    suppress_duration: int
    enabled: bool
    created_at: datetime
