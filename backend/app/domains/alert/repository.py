"""Alert domain repository."""
from app.common.repository import BaseRepository
from app.domains.alert.models import Alert, AlertRule


class AlertRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, Alert)

class AlertRuleRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, AlertRule)
