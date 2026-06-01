"""AUTOPS 全局事件总线.

设计原则：
- 领域间通过事件总线通信，不直接调用其他领域 service
- 支持同步和异步两种处理模式
- 事件持久化到数据库（outbox pattern）
- 支持事件优先级和过滤
- 支持重试和死信
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
    correlation_id: str = ""

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
    """进程内事件总线 + Outbox持久化.

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
        self._outbox_enabled = False

    def enable_outbox(self) -> None:
        """启用outbox持久化（需要DB可用时调用）."""
        self._outbox_enabled = True

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """订阅指定类型的事件."""
        self._handlers[event_type].append(handler)
        logger.debug(
            "EventBus: %s subscribed to %s",
            handler.__name__ if hasattr(handler, '__name__') else handler,
            event_type,
        )

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
        """发布事件: 先持久化到outbox，再触发handler."""
        event_dict = event.to_dict()

        # 记录到内存日志
        self._event_log.append(event_dict)
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]

        # 持久化到outbox表
        if self._outbox_enabled:
            try:
                await self._persist_to_outbox(event)
            except Exception:
                logger.exception("EventBus: outbox persist failed for %s", event.event_type)

        logger.info(
            "EventBus publish: [%s] %s (priority=%s)",
            event.domain, event.event_type, event.priority.name
        )

        # 触发处理器
        handlers = list(self._handlers.get(event.event_type, []))
        all_handlers = handlers + self._wildcard_handlers

        for handler in all_handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                logger.exception(
                    "EventBus handler %s failed for %s",
                    handler.__name__ if hasattr(handler, '__name__') else handler,
                    event.event_type,
                )

    async def _persist_to_outbox(self, event: DomainEvent) -> None:
        """将事件持久化到 event_outbox 表."""
        from app.infra.database import get_session_factory

        session_factory = get_session_factory()
        async with session_factory() as session:
            from sqlalchemy import text
            await session.execute(
                text("""
                    INSERT INTO event_outbox
                        (event_id, event_type, domain, payload, priority, source, status, created_at)
                    VALUES
                        (:eid, :etype, :domain, :payload, :priority, :source, 'pending', NOW())
                """),
                {
                    "eid": event.event_id,
                    "etype": event.event_type,
                    "domain": event.domain,
                    "payload": json.dumps(event.payload, ensure_ascii=False, default=str),
                    "priority": event.priority.value,
                    "source": event.source,
                },
            )
            await session.commit()

    async def replay_pending(self) -> int:
        """重放所有 pending 状态的 outbox 事件（启动/恢复时调用）."""
        from app.infra.database import get_session_factory

        session_factory = get_session_factory()
        replayed = 0
        async with session_factory() as session:
            from sqlalchemy import text
            result = await session.execute(
                text("SELECT * FROM event_outbox WHERE status = 'pending' ORDER BY created_at")
            )
            rows = result.fetchall()
            for row in rows:
                try:
                    evt = DomainEvent(
                        event_id=row.event_id,
                        event_type=row.event_type,
                        domain=row.domain,
                        payload=json.loads(row.payload) if row.payload else {},
                        priority=EventPriority(row.priority),
                        source=row.source or "",
                    )
                    # 直接触发handler（不再重新入outbox）
                    handlers = list(self._handlers.get(evt.event_type, []))
                    for handler in handlers:
                        result = handler(evt)
                        if asyncio.iscoroutine(result):
                            await result
                    # 标记为已完成
                    await session.execute(
                        text("UPDATE event_outbox SET status = 'done' WHERE event_id = :eid"),
                        {"eid": row.event_id},
                    )
                    replayed += 1
                except Exception:
                    logger.exception("EventBus: replay failed for %s", row.event_id)
                    await session.execute(
                        text(
                            "UPDATE event_outbox SET status = 'dead', error = 'replay_failed' "
                            "WHERE event_id = :eid"
                        ),
                        {"eid": row.event_id},
                    )
            await session.commit()
        if replayed:
            logger.info("EventBus: replayed %d pending events", replayed)
        return replayed

    def get_recent_events(self, limit: int = 100) -> list[dict[str, Any]]:
        """获取最近发布的事件."""
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
