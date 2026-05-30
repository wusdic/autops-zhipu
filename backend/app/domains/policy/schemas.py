"""策略 Schema."""

from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class PolicyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    trigger_type: str = Field(..., max_length=32)
    trigger_condition: str = Field(..., description="""JSON trigger expression""")
    scope: str | None = None
    action_chain: str = Field(..., description="""JSON array of action steps""")
    risk_level: str = "low"
    requires_approval: bool = False
    max_affected_assets: int = 10
    verification_steps: str | None = None
    rollback_actions: str | None = None


class PolicySimulate(BaseModel):
    trigger_event: str
    asset_ids: list[str] | None = None


class PolicyResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    trigger_type: str
    trigger_condition: str
    scope: str | None = None
    action_chain: str
    risk_level: str
    requires_approval: bool
    max_affected_assets: int
    verification_steps: str | None = None
    rollback_actions: str | None = None
    version: int
    status: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


class PolicyExecutionResponse(BaseModel):
    id: str
    policy_id: str
    policy_version: int
    alert_id: str | None = None
    trigger_event: str | None = None
    matched_assets: str | None = None
    execution_id: str | None = None
    status: str
    result: str | None = None
    created_at: datetime
