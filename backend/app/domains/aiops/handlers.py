"""AIOps领域事件处理器."""
from __future__ import annotations

import logging

from app.common.events import (
    DomainEvent,
    get_event_bus,
    AlertEvents,
    AIOpsEvents,
)

logger = logging.getLogger(__name__)

# 触发AI分析的告警严重度阈值
AI_ANALYSIS_SEVERITY_THRESHOLD = {"critical", "high"}


async def on_alert_created_trigger_analysis(event: DomainEvent) -> None:
    """告警创建时触发AI分析(如severity=critical/high)."""
    payload = event.payload
    try:
        severity = payload.get("severity", "")
        alert_id = payload.get("alert_id", "")
        asset_ids = payload.get("asset_ids", [])

        if severity not in AI_ANALYSIS_SEVERITY_THRESHOLD:
            logger.debug("aiops: 告警severity=%s未达AI分析阈值, 跳过", severity)
            return

        from app.infra.database import async_session_factory
        from app.domains.aiops.service import AIOpsService

        analysis_id = None
        async with async_session_factory() as session:
            svc = AIOpsService(session)
            analysis = await svc.request_analysis(
                analysis_type="alert_correlation",
                context={
                    "alert_id": alert_id,
                    "severity": severity,
                    "asset_ids": asset_ids,
                    "context": payload.get("context", {}),
                    "source_event_id": event.event_id,
                },
            )
            analysis_id = str(getattr(analysis, "id", ""))
            await session.commit()

        if analysis_id:
            bus = get_event_bus()
            await bus.publish(DomainEvent(
                event_type=AIOpsEvents.ANALYSIS_REQUESTED,
                domain="aiops",
                payload={
                    "analysis_id": analysis_id,
                    "analysis_type": "alert_correlation",
                    "alert_id": alert_id,
                    "severity": severity,
                },
                source="aiops_handler",
                correlation_id=event.correlation_id or event.event_id,
            ))
        logger.info(
            "aiops: 告警触发AI分析 alert_id=%s severity=%s analysis_id=%s",
            alert_id, severity, analysis_id,
        )
    except Exception as e:
        logger.error("aiops: 告警触发AI分析失败: %s", e)


async def on_analysis_completed_recommend(event: DomainEvent) -> None:
    """AI分析完成时记录结果."""
    payload = event.payload
    try:
        analysis_id = payload.get("analysis_id", "")
        result = payload.get("result", "")
        if not analysis_id:
            return

        logger.info(
            "aiops: AI分析完成 analysis_id=%s result_summary=%s",
            analysis_id,
            str(result)[:200] if result else "",
        )
        # AI分析结果可供知识中心推荐、策略引擎参考等
    except Exception as e:
        logger.error("aiops: AI分析完成处理失败: %s", e)


async def on_analysis_failed_log(event: DomainEvent) -> None:
    """AI分析失败时记录降级."""
    payload = event.payload
    try:
        analysis_id = payload.get("analysis_id", "")
        error = payload.get("error", "")
        logger.warning("aiops: AI分析失败 analysis_id=%s error=%s", analysis_id, error)

        bus = get_event_bus()
        await bus.publish(DomainEvent(
            event_type=AIOpsEvents.ANALYSIS_DEGRADED,
            domain="aiops",
            payload={
                "analysis_id": analysis_id,
                "reason": f"analysis_failed: {error}",
            },
            source="aiops_handler",
            correlation_id=event.event_id,
        ))
    except Exception as e:
        logger.error("aiops: AI分析失败处理失败: %s", e)


def register_handlers() -> None:
    """注册AIOps领域的事件处理器."""
    bus = get_event_bus()
    bus.subscribe(AlertEvents.ALERT_CREATED, on_alert_created_trigger_analysis)
    bus.subscribe(AIOpsEvents.ANALYSIS_COMPLETED, on_analysis_completed_recommend)
    bus.subscribe(AIOpsEvents.ANALYSIS_FAILED, on_analysis_failed_log)
    logger.info("aiops领域事件处理器已注册 (3个handler)")
