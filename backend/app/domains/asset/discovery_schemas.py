"""资产发现 Schemas."""
from pydantic import BaseModel


class DiscoveryTaskCreate(BaseModel):
    """发现任务创建."""
    ip_range: str
    scan_type: str = "ping"
    asset_type: str = "linux_server"
    credential_id: str | None = None


class DiscoveryResultCreate(BaseModel):
    """发现结果."""
    task_id: str
    ip: str
    hostname: str | None = None
    asset_type: str = "linux_server"
    status: str = "discovered"
    metadata: dict | None = None
