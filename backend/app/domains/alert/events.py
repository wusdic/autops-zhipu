"""告警中心领域事件定义."""
from __future__ import annotations

from app.common.events import (
    DomainEvent,
    get_event_bus,
    AlertEvents,
)


async def publish_alert_rule_created(rule_id: str, rule_name: str, **kwargs) -> None:
    """发布告警规则创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AlertEvents.ALERT_RULE_CREATED,
        domain="alert",
        payload={"rule_id": rule_id, "rule_name": rule_name, **kwargs},
        source="alert",
    ))


async def publish_alert_rule_updated(rule_id: str, **kwargs) -> None:
    """发布告警规则更新事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AlertEvents.ALERT_RULE_UPDATED,
        domain="alert",
        payload={"rule_id": rule_id, **kwargs},
        source="alert",
    ))


async def publish_alert_created(alert_id: str, rule_id: str, severity: str, **kwargs) -> None:
    """发布告警创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AlertEvents.ALERT_CREATED,
        domain="alert",
        payload={"alert_id": alert_id, "rule_id": rule_id, "severity": severity, **kwargs},
        source="alert",
    ))


async def publish_alert_acknowledged(alert_id: str, acknowledged_by: str, **kwargs) -> None:
    """发布告警确认事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AlertEvents.ALERT_ACKNOWLEDGED,
        domain="alert",
        payload={"alert_id": alert_id, "acknowledged_by": acknowledged_by, **kwargs},
        source="alert",
    ))


async def publish_alert_resolved(alert_id: str, resolved_by: str, **kwargs) -> None:
    """发布告警解决事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AlertEvents.ALERT_RESOLVED,
        domain="alert",
        payload={"alert_id": alert_id, "resolved_by": resolved_by, **kwargs},
        source="alert",
    ))


async def publish_alert_escalated(alert_id: str, escalation_level: str, **kwargs) -> None:
    """发布告警升级事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AlertEvents.ALERT_ESCALATED,
        domain="alert",
        payload={"alert_id": alert_id, "escalation_level": escalation_level, **kwargs},
        source="alert",
    ))


async def publish_alert_suppressed(alert_id: str, reason: str = "", **kwargs) -> None:
    """发布告警抑制事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=AlertEvents.ALERT_SUPPRESSED,
        domain="alert",
        payload={"alert_id": alert_id, "reason": reason, **kwargs},
        source="alert",
    ))
