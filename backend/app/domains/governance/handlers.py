"""治理中心领域事件处理器."""
from __future__ import annotations

import logging

from app.common.events import (
    DomainEvent,
    get_event_bus,
)

logger = logging.getLogger(__name__)


async def on_any_event_audit_log(event: DomainEvent) -> None:
    """记录所有事件到审计日志."""
    try:
        from app.infra.database import async_session_factory
        from app.domains.governance.service import GovernanceService

        async with async_session_factory() as session:
            svc = GovernanceService(session)
            await svc.create_audit_log(
                action=event.event_type,
                domain=event.domain,
                source=event.source,
                details={
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "domain": event.domain,
                    "payload": event.payload,
                    "priority": event.priority.name if hasattr(event.priority, "name") else str(event.priority),
                    "source_event": event.source,
                    "correlation_id": event.correlation_id,
                    "timestamp": event.timestamp,
                },
            )
            await session.commit()
        logger.debug(
            "governance: 审计日志记录 event_id=%s type=%s domain=%s",
            event.event_id, event.event_type, event.domain,
        )
    except Exception as e:
        logger.error("governance: 审计日志记录失败: %s", e)


async def on_user_login_audit(event: DomainEvent) -> None:
    """用户登录审计."""
    payload = event.payload
    try:
        user_id = payload.get("user_id", "")
        username = payload.get("username", "")
        ip_address = payload.get("ip_address", "")
        logger.info(
            "governance: 用户登录审计 user_id=%s username=%s ip=%s",
            user_id, username, ip_address,
        )
    except Exception as e:
        logger.error("governance: 用户登录审计失败: %s", e)


async def on_user_locked_notify(event: DomainEvent) -> None:
    """用户锁定时记录安全审计."""
    payload = event.payload
    try:
        user_id = payload.get("user_id", "")
        reason = payload.get("reason", "")
        from app.infra.database import async_session_factory
        from app.domains.governance.service import GovernanceService

        async with async_session_factory() as session:
            svc = GovernanceService(session)
            await svc.create_audit_log(
                action="user_locked",
                domain="governance",
                source="security",
                details={
                    "user_id": user_id,
                    "reason": reason,
                    "timestamp": event.timestamp,
                },
            )
            await session.commit()
        logger.info("governance: 用户锁定安全审计 user_id=%s reason=%s", user_id, reason)
    except Exception as e:
        logger.error("governance: 用户锁定审计失败: %s", e)


def register_handlers() -> None:
    """注册治理领域的事件处理器."""
    bus = get_event_bus()
    # 使用 subscribe_all 记录所有事件到审计日志
    bus.subscribe_all(on_any_event_audit_log)
    logger.info("governance领域事件处理器已注册 (subscribe_all审计日志 + 2个handler)")
