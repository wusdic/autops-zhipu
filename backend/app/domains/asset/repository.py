"""资产中心 Repository."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.repository import BaseRepository
from app.domains.asset.models import (
    Asset, AssetGroup, AssetRelation, AssetTimeline,
)


class AssetRepository(BaseRepository[Asset]):
    """资产数据访问."""

    def __init__(self, session: AsyncSession):
        super().__init__(Asset, session)

    async def search(
        self, *, page: int = 1, page_size: int = 20,
        asset_type: str | None = None, status: str | None = None,
        health_status: str | None = None, business_system: str | None = None,
        business_system_id: str | None = None,
        environment: str | None = None, search: str | None = None,
    ) -> tuple[list[Asset], int]:
        filters = [Asset.is_deleted == False]  # noqa: E712
        if asset_type:
            filters.append(Asset.asset_type == asset_type)
        if status:
            filters.append(Asset.status == status)
        if health_status:
            filters.append(Asset.health_status == health_status)
        if business_system:
            filters.append(Asset.business_system == business_system)
        if business_system_id:
            filters.append(Asset.business_system_id == business_system_id)
        if environment:
            filters.append(Asset.environment == environment)
        if search:
            filters.append(
                or_(
                    Asset.name.ilike(f"%{search}%"),
                    Asset.ip.ilike(f"%{search}%"),
                    Asset.hostname.ilike(f"%{search}%"),
                )
            )
        return await self.get_multi(
            page=page, page_size=page_size, filters=filters,
            order_by=Asset.created_at.desc(),
        )

    async def get_by_name(self, name: str) -> Asset | None:
        q = select(Asset).where(Asset.name == name, Asset.is_deleted == False)  # noqa: E712
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def get_by_ip(self, ip: str) -> Asset | None:
        q = select(Asset).where(Asset.ip == ip, Asset.is_deleted == False)  # noqa: E712
        result = await self.session.execute(q)
        return result.scalar_one_or_none()


class AssetGroupRepository(BaseRepository[AssetGroup]):
    def __init__(self, session: AsyncSession):
        super().__init__(AssetGroup, session)


class AssetRelationRepository(BaseRepository[AssetRelation]):
    def __init__(self, session: AsyncSession):
        super().__init__(AssetRelation, session)

    async def get_by_asset(self, asset_id: str) -> list[AssetRelation]:
        q = select(AssetRelation).where(
            or_(
                AssetRelation.source_asset_id == asset_id,
                AssetRelation.target_asset_id == asset_id,
            )
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())


class AssetTimelineRepository(BaseRepository[AssetTimeline]):
    def __init__(self, session: AsyncSession):
        super().__init__(AssetTimeline, session)

    async def get_by_asset(self, asset_id: str, limit: int = 50) -> list[AssetTimeline]:
        q = (
            select(AssetTimeline)
            .where(AssetTimeline.asset_id == asset_id)
            .order_by(AssetTimeline.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())
