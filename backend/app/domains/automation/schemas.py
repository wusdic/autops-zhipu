"""自动化 Schema."""

from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class ScriptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    script_type: str = Field(..., max_length=16)
    content: str = Field(..., min_length=1)
    parameters: str | None = None
    timeout: int = 300
    risk_level: str = "low"


class ScriptUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    script_type: str | None = None
    content: str | None = None
    parameters: str | None = None
    timeout: int | None = None
    risk_level: str | None = None


class PlaybookCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    steps: str = Field(..., description="""JSON array of steps""")
    risk_level: str = "low"


class PlaybookUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    steps: str | None = None
    risk_level: str | None = None


class ExecutionCreate(BaseModel):
    execution_type: str = Field(..., max_length=16)
    target_id: str
    asset_ids: list[str] = Field(default_factory=list)
    parameters: str | None = None
    is_dry_run: bool = False
    trigger_source: str = "manual"
    trigger_source_id: str | None = None


class ExecutionApprove(BaseModel):
    pass


class ExecutionCancel(BaseModel):
    reason: str | None = None


class ScriptResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    script_type: str
    parameters: str | None = None
    timeout: int
    risk_level: str
    is_blocked: bool
    version: int
    created_at: datetime
    updated_at: datetime


class PlaybookResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    steps: str
    risk_level: str
    version: int
    created_at: datetime
    updated_at: datetime


class ExecutionResponse(BaseModel):
    id: str
    execution_type: str
    target_id: str
    asset_ids: str
    parameters: str | None = None
    status: str
    trigger_source: str
    trigger_source_id: str | None = None
    policy_execution_id: str | None = None
    is_dry_run: bool
    risk_level: str
    approved_by: str | None = None
    approved_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
