"""状态 Schema."""

from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class StateSnapshotCreate(BaseModel):
    asset_id: str
    state_type: str = Field(..., max_length=32)
    status: str = Field(..., max_length=16)
    value: str | None = None
    collected_at: datetime


class StateSnapshotResponse(BaseModel):
    id: str
    asset_id: str
    state_type: str
    status: str
    value: str | None = None
    collected_at: datetime
    created_at: datetime


class StateChangeResponse(BaseModel):
    id: str
    asset_id: str
    state_type: str
    old_status: str
    new_status: str
    old_value: str | None = None
    new_value: str | None = None
    created_at: datetime
