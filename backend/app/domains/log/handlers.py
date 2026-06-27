"""日志中心领域事件处理器."""
from __future__ import annotations

import logging

from app.common.events import (
    DomainEvent,
    get_event_bus,
    AutomationEvents,
)

logger = logging.getLogger(__name__)


async def on_execution_started_write_log(event: DomainEvent) -> None:
    """自动化执行开始时写入执行日志."""
    payload = event.payload
    try:
        execution_id = payload.get("execution_id", "")
        if not execution_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.log.api import LogService

        async with async_session_factory() as session:
            svc = LogService(session)
            await svc.create_log_entry(
                log_type="execution",
                ref_id=execution_id,
                level="info",
                message=f"自动化执行开始: {execution_id}",
                details={
                    "execution_type": payload.get("execution_type", ""),
                    "trigger_source": payload.get("trigger_source", ""),
                    "asset_ids": payload.get("asset_ids", []),
                    "policy_id": payload.get("policy_id", ""),
                    "source_event_id": event.event_id,
                },
            )
            await session.commit()
        logger.info("log: 自动化执行开始写入日志 execution_id=%s", execution_id)
    except Exception as e:
        logger.error("log: 自动化执行开始写入日志失败: %s", e)


async def on_execution_completed_write_log(event: DomainEvent) -> None:
    """自动化执行完成时写入执行日志."""
    payload = event.payload
    try:
        execution_id = payload.get("execution_id", "")
        if not execution_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.log.api import LogService

        async with async_session_factory() as session:
            svc = LogService(session)
            await svc.create_log_entry(
                log_type="execution",
                ref_id=execution_id,
                level="info",
                message=f"自动化执行完成: {execution_id}",
                details={
                    "result": payload.get("result", ""),
                    "asset_ids": payload.get("asset_ids", []),
                    "source_event_id": event.event_id,
                },
            )
            await session.commit()
        logger.info("log: 自动化执行完成写入日志 execution_id=%s", execution_id)
    except Exception as e:
        logger.error("log: 自动化执行完成写入日志失败: %s", e)


async def on_execution_failed_write_log(event: DomainEvent) -> None:
    """自动化执行失败时写入执行日志."""
    payload = event.payload
    try:
        execution_id = payload.get("execution_id", "")
        error = payload.get("error", "")
        if not execution_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.log.api import LogService

        async with async_session_factory() as session:
            svc = LogService(session)
            await svc.create_log_entry(
                log_type="execution",
                ref_id=execution_id,
                level="error",
                message=f"自动化执行失败: {execution_id}",
                details={
                    "error": error,
                    "policy_id": payload.get("policy_id", ""),
                    "asset_ids": payload.get("asset_ids", []),
                    "source_event_id": event.event_id,
                },
            )
            await session.commit()
        logger.info("log: 自动化执行失败写入日志 execution_id=%s", execution_id)
    except Exception as e:
        logger.error("log: 自动化执行失败写入日志失败: %s", e)


def register_handlers() -> None:
    """注册日志领域的事件处理器."""
    bus = get_event_bus()
    bus.subscribe(AutomationEvents.EXECUTION_STARTED, on_execution_started_write_log)
    bus.subscribe(AutomationEvents.EXECUTION_COMPLETED, on_execution_completed_write_log)
    bus.subscribe(AutomationEvents.EXECUTION_FAILED, on_execution_failed_write_log)
    logger.info("log领域事件处理器已注册 (3个handler)")
