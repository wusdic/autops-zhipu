"""资产中心 Pydantic Schema."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# --- Asset ---
class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    asset_type: str = Field(..., min_length=1, max_length=32)
    ip: str | None = None
    port: int | None = None
    hostname: str | None = None
    os_type: str | None = None
    os_version: str | None = None
    description: str | None = None
    business_system: str | None = None
    environment: str | None = None
    location: str | None = None
    tags: list[str] | None = None


class AssetUpdate(BaseModel):
    name: str | None = None
    ip: str | None = None
    port: int | None = None
    hostname: str | None = None
    os_type: str | None = None
    os_version: str | None = None
    description: str | None = None
    business_system: str | None = None
    environment: str | None = None
    location: str | None = None
    status: str | None = None
    tags: list[str] | None = None


class AssetResponse(BaseModel):
    id: str
    name: str
    asset_type: str
    ip: str | None
    port: int | None
    hostname: str | None
    os_type: str | None
    os_version: str | None
    description: str | None
    business_system: str | None
    environment: str | None
    location: str | None
    status: str
    health_status: str
    reachability: str
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetListQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    asset_type: str | None = None
    status: str | None = None
    health_status: str | None = None
    business_system: str | None = None
    environment: str | None = None
    search: str | None = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


# --- Asset Group ---
class AssetGroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    parent_id: str | None = None


class AssetGroupResponse(BaseModel):
    id: str
    name: str
    description: str | None
    parent_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Asset Relation ---
class AssetRelationCreate(BaseModel):
    target_asset_id: str
    relation_type: str
    description: str | None = None


class AssetRelationResponse(BaseModel):
    id: str
    source_asset_id: str
    target_asset_id: str
    relation_type: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Asset Timeline ---
class AssetTimelineResponse(BaseModel):
    id: str
    asset_id: str
    event_type: str
    title: str
    detail: str | None
    source: str
    source_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Asset Import ---
class AssetImportItem(BaseModel):
    name: str
    asset_type: str
    ip: str | None = None
    port: int | None = None
    hostname: str | None = None
    os_type: str | None = None
    business_system: str | None = None
    environment: str | None = None
