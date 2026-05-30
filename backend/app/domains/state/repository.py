"""State domain repository."""
from app.common.repository import BaseRepository
from app.domains.state.models import StateSnapshot, StateChange


class StateSnapshotRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, StateSnapshot)

class StateChangeRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, StateChange)
