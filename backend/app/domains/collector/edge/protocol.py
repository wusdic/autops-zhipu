"""Edge Collector 通信协议定义."""
from __future__ import annotations
from enum import Enum
from pydantic import BaseModel

class MessageType(str, Enum):
    HEARTBEAT = "heartbeat"
    TASK = "task"
    RESULT = "result"
    REGISTER = "register"
    CONFIG_UPDATE = "config_update"

class HeartbeatPayload(BaseModel):
    collector_id: str
    status: str = "healthy"
    cpu_usage: float | None = None
    memory_usage: float | None = None
    active_tasks: int = 0
    timestamp: str | None = None

class TaskPayload(BaseModel):
    task_id: str
    collector_type: str
    config: dict
    timeout: int = 300

class ResultPayload(BaseModel):
    task_id: str
    status: str  # success, failed, timeout
    data: dict | None = None
    error_message: str | None = None
    duration_ms: int | None = None

class RegisterPayload(BaseModel):
    collector_id: str | None = None
    name: str
    collector_type: str
    hostname: str
    capabilities: list[str] = []
