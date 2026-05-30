"""Log domain repository."""
from app.common.repository import BaseRepository
from app.domains.log.models import ExecutionLog


class ExecutionLogRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, ExecutionLog)
