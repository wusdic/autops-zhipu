"""告警中心领域事件处理器."""
from __future__ import annotations

import logging

from app.common.events import (
    DomainEvent,
    get_event_bus,
    EventEvents,
    StateEvents,
)

logger = logging.getLogger(__name__)


async def on_event_created_match_rules(event: DomainEvent) -> None:
    """事件创建时匹配告警规则."""
    payload = event.payload
    try:
        event_type = payload.get("event_type", "")
        asset_id = payload.get("asset_id")
        if not event_type and not asset_id:
            logger.debug("alert: 事件创建缺少event_type/asset_id, 跳过规则匹配")
            return

        from app.infra.database import async_session_factory
        from app.domains.alert.service import AlertService
        from app.common.events import AlertEvents

        async with async_session_factory() as session:
            svc = AlertService(session)
            rules = await svc.list_rules(enabled_only=True)
            matched_alerts = []
            for rule in rules:
                rule_types = rule.event_types if isinstance(rule.event_types, list) else []
                rule_assets = rule.asset_ids if isinstance(rule.asset_ids, list) else []
                type_match = event_type in rule_types or not rule_types
                asset_match = asset_id in rule_assets if rule_assets else True
                if type_match and asset_match:
                    matched_alerts.append({
                        "title": f"[规则触发] {rule.name}",
                        "severity": rule.severity,
                        "rule_id": str(rule.id),
                        "event_ids": [event.event_id],
                        "asset_ids": [asset_id] if asset_id else [],
                        "context": payload,
                    })

        if matched_alerts:
            bus = get_event_bus()
            for alert_data in matched_alerts:
                await bus.publish(DomainEvent(
                    event_type=AlertEvents.ALERT_CREATED,
                    domain="alert",
                    payload=alert_data,
                    source="alert_engine",
                    correlation_id=event.correlation_id or event.event_id,
                ))
            logger.info("alert: 事件创建匹配到 %d 条告警规则", len(matched_alerts))
        else:
            logger.debug("alert: 事件创建未匹配到告警规则 event_type=%s", event_type)
    except Exception as e:
        logger.error("alert: 事件创建匹配告警规则失败: %s", e)


async def on_state_recovered_auto_resolve(event: DomainEvent) -> None:
    """状态恢复时自动resolve关联告警."""
    payload = event.payload
    try:
        asset_id = payload.get("asset_id")
        new_status = payload.get("new_status", "")
        if not asset_id or new_status != "normal":
            return

        from app.infra.database import async_session_factory
        from app.domains.alert.service import AlertService

        async with async_session_factory() as session:
            svc = AlertService(session)
            # 查找该资产的活跃告警
            active_alerts = await svc.list_alerts(
                asset_id=asset_id,
                status="active",
            )
            resolved_count = 0
            for alert in active_alerts:
                try:
                    await svc.resolve(alert_id=str(alert.id), user_id="system")
                    resolved_count += 1
                except Exception as e:
                    logger.warning(
                        "alert: 自动resolve告警失败 alert_id=%s: %s",
                        str(alert.id), e,
                    )
            await session.commit()
            logger.info(
                "alert: 状态恢复自动resolve %d 条告警 asset_id=%s",
                resolved_count, asset_id,
            )
    except Exception as e:
        logger.error("alert: 状态恢复自动resolve告警失败: %s", e)


async def on_event_deduplicated_suppress(event: DomainEvent) -> None:
    """事件去重时抑制重复告警."""
    payload = event.payload
    try:
        original_event_id = payload.get("original_event_id", "")
        if not original_event_id:
            return
        logger.info(
            "alert: 事件去重, 跳过重复告警 original_event_id=%s",
            original_event_id,
        )
    except Exception as e:
        logger.error("alert: 事件去重抑制告警失败: %s", e)


def register_handlers() -> None:
    """注册告警领域的事件处理器."""
    bus = get_event_bus()
    bus.subscribe(EventEvents.EVENT_CREATED, on_event_created_match_rules)
    bus.subscribe(StateEvents.STATE_RECOVERED, on_state_recovered_auto_resolve)
    bus.subscribe(EventEvents.EVENT_DEDUPLICATED, on_event_deduplicated_suppress)
    logger.info("alert领域事件处理器已注册 (3个handler)")
