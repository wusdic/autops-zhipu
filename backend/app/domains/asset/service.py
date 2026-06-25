"""资产中心 Service."""

from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import DuplicateError, NotFoundError
from app.domains.asset.models import (
    Asset,
    AssetGroup,
    AssetGroupMember,
    AssetRelation,
    AssetTimeline,
)
from app.domains.asset.repository import (
    AssetGroupRepository,
    AssetRelationRepository,
    AssetRepository,
    AssetTimelineRepository,
)
from app.domains.asset.schemas import (
    AssetCreate,
    AssetGroupCreate,
    AssetImportItem,
    AssetRelationCreate,
    AssetUpdate,
)
from app.domains.collector.query_service import (
    get_collection_jobs_by_asset,
    create_collection_job_for_asset,
)
from app.domains.config.query_service import get_bindings_by_asset
from app.domains.policy.query_service import get_policy_executions_by_asset


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
            asset_id=asset_id,
            event_type="updated",
            title="资产更新",
            detail=f"更新了 {', '.join(updates.keys())}",
            source="manual",
        )
        return asset

    async def delete_asset(self, asset_id: str) -> None:
        await self.repo.soft_delete(asset_id)

    async def import_assets(self, items: list[AssetImportItem]) -> dict:
        """批量导入资产.

        返回 {created, skipped, errors} 明细，而非仅成功的数量，
        让调用方能区分重复跳过与真实失败。
        """
        created: list[Asset] = []
        skipped: list[str] = []
        errors: list[dict] = []
        for idx, item in enumerate(items):
            try:
                asset = await self.create_asset(AssetCreate(**item.model_dump()))
                created.append(asset)
            except DuplicateError:
                skipped.append(item.name or item.ip_address or f"#{idx}")
            except Exception as e:
                errors.append(
                    {
                        "index": idx,
                        "name": item.name or item.ip_address or f"#{idx}",
                        "error": str(e)[:200],
                    }
                )
        return {"created": created, "skipped": skipped, "errors": errors}

    async def add_relation(
        self, asset_id: str, data: AssetRelationCreate
    ) -> AssetRelation:
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
        q = "DELETE FROM asset_group_members WHERE group_id = :gid AND asset_id = :aid"
        from sqlalchemy import text

        await self.session.execute(text(q), {"gid": group_id, "aid": asset_id})
        await self.session.flush()

    async def get_group(self, group_id: str) -> AssetGroup:
        group = await self.group_repo.get_by_id(group_id)
        if not group:
            raise NotFoundError(f"资产分组 {group_id} 不存在")
        return group

    async def get_asset_credentials(self, asset_id: str) -> list[dict]:
        """获取资产关联的凭证列表（通过 config query_service，不直接跨域引用模型）."""
        await self.get_asset(asset_id)
        return await get_bindings_by_asset(asset_id, self.session)

    async def get_asset_policies(self, asset_id: str) -> list[dict]:
        """获取资产关联的策略执行记录（通过 policy query_service，不直接跨域引用模型）."""
        await self.get_asset(asset_id)
        return await get_policy_executions_by_asset(asset_id, self.session)

    async def delete_relation(self, asset_id: str, relation_id: str) -> None:
        """删除资产关系."""
        rel = await self.session.get(AssetRelation, relation_id)
        if not rel:
            raise NotFoundError(f"关系 {relation_id} 不存在")
        await self.session.delete(rel)
        await self.session.flush()

    async def get_collection_configs(self, asset_id: str) -> list[dict]:
        """获取资产采集配置列表（通过 collector query_service，不直接跨域引用模型）."""
        await self.get_asset(asset_id)
        return await get_collection_jobs_by_asset(asset_id, self.session)

    async def trigger_collection(self, asset_id: str) -> dict:
        """触发资产采集 — 创建真实 CollectionJob 并发布 collector.job_created 事件."""
        await self.get_asset(asset_id)
        job_info = await create_collection_job_for_asset(asset_id, self.session)
        return {
            "asset_id": asset_id,
            "job_id": job_info["job_id"],
            "status": job_info["status"],
            "message": "采集任务已创建",
        }

    async def get_topology(self, asset_id: str, depth: int = 2) -> dict:
        """获取资产拓扑关系图（递归查询关联资产）."""
        from sqlalchemy import select

        nodes = {}
        edges = []
        visited = set()

        async def _traverse(aid: str, current_depth: int):
            if current_depth > depth or aid in visited:
                return
            visited.add(aid)

            # 获取资产信息
            asset = await self.session.get(Asset, aid)
            if not asset:
                return
            nodes[aid] = {
                "id": str(asset.id),
                "name": asset.name,
                "type": asset.asset_type,
                "status": asset.status,
                "health": asset.health_status,
                "ip": asset.ip,
            }

            # 获取关联关系
            result = await self.session.execute(
                select(AssetRelation).where(
                    (AssetRelation.source_asset_id == aid)
                    | (AssetRelation.target_asset_id == aid)
                )
            )
            relations = result.scalars().all()
            for rel in relations:
                target_id = str(
                    rel.target_asset_id
                    if str(rel.source_asset_id) == aid
                    else rel.source_asset_id
                )
                edges.append(
                    {
                        "source": str(rel.source_asset_id),
                        "target": str(rel.target_asset_id),
                        "type": rel.relation_type,
                    }
                )
                await _traverse(target_id, current_depth + 1)

        await _traverse(asset_id, 0)
        return {
            "center": asset_id,
            "nodes": list(nodes.values()),
            "edges": edges,
            "depth": depth,
        }
