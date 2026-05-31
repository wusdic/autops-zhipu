"""资产中心领域事件处理器."""
from __future__ import annotations

import logging

from app.common.events import (
    DomainEvent,
    get_event_bus,
    AlertEvents,
    AutomationEvents,
)

logger = logging.getLogger(__name__)


async def on_alert_created_update_health(event: DomainEvent) -> None:
    """告警创建时更新资产健康状态."""
    payload = event.payload
    try:
        asset_ids = payload.get("asset_ids", [])
        severity = payload.get("severity", "warning")
        if not asset_ids:
            logger.debug("asset: 告警事件无关联资产, 跳过健康状态更新")
            return

        from app.infra.database import async_session_factory
        from app.domains.asset.service import AssetService

        async with async_session_factory() as session:
            svc = AssetService(session)
            # 根据 severity 映射健康状态
            health_map = {
                "critical": "critical",
                "high": "warning",
                "warning": "warning",
                "info": "healthy",
            }
            new_health = health_map.get(severity, "warning")
            for asset_id in asset_ids:
                try:
                    asset = await svc.get(asset_id)
                    if asset:
                        old_health = getattr(asset, "health_status", "unknown")
                        if old_health != new_health:
                            await svc.update(asset_id, health_status=new_health)
                            logger.info(
                                "asset: 更新资产健康状态 %s -> %s, asset_id=%s",
                                old_health, new_health, asset_id,
                            )
                except Exception as e:
                    logger.warning("asset: 更新单个资产健康状态失败 asset_id=%s: %s", asset_id, e)
            await session.commit()
        logger.info("asset: 告警创建触发健康状态更新完成, event=%s", event.event_type)
    except Exception as e:
        logger.error("asset: 告警创建更新健康状态失败: %s", e)


async def on_execution_completed_update_timeline(event: DomainEvent) -> None:
    """自动化执行完成时更新资产时间线."""
    payload = event.payload
    try:
        asset_ids = payload.get("asset_ids", [])
        execution_id = payload.get("execution_id", "")
        if not asset_ids:
            logger.debug("asset: 执行完成事件无关联资产, 跳过时间线更新")
            return

        from app.infra.database import async_session_factory
        from app.domains.asset.service import AssetService

        async with async_session_factory() as session:
            svc = AssetService(session)
            for asset_id in asset_ids:
                try:
                    # 记录自动化执行到资产时间线
                    timeline_entry = {
                        "type": "automation_completed",
                        "execution_id": execution_id,
                        "timestamp": event.timestamp,
                        "policy_id": payload.get("policy_id"),
                        "trigger_source": payload.get("trigger_source"),
                    }
                    await svc.add_timeline_entry(asset_id, timeline_entry)
                    logger.info(
                        "asset: 更新资产时间线 asset_id=%s execution_id=%s",
                        asset_id, execution_id,
                    )
                except Exception as e:
                    logger.warning("asset: 更新单个资产时间线失败 asset_id=%s: %s", asset_id, e)
            await session.commit()
        logger.info("asset: 执行完成触发时间线更新完成")
    except Exception as e:
        logger.error("asset: 执行完成更新时间线失败: %s", e)


async def on_execution_failed_update_timeline(event: DomainEvent) -> None:
    """自动化执行失败时更新资产时间线."""
    payload = event.payload
    try:
        asset_ids = payload.get("asset_ids", [])
        execution_id = payload.get("execution_id", "")
        if not asset_ids:
            return

        from app.infra.database import async_session_factory
        from app.domains.asset.service import AssetService

        async with async_session_factory() as session:
            svc = AssetService(session)
            for asset_id in asset_ids:
                try:
                    timeline_entry = {
                        "type": "automation_failed",
                        "execution_id": execution_id,
                        "timestamp": event.timestamp,
                        "error": payload.get("error", ""),
                    }
                    await svc.add_timeline_entry(asset_id, timeline_entry)
                except Exception as e:
                    logger.warning("asset: 更新资产时间线(失败)失败 asset_id=%s: %s", asset_id, e)
            await session.commit()
        logger.info("asset: 执行失败触发时间线更新完成")
    except Exception as e:
        logger.error("asset: 执行失败更新时间线失败: %s", e)


def register_handlers() -> None:
    """注册资产领域的事件处理器."""
    bus = get_event_bus()
    bus.subscribe(AlertEvents.ALERT_CREATED, on_alert_created_update_health)
    bus.subscribe(AutomationEvents.EXECUTION_COMPLETED, on_execution_completed_update_timeline)
    bus.subscribe(AutomationEvents.EXECUTION_FAILED, on_execution_failed_update_timeline)
    logger.info("asset领域事件处理器已注册 (3个handler)")
