"""配置中心领域事件定义."""
from __future__ import annotations

from app.common.events import (
    DomainEvent,
    get_event_bus,
    ConfigEvents,
)


async def publish_config_version_created(config_id: str, version: str, **kwargs) -> None:
    """发布配置版本创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=ConfigEvents.CONFIG_VERSION_CREATED,
        domain="config",
        payload={"config_id": config_id, "version": version, **kwargs},
        source="config",
    ))


async def publish_config_version_published(config_id: str, version: str, **kwargs) -> None:
    """发布配置版本发布事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=ConfigEvents.CONFIG_VERSION_PUBLISHED,
        domain="config",
        payload={"config_id": config_id, "version": version, **kwargs},
        source="config",
    ))


async def publish_config_binding_created(binding_id: str, config_id: str, asset_id: str, **kwargs) -> None:
    """发布配置绑定创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=ConfigEvents.CONFIG_BINDING_CREATED,
        domain="config",
        payload={"binding_id": binding_id, "config_id": config_id, "asset_id": asset_id, **kwargs},
        source="config",
    ))


async def publish_config_drift_detected(config_id: str, asset_id: str, **kwargs) -> None:
    """发布配置漂移检测事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=ConfigEvents.CONFIG_DRIFT_DETECTED,
        domain="config",
        payload={"config_id": config_id, "asset_id": asset_id, **kwargs},
        source="config",
    ))


async def publish_credential_created(credential_id: str, **kwargs) -> None:
    """发布凭据创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=ConfigEvents.CREDENTIAL_CREATED,
        domain="config",
        payload={"credential_id": credential_id, **kwargs},
        source="config",
    ))


async def publish_credential_tested(credential_id: str, result: str, **kwargs) -> None:
    """发布凭据测试事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=ConfigEvents.CREDENTIAL_TESTED,
        domain="config",
        payload={"credential_id": credential_id, "result": result, **kwargs},
        source="config",
    ))
