"""巡检域 Pydantic Schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# --- InspectionTemplate ---
class InspectionTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    check_items: list[Any] | None = None


class InspectionTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    check_items: list[Any] | None = None


class InspectionTemplateResponse(BaseModel):
    id: str
    name: str
    description: str | None
    check_items: list[Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- InspectionPlan ---
class InspectionPlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    template_id: str
    cron_expression: str
    target_assets: list[str] | None = None
    enabled: bool = True


class InspectionPlanUpdate(BaseModel):
    name: str | None = None
    template_id: str | None = None
    cron_expression: str | None = None
    target_assets: list[str] | None = None
    enabled: bool | None = None


class InspectionPlanResponse(BaseModel):
    id: str
    name: str
    template_id: str
    cron_expression: str
    target_assets: list[str] | None
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- InspectionTask ---
class InspectionTaskCreate(BaseModel):
    template_id: str
    plan_id: str | None = None


class InspectionTaskResponse(BaseModel):
    id: str
    plan_id: str | None
    template_id: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    summary: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- InspectionResult ---
class InspectionResultResponse(BaseModel):
    id: str
    task_id: str
    asset_id: str
    check_item: str
    status: str
    detail: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- InspectionReport ---
class InspectionReportResponse(BaseModel):
    id: str
    task_id: str
    report_data: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
