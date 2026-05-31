"""知识中心领域事件定义."""
from __future__ import annotations

from app.common.events import (
    DomainEvent,
    EventBus,
    get_event_bus,
    KnowledgeEvents,
)


async def publish_article_created(article_id: str, title: str, **kwargs) -> None:
    """发布知识文章创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=KnowledgeEvents.ARTICLE_CREATED,
        domain="knowledge",
        payload={"article_id": article_id, "title": title, **kwargs},
        source="knowledge",
    ))


async def publish_article_updated(article_id: str, **kwargs) -> None:
    """发布知识文章更新事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=KnowledgeEvents.ARTICLE_UPDATED,
        domain="knowledge",
        payload={"article_id": article_id, **kwargs},
        source="knowledge",
    ))


async def publish_article_published(article_id: str, **kwargs) -> None:
    """发布知识文章发布事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=KnowledgeEvents.ARTICLE_PUBLISHED,
        domain="knowledge",
        payload={"article_id": article_id, **kwargs},
        source="knowledge",
    ))


async def publish_article_imported(article_id: str, source: str, **kwargs) -> None:
    """发布知识文章导入事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=KnowledgeEvents.ARTICLE_IMPORTED,
        domain="knowledge",
        payload={"article_id": article_id, "source": source, **kwargs},
        source="knowledge",
    ))


async def publish_draft_created(draft_id: str, title: str, **kwargs) -> None:
    """发布知识草稿创建事件."""
    bus = get_event_bus()
    await bus.publish(DomainEvent(
        event_type=KnowledgeEvents.DRAFT_CREATED,
        domain="knowledge",
        payload={"draft_id": draft_id, "title": title, **kwargs},
        source="knowledge",
    ))
