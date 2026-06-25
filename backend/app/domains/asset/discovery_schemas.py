"""资产发现 Schemas - 对齐前端字段."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DiscoveryTaskCreate(BaseModel):
    """发现任务创建."""

    name: str = Field(..., description="任务名称")
    ip_mode: str = Field(default="cidr", description="IP模式: cidr | range")
    cidr: str | None = Field(default=None, description="CIDR格式: 10.168.1.0/24")
    ip_start: str | None = Field(default=None, description="起始IP (range模式)")
    ip_end: str | None = Field(default=None, description="结束IP (range模式)")
    protocols: list[str] = Field(default=["icmp"], description="探测协议")
    ports: str | None = Field(default=None, description="端口范围: 22,80,443")
    credential_id: str | None = Field(default=None, description="绑定凭证ID")
    timeout: int = Field(default=30, description="超时秒数")
    # 自动纳管：开启后建任务即自动启动扫描，扫描完成自动纳管全部存活IP
    auto_onboard: bool = Field(default=True, description="自动发现并纳管存活IP")
    # 兼容旧字段
    ip_range: str | None = Field(default=None, description="IP范围(兼容)")
    scan_type: str | None = Field(default="ping", description="扫描类型(兼容)")
    asset_type: str | None = Field(default="linux_server", description="资产类型(兼容)")

    def get_ip_range(self) -> str:
        """获取IP范围字符串."""
        if self.ip_range:
            return self.ip_range
        if self.ip_mode == "cidr" and self.cidr:
            return self.cidr
        if self.ip_mode == "range" and self.ip_start and self.ip_end:
            return f"{self.ip_start}-{self.ip_end}"
        return ""


class DiscoveryResultCreate(BaseModel):
    """发现结果."""

    task_id: str
    ip: str
    hostname: str | None = None
    asset_type: str = "linux_server"
    status: str = "discovered"
    metadata: dict | None = None


class DiscoveryOnboardRequest(BaseModel):
    """发现结果纳管请求."""

    result_ids: list[str] = Field(default=[], description="要纳管的结果ID列表")
    asset_type: str = Field(default="auto", description="资产类型(auto=自动推断)")
