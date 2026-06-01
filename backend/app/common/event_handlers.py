"""AUTOPS 领域间事件处理器注册中心.

在应用启动时将所有领域的 handlers 注册到 EventBus，
建立领域间的联动链路。

本文件仅做注册编排，具体处理器逻辑在各自领域模块中。
"""
from __future__ import annotations

import logging

from app.common.events import get_event_bus

logger = logging.getLogger(__name__)

_handlers_registered = False


def register_all_handlers() -> None:
    """注册所有领域事件处理器（幂等，只执行一次）.

    按依赖顺序注册各领域处理器：
    event → state → alert → ticket → aiops → automation → 其他领域
    """
    global _handlers_registered
    if _handlers_registered:
        return
    _handlers_registered = True

    # --- 核心领域（按依赖顺序） ---

    from app.domains.event.handlers import register_handlers as register_event
    register_event()

    from app.domains.state.handlers import register_handlers as register_state
    register_state()

    from app.domains.alert.handlers import register_handlers as register_alert
    register_alert()

    from app.domains.ticket.handlers import register_handlers as register_ticket
    register_ticket()

    from app.domains.aiops.handlers import register_handlers as register_aiops
    register_aiops()

    # --- 辅助领域 ---

    from app.domains.automation.handlers import register_handlers as register_automation
    register_automation()

    from app.domains.collector.handlers import register_handlers as register_collector
    register_collector()

    from app.domains.policy.handlers import register_handlers as register_policy
    register_policy()

    from app.domains.knowledge.handlers import register_handlers as register_knowledge
    register_knowledge()

    from app.domains.notification.handlers import register_handlers as register_notification
    register_notification()

    from app.domains.asset.handlers import register_handlers as register_asset
    register_asset()

    from app.domains.log.handlers import register_handlers as register_log
    register_log()

    from app.domains.governance.handlers import register_handlers as register_governance
    register_governance()

    from app.domains.config.handlers import register_handlers as register_config
    register_config()

    # --- 全局审计（通配处理器） ---

    bus = get_event_bus()
    bus.subscribe_all(_on_any_event_audit)

    logger.info("EventBus: 所有领域事件处理器已注册 (15个领域 + 全局审计)")


# ---------------------------------------------------------------------------
# 全局处理器（审计 — 唯一保留在此的处理器）
# ---------------------------------------------------------------------------

async def _on_any_event_audit(event) -> None:
    """全局审计: 记录所有事件到审计日志."""
    logger.debug(
        "AUDIT event_id=%s type=%s domain=%s source=%s",
        event.event_id, event.event_type, event.domain, event.source,
    )
