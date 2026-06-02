"""巡检域 Service."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.domains.inspection.models import (
    InspectionPlan, InspectionReport, InspectionResult, InspectionTask,
    InspectionTemplate,
)
from app.domains.inspection.repository import (
    InspectionPlanRepository, InspectionReportRepository,
    InspectionResultRepository, InspectionTaskRepository,
    InspectionTemplateRepository,
)
from app.domains.inspection.schemas import (
    InspectionPlanCreate, InspectionPlanUpdate, InspectionTaskCreate,
    InspectionTemplateCreate, InspectionTemplateUpdate,
)


class InspectionService:
    """巡检业务逻辑."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.template_repo = InspectionTemplateRepository(session)
        self.plan_repo = InspectionPlanRepository(session)
        self.task_repo = InspectionTaskRepository(session)
        self.result_repo = InspectionResultRepository(session)
        self.report_repo = InspectionReportRepository(session)

    # --- 巡检模板 ---
    async def create_template(self, data: InspectionTemplateCreate) -> InspectionTemplate:
        template = await self.template_repo.create(**data.model_dump())
        await self.session.refresh(template)
        return template

    async def get_template(self, template_id: str) -> InspectionTemplate:
        template = await self.template_repo.get_by_id(template_id)
        if not template:
            raise NotFoundError(f"巡检模板 {template_id} 不存在")
        return template

    async def list_templates(
        self, *, page: int = 1, page_size: int = 20, search: str | None = None,
    ) -> tuple[list[InspectionTemplate], int]:
        filters = []
        if search:
            filters.append(InspectionTemplate.name.ilike(f"%{search}%"))
        return await self.template_repo.get_multi(
            page=page, page_size=page_size, filters=filters or None,
            order_by=InspectionTemplate.created_at.desc(),
        )

    async def update_template(
        self, template_id: str, data: InspectionTemplateUpdate,
    ) -> InspectionTemplate:
        updates = data.model_dump(exclude_unset=True, exclude_none=True)
        template = await self.template_repo.update(template_id, **updates)
        await self.session.refresh(template)
        return template

    async def delete_template(self, template_id: str) -> None:
        await self.template_repo.delete(template_id)

    # --- 巡检计划 ---
    async def create_plan(self, data: InspectionPlanCreate) -> InspectionPlan:
        # 校验模板存在
        await self.get_template(data.template_id)
        plan = await self.plan_repo.create(**data.model_dump())
        await self.session.refresh(plan)
        return plan

    async def get_plan(self, plan_id: str) -> InspectionPlan:
        plan = await self.plan_repo.get_by_id(plan_id)
        if not plan:
            raise NotFoundError(f"巡检计划 {plan_id} 不存在")
        return plan

    async def list_plans(
        self, *, page: int = 1, page_size: int = 20,
    ) -> tuple[list[InspectionPlan], int]:
        return await self.plan_repo.get_multi(
            page=page, page_size=page_size,
            order_by=InspectionPlan.created_at.desc(),
        )

    async def update_plan(
        self, plan_id: str, data: InspectionPlanUpdate,
    ) -> InspectionPlan:
        updates = data.model_dump(exclude_unset=True, exclude_none=True)
        if "template_id" in updates:
            await self.get_template(updates["template_id"])
        plan = await self.plan_repo.update(plan_id, **updates)
        await self.session.refresh(plan)
        return plan

    async def delete_plan(self, plan_id: str) -> None:
        await self.plan_repo.delete(plan_id)

    # --- 巡检任务 ---
    async def trigger_task(self, data: InspectionTaskCreate) -> InspectionTask:
        """触发一次巡检任务."""
        await self.get_template(data.template_id)
        task = await self.task_repo.create(
            template_id=data.template_id,
            plan_id=data.plan_id,
            status="pending",
        )
        await self.session.refresh(task)
        return task

    async def get_task(self, task_id: str) -> InspectionTask:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise NotFoundError(f"巡检任务 {task_id} 不存在")
        return task

    async def list_tasks(
        self, *, page: int = 1, page_size: int = 20,
        status: str | None = None, plan_id: str | None = None,
    ) -> tuple[list[InspectionTask], int]:
        filters = []
        if status:
            filters.append(InspectionTask.status == status)
        if plan_id:
            filters.append(InspectionTask.plan_id == plan_id)
        return await self.task_repo.get_multi(
            page=page, page_size=page_size, filters=filters or None,
            order_by=InspectionTask.created_at.desc(),
        )

    # --- 巡检结果 ---
    async def list_results(
        self, *, page: int = 1, page_size: int = 20,
        task_id: str | None = None, asset_id: str | None = None,
        status: str | None = None,
    ) -> tuple[list[InspectionResult], int]:
        filters = []
        if task_id:
            filters.append(InspectionResult.task_id == task_id)
        if asset_id:
            filters.append(InspectionResult.asset_id == asset_id)
        if status:
            filters.append(InspectionResult.status == status)
        return await self.result_repo.get_multi(
            page=page, page_size=page_size, filters=filters or None,
            order_by=InspectionResult.created_at.desc(),
        )

    async def get_result(self, result_id: str) -> InspectionResult:
        result = await self.result_repo.get_by_id(result_id)
        if not result:
            raise NotFoundError(f"巡检结果 {result_id} 不存在")
        return result

    # --- 巡检报告 ---
    async def list_reports(
        self, *, page: int = 1, page_size: int = 20, task_id: str | None = None,
    ) -> tuple[list[InspectionReport], int]:
        filters = []
        if task_id:
            filters.append(InspectionReport.task_id == task_id)
        return await self.report_repo.get_multi(
            page=page, page_size=page_size, filters=filters or None,
            order_by=InspectionReport.created_at.desc(),
        )

    async def get_report(self, report_id: str) -> InspectionReport:
        report = await self.report_repo.get_by_id(report_id)
        if not report:
            raise NotFoundError(f"巡检报告 {report_id} 不存在")
        return report

    # --- 统计 ---
    async def get_stats(self) -> dict:
        """巡检总览统计."""
        # 任务总数 / 各状态
        total_tasks = await self._count(InspectionTask)
        running_tasks = await self._count(InspectionTask, InspectionTask.status == "running")
        completed_tasks = await self._count(InspectionTask, InspectionTask.status == "completed")
        failed_tasks = await self._count(InspectionTask, InspectionTask.status == "failed")
        pending_tasks = await self._count(InspectionTask, InspectionTask.status == "pending")

        # 模板 / 计划
        total_templates = await self._count(InspectionTemplate)
        total_plans = await self._count(InspectionPlan)
        enabled_plans = await self._count(InspectionPlan, InspectionPlan.enabled == True)  # noqa: E712

        # 结果
        total_results = await self._count(InspectionResult)
        pass_results = await self._count(InspectionResult, InspectionResult.status == "pass")
        fail_results = await self._count(InspectionResult, InspectionResult.status == "fail")
        warning_results = await self._count(InspectionResult, InspectionResult.status == "warning")

        return {
            "tasks": {
                "total": total_tasks,
                "pending": pending_tasks,
                "running": running_tasks,
                "completed": completed_tasks,
                "failed": failed_tasks,
            },
            "templates": {"total": total_templates},
            "plans": {"total": total_plans, "enabled": enabled_plans},
            "results": {
                "total": total_results,
                "pass": pass_results,
                "fail": fail_results,
                "warning": warning_results,
            },
        }

    async def _count(self, model, *filters) -> int:
        q = select(func.count()).select_from(model)
        for f in filters:
            q = q.where(f)
        result = await self.session.execute(q)
        return result.scalar() or 0
