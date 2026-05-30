"""资产中心数据模型."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.database import Base


class Asset(Base):
    """资产表."""

    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )  # linux_server, windows_server, database, web_service, network_device
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True, index=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hostname: Mapped[str | None] = mapped_column(String(128), nullable=True)
    os_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    os_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_system: Mapped[str | None] = mapped_column(String(64), nullable=True)
    environment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    location: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), default="active", nullable=False, index=True
    )  # active, inactive, maintenance, decommissioned
    health_status: Mapped[str] = mapped_column(
        String(16), default="unknown", nullable=False
    )  # healthy, warning, critical, unknown
    reachability: Mapped[str] = mapped_column(
        String(16), default="unknown", nullable=False
    )  # reachable, unreachable, unknown
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # 关系
    ips: Mapped[list["AssetIP"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )
    relations_as_source: Mapped[list["AssetRelation"]] = relationship(
        foreign_keys="AssetRelation.source_asset_id",
        back_populates="source_asset",
        cascade="all, delete-orphan",
    )
    relations_as_target: Mapped[list["AssetRelation"]] = relationship(
        foreign_keys="AssetRelation.target_asset_id",
        back_populates="target_asset",
        cascade="all, delete-orphan",
    )


class AssetIP(Base):
    """资产 IP 表（一个资产可以有多个 IP）."""

    __tablename__ = "asset_ips"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ip: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    ip_type: Mapped[str] = mapped_column(
        String(16), default="ipv4", nullable=False
    )  # ipv4, ipv6
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    interface: Mapped[str | None] = mapped_column(String(32), nullable=True)

    asset: Mapped["Asset"] = relationship(back_populates="ips")


class AssetGroup(Base):
    """资产分组."""

    __tablename__ = "asset_groups"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("asset_groups.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    members: Mapped[list["AssetGroupMember"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )


class AssetGroupMember(Base):
    """资产分组成员."""

    __tablename__ = "asset_group_members"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    group_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("asset_groups.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    group: Mapped["AssetGroup"] = relationship(back_populates="members")


class AssetRelation(Base):
    """资产关系."""

    __tablename__ = "asset_relations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    source_asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    target_asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # depends_on, runs_on, connects_to, contains, member_of
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    source_asset: Mapped["Asset"] = relationship(
        foreign_keys=[source_asset_id], back_populates="relations_as_source"
    )
    target_asset: Mapped["Asset"] = relationship(
        foreign_keys=[target_asset_id], back_populates="relations_as_target"
    )


class AssetTimeline(Base):
    """资产时间线事件."""

    __tablename__ = "asset_timeline"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    # manual, collector, alert, automation, system
    source_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )
