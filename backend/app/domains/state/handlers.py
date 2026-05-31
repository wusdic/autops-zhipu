"""状态中心领域事件处理器."""
from __future__ import annotations

import logging

from app.common.events import (
    DomainEvent,
    get_event_bus,
    CollectorEvents,
    AlertEvents,
)

logger = logging.getLogger(__name__)


async def on_job_completed_update_snapshot(event: DomainEvent) -> None:
    """采集完成时更新状态快照."""
    payload = event.payload
    try:
        asset_id = payload.get("asset_id")
        result_data = payload.get("result_data", {})
        if not asset_id or not result_data:
            logger.debug("state: 采集完成事件缺少asset_id或result_data, 跳过状态更新")
            return

        from app.infra.database import async_session_factory
        from app.domains.state.service import StateService
        from app.domains.state.schemas import StateSnapshotCreate

        async with async_session_factory() as session:
            svc = StateService(session)
            for state_type, value in result_data.items():
                if isinstance(value, dict) and "status" in value:
                    try:
                        await svc.record_snapshot(StateSnapshotCreate(
                            asset_id=asset_id,
                            state_type=state_type,
                            status=value["status"],
                            value=value,
                        ))
                    except Exception as e:
                        logger.warning(
                            "state: 记录单个状态快照失败 state_type=%s: %s",
                            state_type, e,
                        )
            await session.commit()
        logger.info(
            "state: 采集完成更新状态快照 asset_id=%s state_types=%s",
            asset_id, list(result_data.keys()),
        )
    except Exception as e:
        logger.error("state: 采集完成更新状态快照失败: %s", e)


async def on_alert_resolved_mark_recovered(event: DomainEvent) -> None:
    """告警解决时标记关联资产状态恢复."""
    payload = event.payload
    try:
        asset_ids = payload.get("asset_ids", [])
        alert_id = payload.get("alert_id", "")
        if not asset_ids:
            logger.debug("state: 告警解决事件无关联资产, 跳过状态恢复")
            return

        from app.infra.database import async_session_factory
        from app.domains.state.service import StateService
        from app.domains.state.schemas import StateSnapshotCreate

        async with async_session_factory() as session:
            svc = StateService(session)
            for asset_id in asset_ids:
                try:
                    await svc.record_snapshot(StateSnapshotCreate(
                        asset_id=asset_id,
                        state_type="health",
                        status="normal",
                        value={"recovered": True, "alert_id": alert_id},
                    ))
                except Exception as e:
                    logger.warning(
                        "state: 标记资产状态恢复失败 asset_id=%s: %s",
                        asset_id, e,
                    )
            await session.commit()
        logger.info("state: 告警解决标记状态恢复完成 alert_id=%s", alert_id)
    except Exception as e:
        logger.error("state: 告警解决标记状态恢复失败: %s", e)


async def on_job_failed_mark_degraded(event: DomainEvent) -> None:
    """采集失败时标记资产状态降级."""
    payload = event.payload
    try:
        asset_id = payload.get("asset_id")
        error = payload.get("error", "")
        if not asset_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.state.service import StateService
        from app.domains.state.schemas import StateSnapshotCreate

        async with async_session_factory() as session:
            svc = StateService(session)
            await svc.record_snapshot(StateSnapshotCreate(
                asset_id=asset_id,
                state_type="collection",
                status="degraded",
                value={"error": error, "source": "collector_job_failed"},
            ))
            await session.commit()
        logger.info("state: 采集失败标记状态降级 asset_id=%s", asset_id)
    except Exception as e:
        logger.error("state: 采集失败标记状态降级失败: %s", e)


def register_handlers() -> None:
    """注册状态领域的事件处理器."""
    bus = get_event_bus()
    bus.subscribe(CollectorEvents.JOB_COMPLETED, on_job_completed_update_snapshot)
    bus.subscribe(AlertEvents.ALERT_RESOLVED, on_alert_resolved_mark_recovered)
    bus.subscribe(CollectorEvents.JOB_FAILED, on_job_failed_mark_degraded)
    logger.info("state领域事件处理器已注册 (3个handler)")
