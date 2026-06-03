"""发现模板模型."""

from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.database import Base


class DiscoveryTemplate(Base):
    """发现模板表."""
    __tablename__ = "discovery_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    protocol: Mapped[str] = mapped_column(String(32), nullable=False)
    # ssh, snmp, icmp, arp, wmi, agent
    target_scope: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON: {"ip_ranges": [...], "asset_groups": [...], "exclude": [...]}
    port_range: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # e.g. "22,80,443,3389" or "1-1024"
    credential_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    scan_interval: Mapped[int] = mapped_column(Integer, default=3600)
    # 扫描间隔（秒）
    timeout: Mapped[int] = mapped_column(Integer, default=300)
    # 单次超时（秒）
    asset_type_mapping: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON: auto-detected asset type mapping rules
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    # 内置模板不可删除
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
