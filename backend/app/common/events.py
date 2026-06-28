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
from typing import TYPE_CHECKING, Any, Callable, Coroutine
from functools import lru_cache

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class EventDispatchError(Exception):
    """一个或多个事件处理器执行失败 — 触发 outbox 重试."""

    def __init__(self, event_type: str, errors: list[Exception]):
        self.event_type = event_type
        self.errors = errors
        super().__init__(
            f"{len(errors)} handler(s) failed for {event_type}: "
            + "; ".join(str(e)[:200] for e in errors)
        )


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

    @property
    def outbox_enabled(self) -> bool:
        return self._outbox_enabled

    def enable_outbox(self) -> None:
        """启用outbox持久化（需要DB可用时调用）."""
        self._outbox_enabled = True

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """订阅指定类型的事件."""
        self._handlers[event_type].append(handler)
        logger.debug(
            "EventBus: %s subscribed to %s",
            handler.__name__ if hasattr(handler, "__name__") else handler,
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

    async def publish(
        self, event: DomainEvent, session: AsyncSession | None = None
    ) -> None:
        """发布事件.

        两种模式:
        - _outbox_enabled=False (dev mode): 直接触发handler（in-process dispatch）
        - _outbox_enabled=True  (prod/API): 仅写入outbox，不触发handler

        Args:
            event: 要发布的事件
            session: 可选的业务会话。传入时 outbox 写入复用该会话的事务
                （与业务数据原子提交/回滚）；不传则使用独立会话。
        """
        event_dict = event.to_dict()

        # 记录到内存日志
        self._event_log.append(event_dict)
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size :]

        logger.info(
            "EventBus publish: [%s] %s (priority=%s, outbox=%s)",
            event.domain,
            event.event_type,
            event.priority.name,
            self._outbox_enabled,
        )

        if self._outbox_enabled:
            # 生产模式: 仅持久化到outbox，不触发handler
            try:
                await self._persist_to_outbox(event, session)
            except Exception:
                logger.exception(
                    "EventBus: outbox persist failed for %s", event.event_type
                )
                # 复用业务事务（session 非空）时，持久化失败必须向上抛出，
                # 让调用方回滚业务数据，避免"业务写成功但事件丢失"破坏一致性。
                # 独立 session 模式下已自行提交，失败仅记录日志。
                if session is not None:
                    raise
        else:
            # 开发模式: 直接触发handler（无outbox持久化）
            await self.dispatch_to_handlers(event)

    async def dispatch_to_handlers(self, event: DomainEvent) -> None:
        """仅触发已注册的处理器（由 OutboxConsumer 调用）.

        任一 handler 抛异常时，记录后聚合抛出 EventDispatchError，使 OutboxConsumer
        将该 outbox 事件按退避重试（已成功的 handler 由幂等保护在重试时跳过）。
        注意：大多数领域 handler 内部自吞异常仅记日志（不会触发重试）；仅显式向上
        抛出的关键 handler（如执行入队）才会驱动重试，从而避免静默丢任务。
        """
        handlers = list(self._handlers.get(event.event_type, []))
        all_handlers = handlers + self._wildcard_handlers

        errors: list[Exception] = []
        for handler in all_handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "EventBus handler %s failed for %s",
                    handler.__name__ if hasattr(handler, "__name__") else handler,
                    event.event_type,
                )
                errors.append(exc)

        if errors:
            raise EventDispatchError(event.event_type, errors)

    async def _persist_to_outbox(
        self, event: DomainEvent, session: AsyncSession | None = None
    ) -> None:
        """将事件持久化到 event_outbox 表.

        Args:
            event: 要持久化的事件
            session: 业务会话。传入时复用其事务（不自行 commit/关闭），
                实现 outbox 与业务数据的原子性；不传则新建独立会话并提交。
        """
        from sqlalchemy import text

        # event_outbox.id 是 varchar(36) 主键且无 server_default，必须显式传值，
        # 否则 MySQL 严格模式报 (1364, "Field 'id' doesn't have a default value")，
        # 导致所有事件发布失败、业务事务连带回滚（资产发现/告警/策略链路全断）。
        insert_sql = text("""
            INSERT INTO event_outbox
                (id, event_id, event_type, domain, payload, priority, source,
                 correlation_id, status, created_at)
            VALUES
                (:id, :eid, :etype, :domain, :payload, :priority, :source,
                 :corr_id, 'pending', NOW())
        """)
        params = {
            "id": str(uuid.uuid4()),
            "eid": event.event_id,
            "etype": event.event_type,
            "domain": event.domain,
            "payload": json.dumps(event.payload, ensure_ascii=False, default=str),
            "priority": event.priority.value,
            "source": event.source,
            "corr_id": event.correlation_id or None,
        }

        if session is not None:
            # 复用业务事务，由调用方统一 commit/rollback
            await session.execute(insert_sql, params)
            return

        # 无外部 session：新建独立会话并提交
        from app.infra.database import get_session_factory

        session_factory = get_session_factory()
        async with session_factory() as s:
            await s.execute(insert_sql, params)
            await s.commit()

    async def replay_pending(self) -> int:
        """重放所有 pending 状态的 outbox 事件（启动/恢复时调用）."""
        from app.infra.database import get_session_factory

        session_factory = get_session_factory()
        replayed = 0
        async with session_factory() as session:
            from sqlalchemy import text

            result = await session.execute(
                text(
                    "SELECT * FROM event_outbox WHERE status = 'pending' ORDER BY created_at"
                )
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
                        text(
                            "UPDATE event_outbox SET status = 'done' WHERE event_id = :eid"
                        ),
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
    # 发现扫描请求 — 由 API 发出、Worker 进程执行（移出 API 进程）
    DISCOVERY_SCAN_REQUESTED = "asset.discovery_scan_requested"


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
    FULL_SCAN_REQUESTED = "collector.full_scan_requested"
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


class AnomalyEvents:
    """异常检测中心事件."""

    ANOMALY_DETECTED = "anomaly.detected"
    ANOMALY_ACKNOWLEDGED = "anomaly.acknowledged"
    ANOMALY_RESOLVED = "anomaly.resolved"
    ANOMALY_ESCALATED = "anomaly.escalated"
    ANOMALY_ASSIGNED = "anomaly.assigned"


class InspectionEvents:
    """巡检中心事件."""

    PLAN_CREATED = "inspection.plan_created"
    PLAN_UPDATED = "inspection.plan_updated"
    TASK_STARTED = "inspection.task_started"
    TASK_COMPLETED = "inspection.task_completed"
    TASK_FAILED = "inspection.task_failed"
    RESULT_ANOMALY_FOUND = "inspection.result_anomaly_found"


class ReportEvents:
    """报表中心事件."""

    REPORT_GENERATION_REQUESTED = "report.generation_requested"
    REPORT_GENERATION_STARTED = "report.generation_started"
    REPORT_GENERATION_COMPLETED = "report.generation_completed"
    REPORT_GENERATION_FAILED = "report.generation_failed"
    REPORT_DOWNLOADED = "report.downloaded"
    REPORT_SCHEDULE_TRIGGERED = "report.schedule_triggered"
