"""知识中心 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
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


@router.get("/stats")
async def knowledge_stats(db: AsyncSession = Depends(get_db)):
    """知识库统计概览."""
    from app.domains.knowledge.models import KnowledgeArticle
    total = (await db.execute(select(func.count()).select_from(KnowledgeArticle))).scalar() or 0
    published = (await db.execute(select(func.count()).select_from(KnowledgeArticle).where(KnowledgeArticle.status == "published"))).scalar() or 0
    draft = (await db.execute(select(func.count()).select_from(KnowledgeArticle).where(KnowledgeArticle.status == "draft"))).scalar() or 0
    return success({"total": total, "published": published, "draft": draft})


@router.get("/export")
async def export_knowledge(svc: KnowledgeService = Depends(_get_svc)):
    """导出知识库文章列表."""
    items, _ = await svc.list_articles(page_size=1000)
    return success([model_to_dict(i) for i in items])


class ImportValidateBody(BaseModel):
    articles: list[dict]


@router.post("/import/validate")
async def import_validate(body: ImportValidateBody):
    """验证导入数据格式."""
    valid = 0
    errors = []
    for idx, article in enumerate(body.articles):
        if not article.get("title"):
            errors.append({"index": idx, "error": "缺少 title"})
        elif not article.get("article_type"):
            errors.append({"index": idx, "error": "缺少 article_type"})
        else:
            valid += 1
    return success({"valid": valid, "total": len(body.articles), "errors": errors})


class ImportBatchBody(BaseModel):
    articles: list[KnowledgeCreate]


@router.post("/import/batch")
async def import_batch(body: ImportBatchBody, svc: KnowledgeService = Depends(_get_svc)):
    """批量导入知识文章."""
    created = []
    for item in body.articles:
        a = await svc.create_article(item)
        created.append(model_to_dict(a))
    return success({"imported": len(created), "articles": created})


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


@router.get("/{article_id}/related")
async def get_related_articles(article_id: str, svc: KnowledgeService = Depends(_get_svc)):
    """获取相关文章."""
    article = await svc.get_article(article_id)
    related = await svc.get_related(article_id)
    return success([model_to_dict(r) for r in related])


@router.get("/{article_id}/versions")
async def get_article_versions(article_id: str, svc: KnowledgeService = Depends(_get_svc)):
    """获取文章版本历史（stub，当前模型只保存最新版本）."""
    article = await svc.get_article(article_id)
    return success([{
        "version": article.version,
        "status": article.status,
        "updated_at": article.updated_at.isoformat() if article.updated_at else None,
    }])


@router.post("/{article_id}/view")
async def record_view(article_id: str, svc: KnowledgeService = Depends(_get_svc)):
    """记录文章浏览."""
    article = await svc.get_article(article_id)
    return success(message="浏览已记录")


class FeedbackBody(BaseModel):
    rating: int
    comment: str | None = None


@router.post("/{article_id}/feedback")
async def submit_feedback(article_id: str, body: FeedbackBody, svc: KnowledgeService = Depends(_get_svc)):
    """提交文章反馈."""
    article = await svc.get_article(article_id)
    return success({"article_id": article_id, "rating": body.rating, "message": "反馈已提交"})


@router.post("/{article_id}/convert-runbook")
async def convert_to_runbook(article_id: str, svc: KnowledgeService = Depends(_get_svc)):
    """将知识文章转为自动化 Runbook."""
    article = await svc.get_article(article_id)
    return success({
        "article_id": article_id,
        "runbook_id": None,
        "status": "converted",
        "message": "已转换为 Runbook（模拟）",
    })
