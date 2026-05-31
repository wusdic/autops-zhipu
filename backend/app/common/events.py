"""AUTOPS 全局事件总线.

设计原则：
- 领域间通过事件总线通信，不直接调用其他领域 service
- 支持同步和异步两种处理模式
- 事件持久化到数据库（通过 audit log）
- 支持事件优先级和过滤
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine
from functools import lru_cache

logger = logging.getLogger(__name__)


class EventPriority(int, Enum):
    """事件优先级."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class DomainEvent:
    """领域事件基类.

    所有领域间通信的事件都继承此类。
    """
    event_type: str
    domain: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    priority: EventPriority = EventPriority.NORMAL
    source: str = ""
    correlation_id: str = ""  # 用于追踪关联事件链

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "domain": self.domain,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "priority": self.priority.value,
            "source": self.source,
            "correlation_id": self.correlation_id,
        }


# 事件处理器类型
SyncHandler = Callable[[DomainEvent], None]
AsyncHandler = Callable[[DomainEvent], Coroutine[Any, Any, None]]
EventHandler = SyncHandler | AsyncHandler


class EventBus:
    """进程内事件总线.

    使用方式：
        bus = get_event_bus()
        bus.subscribe("state.status_changed", my_handler)
        await bus.publish(DomainEvent(
            event_type="state.status_changed",
            domain="state",
            payload={"asset_id": "...", "old_status": "normal", "new_status": "critical"}
        ))
    """

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._wildcard_handlers: list[EventHandler] = []
        self._event_log: list[dict[str, Any]] = []
        self._max_log_size = 1000

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """订阅指定类型的事件."""
        self._handlers[event_type].append(handler)
        logger.debug("EventBus: %s 订阅了事件 %s", handler.__name__ if hasattr(handler, '__name__') else handler, event_type)

    def subscribe_all(self, handler: EventHandler) -> None:
        """订阅所有事件（审计/日志用）."""
        self._wildcard_handlers.append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """取消订阅."""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]

    async def publish(self, event: DomainEvent) -> None:
        """发布事件到所有订阅者."""
        event_dict = event.to_dict()

        # 记录事件日志
        self._event_log.append(event_dict)
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]

        logger.info(
            "EventBus 发布: [%s] %s (priority=%s)",
            event.domain, event.event_type, event.priority.name
        )

        # 调用特定事件类型的处理器
        handlers = list(self._handlers.get(event.event_type, []))

        # 也调用通配处理器
        all_handlers = handlers + self._wildcard_handlers

        for handler in all_handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                logger.exception(
                    "EventBus 处理器 %s 处理事件 %s 时出错",
                    handler.__name__ if hasattr(handler, '__name__') else handler,
                    event.event_type,
                )

    def get_recent_events(self, limit: int = 100) -> list[dict[str, Any]]:
        """获取最近发布的事件（用于调试/审计）."""
        return self._event_log[-limit:]

    def clear(self) -> None:
        """清除所有订阅和日志（测试用）."""
        self._handlers.clear()
        self._wildcard_handlers.clear()
        self._event_log.clear()


@lru_cache(maxsize=1)
def get_event_bus() -> EventBus:
    """获取全局事件总线单例."""
    return EventBus()


# ============================================================
# 事件类型常量 — 按领域分组
# ============================================================

class AssetEvents:
    """资产中心事件."""
    ASSET_CREATED = "asset.created"
    ASSET_UPDATED = "asset.updated"
    ASSET_DELETED = "asset.deleted"
    ASSET_STATUS_CHANGED = "asset.status_changed"
    ASSET_HEALTH_CHANGED = "asset.health_changed"
    ASSET_DISCOVERED = "asset.discovered"
    ASSET_RELATION_ADDED = "asset.relation_added"
    ASSET_RELATION_REMOVED = "asset.relation_removed"


class ConfigEvents:
    """配置中心事件."""
    CONFIG_VERSION_CREATED = "config.version_created"
    CONFIG_VERSION_PUBLISHED = "config.version_published"
    CONFIG_BINDING_CREATED = "config.binding_created"
    CONFIG_DRIFT_DETECTED = "config.drift_detected"
    CREDENTIAL_CREATED = "config.credential_created"
    CREDENTIAL_TESTED = "config.credential_tested"
    CREDENTIAL_BINDING_CREATED = "config.credential_binding_created"


class CollectorEvents:
    """采集中心事件."""
    COLLECTOR_REGISTERED = "collector.registered"
    COLLECTOR_HEALTH_CHANGED = "collector.health_changed"
    JOB_CREATED = "collector.job_created"
    JOB_COMPLETED = "collector.job_completed"
    JOB_FAILED = "collector.job_failed"
    JOB_TIMEOUT = "collector.job_timeout"


