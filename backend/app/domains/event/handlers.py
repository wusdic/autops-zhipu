"""事件中心领域事件处理器."""
from __future__ import annotations

import logging

from app.common.events import (
    DomainEvent,
    get_event_bus,
    StateEvents,
    AssetEvents,
    EventEvents,
)

logger = logging.getLogger(__name__)


async def on_state_changed_create_event(event: DomainEvent) -> None:
    """状态变更时创建事件记录."""
    payload = event.payload
    try:
        asset_id = payload.get("asset_id")
        old_status = payload.get("old_status", "")
        new_status = payload.get("new_status", "")
        state_type = payload.get("state_type", "")
        if not asset_id:
            logger.debug("event: 状态变更事件缺少asset_id, 跳过事件创建")
            return

        from app.infra.database import async_session_factory
        from app.domains.event.service import EventService

        async with async_session_factory() as session:
            svc = EventService(session)
            await svc.create_event(
                event_type="state_change",
                source="state",
                asset_id=asset_id,
                severity="warning" if new_status != "normal" else "info",
                details={
                    "state_type": state_type,
                    "old_status": old_status,
                    "new_status": new_status,
                    "source_event_id": event.event_id,
                },
            )
            await session.commit()
        logger.info(
            "event: 状态变更创建事件记录 asset_id=%s %s->%s",
            asset_id, old_status, new_status,
        )
    except Exception as e:
        logger.error("event: 状态变更创建事件记录失败: %s", e)


async def on_state_critical_create_event(event: DomainEvent) -> None:
    """状态变critical时创建高优先级事件."""
    payload = event.payload
    try:
        asset_id = payload.get("asset_id")
        if not asset_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.event.service import EventService

        async with async_session_factory() as session:
            svc = EventService(session)
            await svc.create_event(
                event_type="threshold_exceeded",
                source="state",
                asset_id=asset_id,
                severity="critical",
                details={
                    "state_type": payload.get("state_type", ""),
                    "status": payload.get("status", ""),
                    "source_event_id": event.event_id,
                },
            )
            await session.commit()
        logger.info("event: 状态critical创建高优先级事件 asset_id=%s", asset_id)
    except Exception as e:
        logger.error("event: 状态critical创建事件失败: %s", e)


async def on_asset_changed_create_event(event: DomainEvent) -> None:
    """资产变更时创建事件记录."""
    payload = event.payload
    try:
        asset_id = payload.get("asset_id")
        if not asset_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.event.service import EventService

        async with async_session_factory() as session:
            svc = EventService(session)
            # 映射资产事件类型到内部事件类型
            event_type_map = {
                AssetEvents.ASSET_CREATED: "asset_created",
                AssetEvents.ASSET_UPDATED: "asset_updated",
                AssetEvents.ASSET_DELETED: "asset_deleted",
                AssetEvents.ASSET_STATUS_CHANGED: "asset_status_changed",
                AssetEvents.ASSET_HEALTH_CHANGED: "asset_health_changed",
                AssetEvents.ASSET_DISCOVERED: "asset_discovered",
            }
            internal_type = event_type_map.get(event.event_type, "asset_change")
            await svc.create_event(
                event_type=internal_type,
                source="asset",
                asset_id=asset_id,
                severity="info",
                details={
                    "original_event_type": event.event_type,
                    "payload": payload,
                    "source_event_id": event.event_id,
                },
            )
            await session.commit()
        logger.info("event: 资产变更创建事件 asset_id=%s type=%s", asset_id, event.event_type)
    except Exception as e:
        logger.error("event: 资产变更创建事件失败: %s", e)


async def on_state_recovered_create_event(event: DomainEvent) -> None:
    """状态恢复 → 创建恢复事件（用于自动resolved告警）."""
    payload = event.payload
    try:
        asset_id = payload.get("asset_id")
        if not asset_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.event.service import EventService
        import json

        async with async_session_factory() as session:
            svc = EventService(session)
            await svc.create_event(
                event_type="state_recovered",
                source="state",
                asset_id=asset_id,
                severity="info",
                details={
                    "state_type": payload.get("state_type", ""),
                    "old_status": payload.get("old_status", ""),
                    "new_status": "normal",
                    "source_event_id": event.event_id,
                },
            )
            await session.commit()
        logger.info("event: 状态恢复创建事件 asset_id=%s", asset_id)
    except Exception as e:
        logger.error("event: 状态恢复创建事件失败: %s", e)


def register_handlers() -> None:
    """注册事件领域的事件处理器."""
    bus = get_event_bus()
    bus.subscribe(StateEvents.STATE_CHANGED, on_state_changed_create_event)
    bus.subscribe(StateEvents.STATE_CRITICAL, on_state_critical_create_event)
    bus.subscribe(StateEvents.STATE_RECOVERED, on_state_recovered_create_event)
    bus.subscribe(AssetEvents.ASSET_CREATED, on_asset_changed_create_event)
    bus.subscribe(AssetEvents.ASSET_UPDATED, on_asset_changed_create_event)
    bus.subscribe(AssetEvents.ASSET_DELETED, on_asset_changed_create_event)
    bus.subscribe(AssetEvents.ASSET_STATUS_CHANGED, on_asset_changed_create_event)
    bus.subscribe(AssetEvents.ASSET_HEALTH_CHANGED, on_asset_changed_create_event)
    logger.info("event领域事件处理器已注册 (4个handler, 监听8个事件)")
