"""采集中心领域事件处理器."""
from __future__ import annotations

import logging

from app.common.events import (
    DomainEvent,
    get_event_bus,
    AssetEvents,
    ConfigEvents,
)

logger = logging.getLogger(__name__)


async def on_asset_created_create_job(event: DomainEvent) -> None:
    """资产创建时自动创建采集作业."""
    payload = event.payload
    try:
        asset_id = payload.get("asset_id")
        asset_name = payload.get("asset_name", "")
        asset_type = payload.get("asset_type", "")
        if not asset_id:
            logger.debug("collector: 资产创建事件缺少asset_id, 跳过采集作业创建")
            return

        from app.infra.database import async_session_factory
        from app.domains.collector.service import CollectorService

        async with async_session_factory() as session:
            svc = CollectorService(session)
            # 根据资产类型查找匹配的采集器
            collectors = await svc.list_collectors(asset_type=asset_type)
            for collector in collectors:
                collector_id = str(getattr(collector, "id", ""))
                try:
                    job = await svc.create_job(
                        collector_id=collector_id,
                        asset_id=asset_id,
                        job_type="auto_discovery",
                        config={
                            "asset_name": asset_name,
                            "asset_type": asset_type,
                            "trigger": "asset_created",
                        },
                    )
                    logger.info(
                        "collector: 自动创建采集作业 job_id=%s collector_id=%s asset_id=%s",
                        getattr(job, "id", ""), collector_id, asset_id,
                    )
                except Exception as e:
                    logger.warning(
                        "collector: 创建采集作业失败 collector_id=%s asset_id=%s: %s",
                        collector_id, asset_id, e,
                    )
            await session.commit()
        logger.info("collector: 资产创建触发采集作业创建完成 asset_id=%s", asset_id)
    except Exception as e:
        logger.error("collector: 资产创建触发采集作业创建失败: %s", e)


async def on_credential_tested_retry_jobs(event: DomainEvent) -> None:
    """凭证变更/测试通过时重试失败的采集作业."""
    payload = event.payload
    try:
        credential_id = payload.get("credential_id")
        result = payload.get("result", "")
        if result != "success":
            logger.debug("collector: 凭证测试未通过, 跳过重试 result=%s", result)
            return

        from app.infra.database import async_session_factory
        from app.domains.collector.service import CollectorService

        async with async_session_factory() as session:
            svc = CollectorService(session)
            # 查找因凭证问题失败的任务
            failed_jobs = await svc.list_failed_jobs(reason="credential")
            retried = 0
            for job in failed_jobs:
                job_id = str(getattr(job, "id", ""))
                try:
                    await svc.retry_job(job_id)
                    retried += 1
                except Exception as e:
                    logger.warning("collector: 重试采集作业失败 job_id=%s: %s", job_id, e)
            await session.commit()
            logger.info("collector: 凭证变更后重试采集作业完成, 重试 %d 个", retried)
    except Exception as e:
        logger.error("collector: 凭证变更触发重试失败: %s", e)


async def on_asset_deleted_cancel_jobs(event: DomainEvent) -> None:
    """资产删除时取消相关采集作业."""
    payload = event.payload
    try:
        asset_id = payload.get("asset_id")
        if not asset_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.collector.service import CollectorService

        async with async_session_factory() as session:
            svc = CollectorService(session)
            jobs = await svc.list_jobs(asset_id=asset_id, status="pending")
            for job in jobs:
                try:
                    await svc.cancel_job(str(getattr(job, "id", "")))
                except Exception as e:
                    logger.warning("collector: 取消采集作业失败: %s", e)
            await session.commit()
            logger.info("collector: 资产删除取消采集作业完成 asset_id=%s", asset_id)
    except Exception as e:
        logger.error("collector: 资产删除取消作业失败: %s", e)


def register_handlers() -> None:
    """注册采集领域的事件处理器."""
    bus = get_event_bus()
    bus.subscribe(AssetEvents.ASSET_CREATED, on_asset_created_create_job)
    bus.subscribe(ConfigEvents.CREDENTIAL_TESTED, on_credential_tested_retry_jobs)
    bus.subscribe(AssetEvents.ASSET_DELETED, on_asset_deleted_cancel_jobs)
    logger.info("collector领域事件处理器已注册 (3个handler)")
