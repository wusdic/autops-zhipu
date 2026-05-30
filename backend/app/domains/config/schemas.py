"""配置中心 Schema."""

from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class ConfigDefinitionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    config_type: str = Field(..., min_length=1, max_length=32)
    description: str | None = None
    schema_def: str | None = None


class ConfigVersionCreate(BaseModel):
    content: str = Field(..., min_length=1)


class ConfigVersionPublish(BaseModel):
    pass


class ConfigBindingCreate(BaseModel):
    version_id: str
    target_type: str = Field(..., max_length=32)
    target_id: str


class CredentialCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    cred_type: str = Field(..., max_length=32)
    data: str = Field(..., description="""JSON string of credential data""")
    description: str | None = None


class CredentialTest(BaseModel):
    asset_id: str


class ConfigDefinitionResponse(BaseModel):
    id: str
    name: str
    config_type: str
    description: str | None = None
    latest_version: int | None = None
    created_at: datetime
    updated_at: datetime


class ConfigVersionResponse(BaseModel):
    id: str
    definition_id: str
    version: int
    content: str
    status: str
    published_by: str | None = None
    published_at: datetime | None = None
    created_at: datetime


class CredentialResponse(BaseModel):
    id: str
    name: str
    cred_type: str
    description: str | None = None
    test_status: str
    last_tested_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
