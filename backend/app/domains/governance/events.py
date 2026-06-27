"""治理中心领域事件定义."""
from __future__ import annotations

from app.common.events import (
    DomainEvent,
    get_event_bus,
    GovernanceEvents,
)


async def publish_user_created(user_id: str, username: str, **kwargs) -> None:
    """发布用户创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=GovernanceEvents.USER_CREATED,
        domain="governance",
        payload={"user_id": user_id, "username": username, **kwargs},
        source="governance",
    ))


async def publish_user_updated(user_id: str, **kwargs) -> None:
    """发布用户更新事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=GovernanceEvents.USER_UPDATED,
        domain="governance",
        payload={"user_id": user_id, **kwargs},
        source="governance",
    ))


async def publish_user_login(user_id: str, username: str, **kwargs) -> None:
    """发布用户登录事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=GovernanceEvents.USER_LOGIN,
        domain="governance",
        payload={"user_id": user_id, "username": username, **kwargs},
        source="governance",
    ))


async def publish_user_locked(user_id: str, reason: str = "", **kwargs) -> None:
    """发布用户锁定事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=GovernanceEvents.USER_LOCKED,
        domain="governance",
        payload={"user_id": user_id, "reason": reason, **kwargs},
        source="governance",
    ))


async def publish_role_created(role_id: str, role_name: str, **kwargs) -> None:
    """发布角色创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=GovernanceEvents.ROLE_CREATED,
        domain="governance",
        payload={"role_id": role_id, "role_name": role_name, **kwargs},
        source="governance",
    ))


async def publish_role_updated(role_id: str, **kwargs) -> None:
    """发布角色更新事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=GovernanceEvents.ROLE_UPDATED,
        domain="governance",
        payload={"role_id": role_id, **kwargs},
        source="governance",
    ))


async def publish_api_key_created(api_key_id: str, name: str, **kwargs) -> None:
    """发布API Key创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=GovernanceEvents.API_KEY_CREATED,
        domain="governance",
        payload={"api_key_id": api_key_id, "name": name, **kwargs},
        source="governance",
    ))


async def publish_api_key_revoked(api_key_id: str, **kwargs) -> None:
    """发布API Key撤销事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=GovernanceEvents.API_KEY_REVOKED,
        domain="governance",
        payload={"api_key_id": api_key_id, **kwargs},
        source="governance",
    ))
