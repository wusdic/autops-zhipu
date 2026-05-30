"""Config domain repository."""
from app.common.repository import BaseRepository
from app.domains.config.models import ConfigDefinition, ConfigVersion, ConfigBinding, Credential


class ConfigDefinitionRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, ConfigDefinition)

class ConfigVersionRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, ConfigVersion)

class ConfigBindingRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, ConfigBinding)

class CredentialRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, Credential)
