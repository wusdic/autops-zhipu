"""Policy domain repository."""
from app.common.repository import BaseRepository
from app.domains.policy.models import Policy, PolicyVersion


class PolicyRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, Policy)

class PolicyVersionRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, PolicyVersion)