class StateEvents:
    """状态中心事件."""
    SNAPSHOT_RECORDED = "state.snapshot_recorded"
    STATE_CHANGED = "state.status_changed"
    STATE_CRITICAL = "state.critical_detected"
    STATE_RECOVERED = "state.recovered"


class EventEvents:
    """事件中心事件."""
    EVENT_CREATED = "event.created"
    EVENT_DEDUPLICATED = "event.deduplicated"


class AlertEvents:
    """告警中心事件."""
    ALERT_RULE_CREATED = "alert.rule_created"
    ALERT_RULE_UPDATED = "alert.rule_updated"
    ALERT_CREATED = "alert.created"
    ALERT_ACKNOWLEDGED = "alert.acknowledged"
    ALERT_RESOLVED = "alert.resolved"
    ALERT_ESCALATED = "alert.escalated"
    ALERT_SUPPRESSED = "alert.suppressed"


class PolicyEvents:
    """策略中心事件."""
    POLICY_CREATED = "policy.created"
    POLICY_UPDATED = "policy.updated"
    POLICY_ACTIVATED = "policy.activated"
    POLICY_TRIGGERED = "policy.triggered"
    POLICY_SIMULATED = "policy.simulated"
    POLICY_APPROVAL_REQUIRED = "policy.approval_required"
    POLICY_APPROVED = "policy.approved"
    POLICY_REJECTED = "policy.rejected"


class AutomationEvents:
    """自动化中心事件."""
    SCRIPT_CREATED = "automation.script_created"
    PLAYBOOK_CREATED = "automation.playbook_created"
    EXECUTION_CREATED = "automation.execution_created"
    EXECUTION_APPROVED = "automation.execution_approved"
    EXECUTION_STARTED = "automation.execution_started"
    EXECUTION_STEP_COMPLETED = "automation.step_completed"
    EXECUTION_STEP_FAILED = "automation.step_failed"
    EXECUTION_COMPLETED = "automation.execution_completed"
    EXECUTION_FAILED = "automation.execution_failed"
    EXECUTION_CANCELLED = "automation.execution_cancelled"
    EXECUTION_ROLLED_BACK = "automation.execution_rolled_back"
    DRY_RUN_COMPLETED = "automation.dry_run_completed"


class AIOpsEvents:
    """AIops中心事件."""
    ANALYSIS_REQUESTED = "aiops.analysis_requested"
    ANALYSIS_COMPLETED = "aiops.analysis_completed"
    ANALYSIS_FAILED = "aiops.analysis_failed"
    ANALYSIS_DEGRADED = "aiops.analysis_degraded"
    FEEDBACK_SUBMITTED = "aiops.feedback_submitted"


class KnowledgeEvents:
    """知识中心事件."""
    ARTICLE_CREATED = "knowledge.article_created"
    ARTICLE_UPDATED = "knowledge.article_updated"
    ARTICLE_PUBLISHED = "knowledge.article_published"
    ARTICLE_IMPORTED = "knowledge.article_imported"
    DRAFT_CREATED = "knowledge.draft_created"


class TicketEvents:
    """工单中心事件."""
    TICKET_CREATED = "ticket.created"
    TICKET_UPDATED = "ticket.updated"
    TICKET_ASSIGNED = "ticket.assigned"
    TICKET_STATUS_CHANGED = "ticket.status_changed"
    TICKET_COMMENT_ADDED = "ticket.comment_added"
    TICKET_RESOLVED = "ticket.resolved"
    TICKET_CLOSED = "ticket.closed"
    TICKET_ESCALATED = "ticket.escalated"
    TICKET_CONVERTED_TO_KNOWLEDGE = "ticket.converted_to_knowledge"


class GovernanceEvents:
    """治理中心事件."""
    USER_CREATED = "governance.user_created"
    USER_UPDATED = "governance.user_updated"
    USER_LOGIN = "governance.user_login"
    USER_LOCKED = "governance.user_locked"
    ROLE_CREATED = "governance.role_created"
    ROLE_UPDATED = "governance.role_updated"
    API_KEY_CREATED = "governance.api_key_created"
    API_KEY_REVOKED = "governance.api_key_revoked"


class LogEvents:
    """日志中心事件."""
    LOG_ENTRY_CREATED = "log.entry_created"
    EXECUTION_LOG_STREAM = "log.execution_log_stream"


class NotificationEvents:
    """通知中心事件."""
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_READ = "notification.read"
