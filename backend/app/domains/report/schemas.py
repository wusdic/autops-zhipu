"""报告 Schema."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, Field


# ---- Report Template ----

class ReportTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    description: str | None = None
    type: str = Field("custom", pattern="^(daily|weekly|monthly|custom)$")
    config: dict[str, Any] | None = None


class ReportTemplateUpdate(BaseModel):
    name: str | None = Field(None, max_length=256)
    description: str | None = None
    type: str | None = Field(None, pattern="^(daily|weekly|monthly|custom)$")
    config: dict[str, Any] | None = None


class ReportTemplateResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    type: str
    config: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


# ---- Report Task ----

class ReportGenerateRequest(BaseModel):
    # template_id 可选：未提供时按 report_type 自动查找/创建模板
    template_id: str | None = None
    report_type: str | None = Field(
        default=None, validation_alias=AliasChoices("report_type", "type")
    )
    params: dict[str, Any] | None = None
    triggered_by: str | None = None

    model_config = {"populate_by_name": True}


class ReportTaskResponse(BaseModel):
    id: str
    template_id: str
    status: str
    triggered_by: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result_path: str | None = None
    created_at: datetime


# ---- Report Archive ----

class ReportArchiveResponse(BaseModel):
    id: str
    task_id: str
    filename: str
    file_size: int
    storage_path: str
    created_at: datetime
