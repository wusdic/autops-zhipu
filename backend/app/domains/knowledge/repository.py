"""Knowledge domain repository."""
from app.common.repository import BaseRepository
from app.domains.knowledge.models import KnowledgeArticle


class KnowledgeArticleRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, KnowledgeArticle)
