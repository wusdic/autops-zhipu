"""知识中心领域事件处理器."""
from __future__ import annotations

import logging

from app.common.events import (
    DomainEvent,
    get_event_bus,
    TicketEvents,
    AIOpsEvents,
    KnowledgeEvents,
)

logger = logging.getLogger(__name__)


async def on_ticket_closed_generate_draft(event: DomainEvent) -> None:
    """工单关闭时生成知识草稿."""
    payload = event.payload
    try:
        ticket_id = payload.get("ticket_id", "")
        title = payload.get("title", "未知工单")
        if not ticket_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.knowledge.service import KnowledgeService

        draft_id = None
        async with async_session_factory() as session:
            svc = KnowledgeService(session)
            draft = await svc.create_draft(
                title=f"工单总结: {title}",
                article_type="incident_summary",
                source="ticket_closure",
                source_id=ticket_id,
                context=payload.get("context", {}),
            )
            draft_id = str(getattr(draft, "id", ""))
            await session.commit()

        if draft_id:
            bus = get_event_bus()
            await bus.publish(DomainEvent(
                event_type=KnowledgeEvents.DRAFT_CREATED,
                domain="knowledge",
                payload={
                    "draft_id": draft_id,
                    "title": f"工单总结: {title}",
                    "source": "ticket_closure",
                    "ticket_id": ticket_id,
                },
                source="knowledge_handler",
                correlation_id=event.event_id,
            ))
        logger.info(
            "knowledge: 工单关闭生成知识草稿 ticket_id=%s draft_id=%s",
            ticket_id, draft_id,
        )
    except Exception as e:
        logger.error("knowledge: 工单关闭生成知识草稿失败: %s", e)


async def on_aiops_analysis_completed_recommend(event: DomainEvent) -> None:
    """AI分析完成时推荐相关知识."""
    payload = event.payload
    try:
        analysis_id = payload.get("analysis_id", "")
        result = payload.get("result", "")
        if not analysis_id:
            return

        from app.infra.database import async_session_factory
        from app.domains.knowledge.service import KnowledgeService

        async with async_session_factory() as session:
            svc = KnowledgeService(session)
            # 根据分析结果搜索相关知识文章
            search_keywords = payload.get("keywords", [])
            if not search_keywords and isinstance(result, str):
                search_keywords = result.split()[:5]
            recommended = await svc.search_articles(
                keywords=search_keywords,
                limit=5,
            )
            if recommended:
                article_ids = [str(getattr(a, "id", "")) for a in recommended]
                logger.info(
                    "knowledge: AI分析完成推荐知识 analysis_id=%s articles=%s",
                    analysis_id, article_ids,
                )
            else:
                logger.debug("knowledge: AI分析完成但未找到相关知识 analysis_id=%s", analysis_id)
            await session.commit()
    except Exception as e:
        logger.error("knowledge: AI分析完成推荐知识失败: %s", e)


async def on_ticket_converted_link_knowledge(event: DomainEvent) -> None:
    """工单转知识时关联."""
    payload = event.payload
    try:
        ticket_id = payload.get("ticket_id", "")
        article_id = payload.get("article_id", "")
        if ticket_id and article_id:
            logger.info(
                "knowledge: 工单转知识关联 ticket_id=%s article_id=%s",
                ticket_id, article_id,
            )
    except Exception as e:
        logger.error("knowledge: 工单转知识关联处理失败: %s", e)


def register_handlers() -> None:
    """注册知识领域的事件处理器."""
    bus = get_event_bus()
    bus.subscribe(TicketEvents.TICKET_CLOSED, on_ticket_closed_generate_draft)
    bus.subscribe(AIOpsEvents.ANALYSIS_COMPLETED, on_aiops_analysis_completed_recommend)
    bus.subscribe(TicketEvents.TICKET_CONVERTED_TO_KNOWLEDGE, on_ticket_converted_link_knowledge)
    logger.info("knowledge领域事件处理器已注册 (3个handler)")
