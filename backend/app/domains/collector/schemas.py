"""采集器 Schema."""

from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class CollectorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    collector_type: str = Field(..., max_length=32)
    description: str | None = None
    config_schema: str | None = None


class CollectionJobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    collector_id: str
    asset_id: str
    config_version_id: str | None = None
    credential_id: str | None = None
    schedule: str = "manual"
    timeout: int = 300


class CollectionResultResponse(BaseModel):
    id: str
    job_id: str
    asset_id: str
    status: str
    result_data: str | None = None
    error_message: str | None = None
    error_category: str | None = None
    duration_ms: int | None = None
    started_at: datetime
    completed_at: datetime | None = None


class CollectorResponse(BaseModel):
    id: str
    name: str
    collector_type: str
    description: str | None = None
    is_builtin: bool
    created_at: datetime


class CollectionJobResponse(BaseModel):
    id: str
    name: str
    collector_id: str
    asset_id: str
    schedule: str
    status: str
    timeout: int
    last_run_at: datetime | None = None
    created_at: datetime
