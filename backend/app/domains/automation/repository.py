"""Automation domain repository."""
from app.common.repository import BaseRepository
from app.domains.automation.models import Script, Playbook, Execution, ExecutionStep


class ScriptRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, Script)

class PlaybookRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, Playbook)

class ExecutionRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, Execution)

class ExecutionStepRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, ExecutionStep)
