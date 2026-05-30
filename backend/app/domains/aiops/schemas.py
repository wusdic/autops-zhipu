"""AIops Schema."""

from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class AIAnalysisRequest(BaseModel):
    analysis_type: str = Field(..., max_length=32)
    alert_id: str | None = None
    asset_ids: list[str] | None = None


class AIFeedback(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


class AIAnalysisResponse(BaseModel):
    id: str
    analysis_type: str
    alert_id: str | None = None
    asset_ids: str | None = None
    model_name: str
    summary: str | None = None
    root_causes: str | None = None
    recommended_actions: str | None = None
    status: str
    duration_ms: int | None = None
    feedback_rating: int | None = None
    created_at: datetime
