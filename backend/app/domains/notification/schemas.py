"""通知 Schema."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    message: str | None = None
    link: str | None = None
    ref_id: str | None = None
    read_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationReadPatch(BaseModel):
    read: bool = True
