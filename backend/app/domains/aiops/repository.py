"""AIops domain repository."""
from app.common.repository import BaseRepository
from app.domains.aiops.models import AIAnalysis


class AIAnalysisRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, AIAnalysis)
