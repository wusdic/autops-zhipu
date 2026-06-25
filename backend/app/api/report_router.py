"""报告中心 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.exceptions import NotFoundError
from app.common.response import paginate, success
from app.domains.report.schemas import (
    ReportGenerateRequest,
    ReportTemplateCreate,
    ReportTemplateUpdate,
)
from app.domains.report.service import ReportService
from app.infra.database import get_db

router = APIRouter(prefix="/report", tags=["报告中心"])


def _get_svc(db: AsyncSession = Depends(get_db)) -> ReportService:
    return ReportService(db)


# -------------------- Templates --------------------

@router.get("/templates")
async def list_templates(
    type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: ReportService = Depends(_get_svc),
):
    items, total = await svc.list_templates(type, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@router.post("/templates")
async def create_template(
    data: ReportTemplateCreate,
    svc: ReportService = Depends(_get_svc),
):
    t = await svc.create_template(data)
    return success(model_to_dict(t))


@router.get("/templates/{template_id}")
async def get_template(template_id: str, svc: ReportService = Depends(_get_svc)):
    t = await svc.get_template(template_id)
    return success(model_to_dict(t))


@router.put("/templates/{template_id}")
async def update_template(
    template_id: str,
    data: ReportTemplateUpdate,
    svc: ReportService = Depends(_get_svc),
):
    t = await svc.update_template(template_id, data)
    return success(model_to_dict(t))


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, svc: ReportService = Depends(_get_svc)):
    await svc.delete_template(template_id)
    return success({"deleted": template_id})


# -------------------- Generate --------------------

@router.post("/generate")
async def generate_report(
    body: ReportGenerateRequest,
    svc: ReportService = Depends(_get_svc),
):
    """生成报告（创建任务并后台渲染）."""
    task = await svc.generate_report(body)
    await svc.session.commit()
    from app.domains.report.generator import launch_report_build

    launch_report_build(str(task.id))
    return success(model_to_dict(task))


# -------------------- Tasks --------------------

@router.get("/tasks")
async def list_tasks(
    status: str | None = None,
    template_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: ReportService = Depends(_get_svc),
):
    items, total = await svc.list_tasks(status, template_id, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@router.get("/tasks/{task_id}")
async def get_task(task_id: str, svc: ReportService = Depends(_get_svc)):
    t = await svc.get_task(task_id)
    return success(model_to_dict(t))


@router.get("/tasks/{task_id}/preview")
async def preview_task(task_id: str, svc: ReportService = Depends(_get_svc)):
    """预览报告内容（stub）."""
    data = await svc.preview_task(task_id)
    return success(data)


@router.get("/tasks/{task_id}/download")
async def download_task(task_id: str, svc: ReportService = Depends(_get_svc)):
    """下载报告文件：若已生成则 FileResponse，否则返回占位信息."""
    info = await svc.get_task_download_info(task_id)
    if info.get("result_path"):
        import os

        path = info["result_path"]
        if os.path.exists(path):
            return FileResponse(
                path,
                media_type="application/octet-stream",
                filename=os.path.basename(path),
            )
        raise NotFoundError("报告文件不存在于存储路径")
    # Stub：未实际生成文件时返回下载元信息
    return success(info)


# -------------------- Archive --------------------

@router.get("/archive")
async def list_archives(
    task_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: ReportService = Depends(_get_svc),
):
    items, total = await svc.list_archives(task_id, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@router.get("/archive/{archive_id}")
async def get_archive(archive_id: str, svc: ReportService = Depends(_get_svc)):
    a = await svc.get_archive(archive_id)
    return success(model_to_dict(a))


# -------------------- Stats --------------------

@router.get("/stats")
async def report_stats(svc: ReportService = Depends(_get_svc)):
    """报告统计概览."""
    return success(await svc.stats())
