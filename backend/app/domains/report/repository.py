"""报告 domain repository."""

from __future__ import annotations

from app.common.repository import BaseRepository
from app.domains.report.models import ReportArchive, ReportTask, ReportTemplate


class ReportTemplateRepo(BaseRepository):
    def __init__(self, session):
        super().__init__(session, ReportTemplate)


class ReportTaskRepo(BaseRepository):
    def __init__(self, session):
        super().__init__(session, ReportTask)


class ReportArchiveRepo(BaseRepository):
    def __init__(self, session):
        super().__init__(session, ReportArchive)
