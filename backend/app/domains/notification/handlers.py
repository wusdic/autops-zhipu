"""通知中心领域事件处理器."""
from __future__ import annotations

import logging

from app.common.events import (
    DomainEvent,
    get_event_bus,
    AlertEvents,
    TicketEvents,
    AutomationEvents,
    NotificationEvents,
)

logger = logging.getLogger(__name__)


async def on_alert_created_notify(event: DomainEvent) -> None:
    """告警创建时发送通知."""
    payload = event.payload
    try:
        alert_id = payload.get("alert_id", "")
        title = payload.get("title", "告警通知")
        severity = payload.get("severity", "warning")
        if not alert_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.notification.service import NotificationService

        async with async_session_factory() as session:
            svc = NotificationService(session)
            await svc.send_notification(
                notification_type="alert",
                title=f"告警: {title}",
                message=f"严重度: {severity} | 告警ID: {alert_id}",
                ref_id=alert_id,
                severity=severity,
                channel=payload.get("channel", "default"),
            )
            await session.commit()

        bus = get_event_bus()
        await bus.publish(DomainEvent(
            event_type=NotificationEvents.NOTIFICATION_SENT,
            domain="notification",
            payload={
                "type": "alert",
                "title": title,
                "alert_id": alert_id,
                "severity": severity,
            },
            source="notification_handler",
            correlation_id=event.correlation_id or event.event_id,
        ))
        logger.info("notification: 告警通知已发送 alert_id=%s severity=%s", alert_id, severity)
    except Exception as e:
        logger.error("notification: 告警通知发送失败: %s", e)


async def on_alert_escalated_notify(event: DomainEvent) -> None:
    """告警升级时发送紧急通知."""
    payload = event.payload
    try:
        alert_id = payload.get("alert_id", "")
        title = payload.get("title", "告警升级通知")
        escalation_level = payload.get("escalation_level", "")
        escalate_to = payload.get("escalate_to", "")
        if not alert_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.notification.service import NotificationService

        async with async_session_factory() as session:
            svc = NotificationService(session)
            await svc.send_notification(
                notification_type="alert_escalation",
                title=f"告警升级: {title}",
                message=f"升级级别: {escalation_level} | 告警ID: {alert_id}",
                ref_id=alert_id,
                severity="critical",
                recipient=escalate_to,
                channel="urgent",
            )
            await session.commit()

        logger.info(
            "notification: 告警升级通知已发送 alert_id=%s level=%s to=%s",
            alert_id, escalation_level, escalate_to,
        )
    except Exception as e:
        logger.error("notification: 告警升级通知发送失败: %s", e)


async def on_ticket_assigned_notify(event: DomainEvent) -> None:
    """工单分配时发送通知."""
    payload = event.payload
    try:
        ticket_id = payload.get("ticket_id", "")
        assignee = payload.get("assignee", payload.get("assigned_to", ""))
        title = payload.get("title", "工单分配通知")
        if not ticket_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.notification.service import NotificationService

        async with async_session_factory() as session:
            svc = NotificationService(session)
            await svc.send_notification(
                notification_type="ticket_assigned",
                title=f"工单分配: {title}",
                message=f"您被分配了工单: {title} (ID: {ticket_id})",
                ref_id=ticket_id,
                recipient=assignee,
                channel="default",
            )
            await session.commit()

        logger.info(
            "notification: 工单分配通知已发送 ticket_id=%s assignee=%s",
            ticket_id, assignee,
        )
    except Exception as e:
        logger.error("notification: 工单分配通知发送失败: %s", e)


async def on_execution_failed_notify(event: DomainEvent) -> None:
    """自动化执行失败时发送通知."""
    payload = event.payload
    try:
        execution_id = payload.get("execution_id", "")
        error = payload.get("error", "")
        if not execution_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.notification.service import NotificationService

        async with async_session_factory() as session:
            svc = NotificationService(session)
            await svc.send_notification(
                notification_type="automation_failure",
                title=f"自动化执行失败: {execution_id}",
                message=f"执行ID: {execution_id} | 错误: {error}",
                ref_id=execution_id,
                severity="high",
                channel="urgent",
            )
            await session.commit()

        logger.info("notification: 自动化执行失败通知已发送 execution_id=%s", execution_id)
    except Exception as e:
        logger.error("notification: 自动化执行失败通知发送失败: %s", e)


def register_handlers() -> None:
    """注册通知领域的事件处理器."""
    bus = get_event_bus()
    bus.subscribe(AlertEvents.ALERT_CREATED, on_alert_created_notify)
    bus.subscribe(AlertEvents.ALERT_ESCALATED, on_alert_escalated_notify)
    bus.subscribe(TicketEvents.TICKET_ASSIGNED, on_ticket_assigned_notify)
    bus.subscribe(AutomationEvents.EXECUTION_FAILED, on_execution_failed_notify)
    logger.info("notification领域事件处理器已注册 (4个handler)")
