"""工单 Schema."""

from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    ticket_type: str = Field(..., max_length=32)
    priority: str = "medium"
    description: str | None = None
    context: dict | None = None
    alert_ids: list[str] | None = None
    execution_ids: str | None = None
    assigned_to: str | None = None


class TicketUpdate(BaseModel):
    title: str | None = None
    priority: str | None = None
    status: str | None = None
    assigned_to: str | None = None
    description: str | None = None


class TicketCommentCreate(BaseModel):
    content: str = Field(..., min_length=1)


class TicketResponse(BaseModel):
    id: str
    title: str
    ticket_type: str
    status: str
    priority: str
    description: str | None = None
    context: str | None = None
    alert_ids: str | None = None
    execution_ids: str | None = None
    assigned_to: str | None = None
    created_by: str | None = None
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    closed_by: str | None = None
    closed_at: datetime | None = None
    sla_deadline: datetime | None = None
    created_at: datetime
    updated_at: datetime
