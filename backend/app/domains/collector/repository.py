"""Collector domain repository."""
from app.common.repository import BaseRepository
from app.domains.collector.models import Collector, CollectionJob, CollectionResult


class CollectorRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, Collector)

class CollectionJobRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, CollectionJob)

class CollectionResultRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, CollectionResult)
