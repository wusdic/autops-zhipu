"""知识中心 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.response import paginate, success
from app.domains.knowledge.schemas import KnowledgeCreate, KnowledgeUpdate
from app.domains.knowledge.service import KnowledgeService
from app.infra.database import get_db

router = APIRouter(prefix="/knowledge", tags=["知识中心"])


def _get_svc(db: AsyncSession = Depends(get_db)) -> KnowledgeService:
    return KnowledgeService(db)


@router.get("")
async def list_articles(
    article_type: str | None = None, status: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    svc: KnowledgeService = Depends(_get_svc),
):
    items, total = await svc.list_articles(article_type, status, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@router.post("")
async def create_article(data: KnowledgeCreate, svc: KnowledgeService = Depends(_get_svc)):
    a = await svc.create_article(data)
    return success(model_to_dict(a))


@router.get("/{article_id}")
async def get_article(article_id: str, svc: KnowledgeService = Depends(_get_svc)):
    a = await svc.get_article(article_id)
    return success(model_to_dict(a))


@router.put("/{article_id}")
async def update_article(article_id: str, data: KnowledgeUpdate, svc: KnowledgeService = Depends(_get_svc)):
    a = await svc.update_article(article_id, data)
    return success(model_to_dict(a))


@router.post("/{article_id}/publish")
async def publish_article(article_id: str, svc: KnowledgeService = Depends(_get_svc)):
    a = await svc.publish_article(article_id)
    return success(model_to_dict(a))
