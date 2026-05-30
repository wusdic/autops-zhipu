"""Log domain schemas."""
from pydantic import BaseModel, Field
from datetime import datetime


class ExecutionLogResponse(BaseModel):
    """执行日志响应."""
    id: str
    execution_id: str
    step_name: str | None = None
    level: str = "info"
    message: str = ""
    output: str | None = None
    timestamp: datetime | None = None

    class Config:
        from_attributes = True


class ExecutionLogCreate(BaseModel):
    """创建执行日志."""
    execution_id: str = Field(..., min_length=1)
    step_name: str | None = None
    level: str = Field(default="info", max_length=16)
    message: str = Field(default="")
    output: str | None = None
