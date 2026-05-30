"""Event domain repository."""
from app.common.repository import BaseRepository
from app.domains.event.models import Event


class EventRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, Event)
