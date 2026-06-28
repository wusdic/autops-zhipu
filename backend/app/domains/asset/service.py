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

    async def refresh_status_from_snapshots(self, asset_id: str) -> Asset | None:
        """根据最新 state_snapshots 推算资产 health_status/reachability/status（R7）.

        - ping 快照 normal→reachable / critical→unreachable
        - 健康度：任一 critical→critical；全 normal→healthy；无快照→unknown；其余 warning
        - status（生命周期）：业务系统保持 active；普通资产 reachable→active / 不可达→maintenance
        """
        from sqlalchemy import select as _select

        from app.domains.state.models import StateSnapshot

        asset = await self.repo.get_by_id(asset_id)
        if not asset:
            return None

        rows = (
            (
                await self.session.execute(
                    _select(StateSnapshot)
                    .where(StateSnapshot.asset_id == asset_id)
                    .order_by(StateSnapshot.collected_at.desc())
                    .limit(50)
                )
            )
            .scalars()
            .all()
        )
        # 取每个 state_type 的最新一条
        latest: dict[str, str] = {}
        for s in rows:
            latest.setdefault(s.state_type, s.status)
        if not latest:
            return asset  # 无快照，不动

        statuses = list(latest.values())
        if any(v == "critical" for v in statuses):
            health = "critical"
        elif all(v == "normal" for v in statuses):
            health = "healthy"
        elif any(v in ("warning", "degraded") for v in statuses):
            health = "warning"
        else:
            health = "unknown"

        ping = latest.get("ping")
        if ping == "normal":
            reachability = "reachable"
        elif ping == "critical":
            reachability = "unreachable"
        else:
            reachability = asset.reachability or "unknown"

        asset.health_status = health
        asset.reachability = reachability
        if asset.asset_type != "business_system":
            asset.status = "active" if reachability == "reachable" else "maintenance"
        await self.session.flush()
        return asset

    async def refresh_all_statuses(self) -> int:
        """批量从快照刷新所有未删除资产状态，返回处理数量."""
        from sqlalchemy import select as _select

        ids = (
            (
                await self.session.execute(
                    _select(Asset.id).where(Asset.is_deleted == False)  # noqa: E712
                )
            )
            .scalars()
            .all()
        )
        for aid in ids:
            await self.refresh_status_from_snapshots(str(aid))
        return len(ids)

    async def _resolve_business_system(
        self, bs_id: str | None, bs_name: str | None
    ) -> tuple[str | None, str | None]:
        """解析业务系统归属，返回 (business_system_id, business_system 名缓存)。

        - 优先用 id：校验其为有效业务系统资产，返回 (id, name)；无效则清空 (None, None)。
        - 否则用名：能匹配到业务系统资产则返回 (id, name)，匹配不到则保留名、id 空（兼容自由文本）。
        """
        from sqlalchemy import select as _select

        if bs_id:
            row = (
                await self.session.execute(
                    _select(Asset.id, Asset.name).where(
                        Asset.id == bs_id,
                        Asset.asset_type == "business_system",
                        Asset.is_deleted == False,  # noqa: E712
                    )
                )
            ).first()
            return (row[0], row[1]) if row else (None, None)
        if bs_name:
            row = (
                await self.session.execute(
                    _select(Asset.id, Asset.name).where(
                        Asset.name == bs_name,
                        Asset.asset_type == "business_system",
                        Asset.is_deleted == False,  # noqa: E712
                    )
                )
            ).first()
            return (row[0], row[1]) if row else (None, bs_name)
        return None, None

    async def assign_business_system(
        self, asset_id: str, business_system_id: str | None
    ) -> Asset:
        """把资产归属到某业务系统（或传 None 解除归属），同步写 id + 名缓存。"""
        asset = await self.get_asset(asset_id)
        bs_id, bs_name = await self._resolve_business_system(business_system_id, None)
        asset.business_system_id = bs_id
        asset.business_system = bs_name
        await self.session.flush()
        await self.timeline_repo.create(
            asset_id=asset_id,
            event_type="updated",
            title="业务系统归属变更",
            detail=f"归属业务系统: {bs_name or '（已解除）'}",
            source="manual",
        )
        return asset

    async def list_business_members(
        self, business_system_id: str, page: int = 1, page_size: int = 20
    ):
        """列出某业务系统下的成员资产（按 business_system_id 事实源）。"""
        from sqlalchemy import select as _select, func as _func

        base = _select(Asset).where(
            Asset.business_system_id == business_system_id,
            Asset.asset_type != "business_system",
            Asset.is_deleted == False,  # noqa: E712
        )
        total = (
            await self.session.execute(
                _select(_func.count()).select_from(base.subquery())
            )
        ).scalar() or 0
        rows = (
            (
                await self.session.execute(
                    base.order_by(Asset.created_at.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )
        return rows, total

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
        # 解析业务系统归属（id 优先，回退按名），同步写 id + 名缓存
        bs_id, bs_name = await self._resolve_business_system(
            data.business_system_id, data.business_system
        )
        asset = await self.repo.create(
            name=data.name,
            asset_type=data.asset_type,
            ip=data.ip,
            port=data.port,
            hostname=data.hostname,
            os_type=data.os_type,
            os_version=data.os_version,
            description=data.description,
            business_system=bs_name,
            business_system_id=bs_id,
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
        await self.session.flush()

        # 发布 ASSET_CREATED（与业务数据同事务），驱动 worker 立即采集等下游链路。
        from app.common.events import AssetEvents, DomainEvent, get_event_bus

        await get_event_bus().publish(
            DomainEvent(
                domain="asset",
                event_type=AssetEvents.ASSET_CREATED,
                payload={
                    "asset_id": str(asset.id),
                    "asset_name": asset.hostname or asset.name,
                    "asset_type": asset.asset_type,
                    "ip": asset.ip,
                },
                source="asset_service",
            ),
            session=self.session,
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

        # 业务系统归属：从 setattr 流程里摘出，统一经解析写 id + 名缓存
        if "business_system_id" in updates or "business_system" in updates:
            bs_id, bs_name = await self._resolve_business_system(
                updates.pop("business_system_id", None),
                updates.pop("business_system", None),
            )
            asset.business_system_id = bs_id
            asset.business_system = bs_name

        for key, value in updates.items():
            setattr(asset, key, value)
        await self.session.flush()

        # 业务系统自身改名 → 传播到成员资产的名缓存（事实源是 id，不受影响，仅同步展示）
        if asset.asset_type == "business_system" and "name" in updates:
            from sqlalchemy import update as _update

            await self.session.execute(
                _update(Asset)
                .where(Asset.business_system_id == asset.id)
                .values(business_system=asset.name)
            )
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
