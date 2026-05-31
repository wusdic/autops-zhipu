"""Governance domain repository."""
from app.common.repository import BaseRepository
from app.domains.governance.models import User, Role, ApiKey


class UserRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, User)

class RoleRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, Role)

class APIKeyRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, ApiKey)
