"""知识中心 Service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.common.repository import BaseRepository
from app.domains.knowledge.models import KnowledgeArticle
from app.domains.knowledge.schemas import KnowledgeCreate, KnowledgeUpdate


class KnowledgeService:
    """知识中心业务逻辑."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BaseRepository(session, KnowledgeArticle)

    async def create_article(self, data: KnowledgeCreate) -> KnowledgeArticle:
        article = await self.repo.create(**data.model_dump())
        await self.session.flush()
        await self.session.refresh(article)
        return article

    async def list_articles(
        self, article_type: str | None = None, status: str | None = None,
        page: int = 1, page_size: int = 20,
    ):
        stmt = select(KnowledgeArticle)
        count_stmt = select(func.count()).select_from(KnowledgeArticle)
        if article_type:
            stmt = stmt.where(KnowledgeArticle.article_type == article_type)
            count_stmt = count_stmt.where(KnowledgeArticle.article_type == article_type)
        if status:
            stmt = stmt.where(KnowledgeArticle.status == status)
            count_stmt = count_stmt.where(KnowledgeArticle.status == status)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0
        result = await self.session.execute(stmt.order_by(KnowledgeArticle.created_at.desc()).offset((page-1)*page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def get_article(self, article_id: str) -> KnowledgeArticle:
        a = await self.repo.get_by_id(article_id)
        if not a:
            raise NotFoundError(f"知识文章 {article_id} 不存在")
        return a

    async def delete_article(self, article_id: str) -> None:
        a = await self.get_article(article_id)
        await self.session.delete(a)
        await self.session.flush()

    async def update_article(self, article_id: str, data: KnowledgeUpdate) -> KnowledgeArticle:
        a = await self.get_article(article_id)
        update_data = data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            if v is not None:
                setattr(a, k, v)
        a.version += 1
        await self.session.flush()
        await self.session.refresh(a)
        return a

    async def publish_article(self, article_id: str, user_id: str | None = None) -> KnowledgeArticle:
        a = await self.get_article(article_id)
        a.status = "published"
        a.published_by = user_id
        a.published_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(a)
        return a

    async def get_related(self, article_id: str, limit: int = 5) -> list[KnowledgeArticle]:
        """获取相关文章（按类型和标签匹配）."""
        article = await self.get_article(article_id)
        stmt = select(KnowledgeArticle).where(
            KnowledgeArticle.id != article_id,
            KnowledgeArticle.status == "published",
            KnowledgeArticle.article_type == article.article_type,
        ).order_by(KnowledgeArticle.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
