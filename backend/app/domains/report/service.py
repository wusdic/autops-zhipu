"""报告 Service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.common.repository import BaseRepository
from app.domains.report.models import ReportArchive, ReportTask, ReportTemplate
from app.domains.report.schemas import (
    ReportGenerateRequest,
    ReportTemplateCreate,
    ReportTemplateUpdate,
)


class ReportService:
    """报告业务逻辑."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.template_repo: BaseRepository = BaseRepository(session, ReportTemplate)
        self.task_repo: BaseRepository = BaseRepository(session, ReportTask)
        self.archive_repo: BaseRepository = BaseRepository(session, ReportArchive)

    # ---------------- Report Template ----------------

    async def list_templates(
        self,
        type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ReportTemplate], int]:
        stmt = select(ReportTemplate)
        count_stmt = select(func.count()).select_from(ReportTemplate)
        if type:
            stmt = stmt.where(ReportTemplate.type == type)
            count_stmt = count_stmt.where(ReportTemplate.type == type)
        total = (await self.session.execute(count_stmt)).scalar() or 0
        result = await self.session.execute(
            stmt.order_by(ReportTemplate.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def create_template(self, data: ReportTemplateCreate) -> ReportTemplate:
        obj = await self.template_repo.create(**data.model_dump())
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def get_template(self, template_id: str) -> ReportTemplate:
        t = await self.template_repo.get_by_id(template_id)
        if not t:
            raise NotFoundError(f"报告模板 {template_id} 不存在")
        return t

    async def update_template(
        self, template_id: str, data: ReportTemplateUpdate
    ) -> ReportTemplate:
        t = await self.get_template(template_id)
        update_data = data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(t, k, v)
        await self.session.flush()
        await self.session.refresh(t)
        return t

    async def delete_template(self, template_id: str) -> None:
        t = await self.get_template(template_id)
        await self.session.delete(t)
        await self.session.flush()

    # ---------------- Report Task ----------------

    async def list_tasks(
        self,
        status: str | None = None,
        template_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ReportTask], int]:
        stmt = select(ReportTask)
        count_stmt = select(func.count()).select_from(ReportTask)
        if status:
            stmt = stmt.where(ReportTask.status == status)
            count_stmt = count_stmt.where(ReportTask.status == status)
        if template_id:
            stmt = stmt.where(ReportTask.template_id == template_id)
            count_stmt = count_stmt.where(ReportTask.template_id == template_id)
        total = (await self.session.execute(count_stmt)).scalar() or 0
        result = await self.session.execute(
            stmt.order_by(ReportTask.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_task(self, task_id: str) -> ReportTask:
        t = await self.task_repo.get_by_id(task_id)
        if not t:
            raise NotFoundError(f"报告任务 {task_id} 不存在")
        return t

    async def generate_report(self, req: ReportGenerateRequest) -> ReportTask:
        """创建报告生成任务（stub：仅创建任务记录，后台实际生成待接入）."""
        # 校验模板存在
        await self.get_template(req.template_id)
        task = await self.task_repo.create(
            template_id=req.template_id,
            status="pending",
            triggered_by=req.triggered_by or "system",
        )
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def preview_task(self, task_id: str) -> dict:
        """返回任务的预览数据（stub）."""
        task = await self.get_task(task_id)
        template = await self.get_template(task.template_id)
        return {
            "task_id": str(task.id),
            "template_id": str(task.template_id),
            "template_name": template.name,
            "status": task.status,
            "sections": [
                {"title": "概览", "data": {}},
                {"title": "详情", "data": []},
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_task_download_info(self, task_id: str) -> dict:
        """返回下载信息（stub：未实际生成文件时返回占位信息）."""
        task = await self.get_task(task_id)
        return {
            "task_id": str(task.id),
            "status": task.status,
            "result_path": task.result_path,
            "download_url": f"/api/v1/report/tasks/{task.id}/file"
            if task.result_path
            else None,
        }

    # ---------------- Report Archive ----------------

    async def list_archives(
        self,
        task_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ReportArchive], int]:
        stmt = select(ReportArchive)
        count_stmt = select(func.count()).select_from(ReportArchive)
        if task_id:
            stmt = stmt.where(ReportArchive.task_id == task_id)
            count_stmt = count_stmt.where(ReportArchive.task_id == task_id)
        total = (await self.session.execute(count_stmt)).scalar() or 0
        result = await self.session.execute(
            stmt.order_by(ReportArchive.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_archive(self, archive_id: str) -> ReportArchive:
        a = await self.archive_repo.get_by_id(archive_id)
        if not a:
            raise NotFoundError(f"报告归档 {archive_id} 不存在")
        return a

    # ---------------- Stats ----------------

    async def stats(self) -> dict:
        """报告统计概览."""
        # 任务状态分布
        stmt = select(ReportTask.status, func.count(ReportTask.id)).group_by(
            ReportTask.status
        )
        result = await self.session.execute(stmt)
        status_counts = dict(result.all())
        total_tasks = sum(status_counts.values())

        # 模板总数
        tpl_total = (
            await self.session.execute(select(func.count()).select_from(ReportTemplate))
        ).scalar() or 0

        # 归档总数 & 总大小
        arch_stmt = select(
            func.count(ReportArchive.id), func.coalesce(func.sum(ReportArchive.file_size), 0)
        )
        arch_count, arch_size = (await self.session.execute(arch_stmt)).one()

        return {
            "templates": tpl_total,
            "tasks": {
                "total": total_tasks,
                "pending": status_counts.get("pending", 0),
                "running": status_counts.get("running", 0),
                "completed": status_counts.get("completed", 0),
                "failed": status_counts.get("failed", 0),
            },
            "archives": {
                "total": arch_count,
                "total_size": int(arch_size),
            },
        }
