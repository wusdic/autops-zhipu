"""巡检域 Repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.repository import BaseRepository
from app.domains.inspection.models import (
    InspectionPlan, InspectionReport, InspectionResult, InspectionTask,
    InspectionTemplate,
)


class InspectionTemplateRepository(BaseRepository[InspectionTemplate]):
    """巡检模板数据访问."""

    def __init__(self, session: AsyncSession):
        super().__init__(InspectionTemplate, session)


class InspectionPlanRepository(BaseRepository[InspectionPlan]):
    """巡检计划数据访问."""

    def __init__(self, session: AsyncSession):
        super().__init__(InspectionPlan, session)


class InspectionTaskRepository(BaseRepository[InspectionTask]):
    """巡检任务数据访问."""

    def __init__(self, session: AsyncSession):
        super().__init__(InspectionTask, session)

    async def get_by_plan(self, plan_id: str) -> list[InspectionTask]:
        q = (
            select(InspectionTask)
            .where(InspectionTask.plan_id == plan_id)
            .order_by(InspectionTask.created_at.desc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())


class InspectionResultRepository(BaseRepository[InspectionResult]):
    """巡检结果数据访问."""

    def __init__(self, session: AsyncSession):
        super().__init__(InspectionResult, session)

    async def get_by_task(self, task_id: str) -> list[InspectionResult]:
        q = (
            select(InspectionResult)
            .where(InspectionResult.task_id == task_id)
            .order_by(InspectionResult.created_at.desc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())


class InspectionReportRepository(BaseRepository[InspectionReport]):
    """巡检报告数据访问."""

    def __init__(self, session: AsyncSession):
        super().__init__(InspectionReport, session)

    async def get_by_task(self, task_id: str) -> InspectionReport | None:
        q = (
            select(InspectionReport)
            .where(InspectionReport.task_id == task_id)
            .order_by(InspectionReport.created_at.desc())
        )
        result = await self.session.execute(q)
        return result.scalars().first()
