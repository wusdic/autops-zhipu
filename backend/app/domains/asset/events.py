"""资产中心领域事件定义."""
from __future__ import annotations

from app.common.events import (
    DomainEvent,
    EventBus,
    get_event_bus,
    AssetEvents,
)


async def publish_asset_created(asset_id: str, asset_name: str, **kwargs) -> None:
    """发布资产创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AssetEvents.ASSET_CREATED,
        domain="asset",
        payload={"asset_id": asset_id, "asset_name": asset_name, **kwargs},
        source="asset",
    ))


async def publish_asset_updated(asset_id: str, **kwargs) -> None:
    """发布资产更新事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AssetEvents.ASSET_UPDATED,
        domain="asset",
        payload={"asset_id": asset_id, **kwargs},
        source="asset",
    ))


async def publish_asset_deleted(asset_id: str, **kwargs) -> None:
    """发布资产删除事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AssetEvents.ASSET_DELETED,
        domain="asset",
        payload={"asset_id": asset_id, **kwargs},
        source="asset",
    ))


async def publish_asset_status_changed(asset_id: str, old_status: str, new_status: str, **kwargs) -> None:
    """发布资产状态变更事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AssetEvents.ASSET_STATUS_CHANGED,
        domain="asset",
        payload={"asset_id": asset_id, "old_status": old_status, "new_status": new_status, **kwargs},
        source="asset",
    ))


async def publish_asset_health_changed(asset_id: str, old_health: str, new_health: str, **kwargs) -> None:
    """发布资产健康度变更事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AssetEvents.ASSET_HEALTH_CHANGED,
        domain="asset",
        payload={"asset_id": asset_id, "old_health": old_health, "new_health": new_health, **kwargs},
        source="asset",
    ))


async def publish_asset_discovered(asset_id: str, asset_name: str, **kwargs) -> None:
    """发布资产自动发现事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AssetEvents.ASSET_DISCOVERED,
        domain="asset",
        payload={"asset_id": asset_id, "asset_name": asset_name, **kwargs},
        source="asset",
    ))


async def publish_asset_relation_added(asset_id: str, target_id: str, relation_type: str, **kwargs) -> None:
    """发布资产关系添加事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AssetEvents.ASSET_RELATION_ADDED,
        domain="asset",
        payload={"asset_id": asset_id, "target_id": target_id, "relation_type": relation_type, **kwargs},
        source="asset",
    ))


async def publish_asset_relation_removed(asset_id: str, target_id: str, relation_type: str, **kwargs) -> None:
    """发布资产关系移除事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AssetEvents.ASSET_RELATION_REMOVED,
        domain="asset",
        payload={"asset_id": asset_id, "target_id": target_id, "relation_type": relation_type, **kwargs},
        source="asset",
    ))
