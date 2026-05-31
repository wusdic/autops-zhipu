"""资产中心 Service."""

from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import DuplicateError, NotFoundError
from app.domains.asset.models import (
    Asset, AssetGroup, AssetGroupMember, AssetRelation, AssetTimeline,
)
from app.domains.asset.repository import (
    AssetGroupRepository, AssetRelationRepository, AssetRepository,
    AssetTimelineRepository,
)
from app.domains.asset.schemas import (
    AssetCreate, AssetGroupCreate, AssetImportItem, AssetRelationCreate, AssetUpdate,
)


class AssetService:
    """资产业务逻辑."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AssetRepository(session)
        self.group_repo = AssetGroupRepository(session)
        self.relation_repo = AssetRelationRepository(session)
        self.timeline_repo = AssetTimelineRepository(session)

    async def create_asset(self, data: AssetCreate) -> Asset:
        """创建资产."""
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise DuplicateError(f"资产 '{data.name}' 已存在")
        if data.ip:
            existing_ip = await self.repo.get_by_ip(data.ip)
            if existing_ip:
                raise DuplicateError(f"IP '{data.ip}' 已被占用")

        tags_json = json.dumps(data.tags) if data.tags else None
        asset = await self.repo.create(
            name=data.name,
            asset_type=data.asset_type,
            ip=data.ip,
            port=data.port,
            hostname=data.hostname,
            os_type=data.os_type,
            os_version=data.os_version,
            description=data.description,
            business_system=data.business_system,
            environment=data.environment,
            location=data.location,
            tags=tags_json,
        )

        # 写时间线
        await self.timeline_repo.create(
            asset_id=asset.id,
            event_type="created",
            title="资产创建",
            detail=f"资产 {data.name} ({data.asset_type}) 已创建",
            source="manual",
        )
        # Refresh to load server_default fields
        await self.session.refresh(asset)
        return asset

    async def get_asset(self, asset_id: str) -> Asset:
        return await self.repo.get_by_id_or_raise(asset_id)

    async def list_assets(self, **kwargs) -> tuple[list[Asset], int]:
        return await self.repo.search(**kwargs)

    async def update_asset(self, asset_id: str, data: AssetUpdate) -> Asset:
        asset = await self.get_asset(asset_id)
        updates = data.model_dump(exclude_unset=True, exclude_none=True)
        if "tags" in updates and isinstance(updates["tags"], list):
            updates["tags"] = json.dumps(updates["tags"])
        for key, value in updates.items():
            setattr(asset, key, value)
        await self.session.flush()
        await self.session.refresh(asset)

        await self.timeline_repo.create(
            asset_id=asset_id, event_type="updated",
            title="资产更新", detail=f"更新了 {', '.join(updates.keys())}",
            source="manual",
        )
        return asset

    async def delete_asset(self, asset_id: str) -> None:
        await self.repo.soft_delete(asset_id)

    async def import_assets(self, items: list[AssetImportItem]) -> list[Asset]:
        """批量导入资产."""
        created = []
        for item in items:
            try:
                asset = await self.create_asset(AssetCreate(**item.model_dump()))
                created.append(asset)
            except DuplicateError:
                continue
        return created

    async def add_relation(self, asset_id: str, data: AssetRelationCreate) -> AssetRelation:
        await self.get_asset(asset_id)
        await self.get_asset(data.target_asset_id)
        return await self.relation_repo.create(
            source_asset_id=asset_id,
            target_asset_id=data.target_asset_id,
            relation_type=data.relation_type,
            description=data.description,
        )

    async def get_relations(self, asset_id: str) -> list[AssetRelation]:
        await self.get_asset(asset_id)
        return await self.relation_repo.get_by_asset(asset_id)

    async def get_timeline(self, asset_id: str, limit: int = 50) -> list[AssetTimeline]:
        await self.get_asset(asset_id)
        return await self.timeline_repo.get_by_asset(asset_id, limit)

    # --- 分组 ---
    async def create_group(self, data: AssetGroupCreate) -> AssetGroup:
        return await self.group_repo.create(**data.model_dump())

    async def list_groups(self, **kwargs) -> tuple[list[AssetGroup], int]:
        return await self.group_repo.get_multi(**kwargs)

    async def add_group_member(self, group_id: str, asset_id: str) -> None:
        group = await self.group_repo.get_by_id_or_raise(group_id)
        await self.get_asset(asset_id)
        self.session.add(AssetGroupMember(group_id=group_id, asset_id=asset_id))
        await self.session.flush()

    async def remove_group_member(self, group_id: str, asset_id: str) -> None:
        q = (
            "DELETE FROM asset_group_members WHERE group_id = :gid AND asset_id = :aid"
        )
        from sqlalchemy import text
        await self.session.execute(text(q), {"gid": group_id, "aid": asset_id})
        await self.session.flush()

    async def get_group(self, group_id: str) -> AssetGroup:
        group = await self.group_repo.get_by_id(group_id)
        if not group:
            raise NotFoundError(f"资产分组 {group_id} 不存在")
        return group

    async def get_asset_credentials(self, asset_id: str) -> list:
        """获取资产关联的凭证列表."""
        await self.get_asset(asset_id)
        from sqlalchemy import select
        from app.domains.config.models import CredentialBinding
        stmt = select(CredentialBinding).where(CredentialBinding.target_id == asset_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_asset_policies(self, asset_id: str) -> list:
        """获取资产关联的策略执行记录."""
        await self.get_asset(asset_id)
        from sqlalchemy import select
        from app.domains.policy.models import PolicyExecution
        from sqlalchemy import func as sa_func
        stmt = select(PolicyExecution).where(
            PolicyExecution.matched_assets.contains(asset_id)
        ).order_by(PolicyExecution.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_relation(self, asset_id: str, relation_id: str) -> None:
        """删除资产关系."""
        rel = await self.session.get(AssetRelation, relation_id)
        if not rel:
            raise NotFoundError(f"关系 {relation_id} 不存在")
        await self.session.delete(rel)
        await self.session.flush()

    async def get_collection_configs(self, asset_id: str) -> list:
        """获取资产采集配置列表."""
        await self.get_asset(asset_id)
        from sqlalchemy import select
        from app.domains.collector.models import CollectionJob
        stmt = select(CollectionJob).where(CollectionJob.asset_id == asset_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def trigger_collection(self, asset_id: str) -> dict:
        """触发资产采集."""
        await self.get_asset(asset_id)
        return {"asset_id": asset_id, "status": "triggered", "message": "采集任务已触发"}
