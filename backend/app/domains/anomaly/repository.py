"""异常检测 Repository."""

from __future__ import annotations

from app.common.repository import BaseRepository
from app.domains.anomaly.models import Anomaly


class AnomalyRepo(BaseRepository):
    """异常数据访问层."""

    def __init__(self, session):
        super().__init__(session, Anomaly)
