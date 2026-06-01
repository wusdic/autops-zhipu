"""资产发现 API."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import paginate, success, error
from app.infra.database import get_db
from app.domains.asset.discovery_schemas import (
    DiscoveryTaskCreate,
    DiscoveryOnboardRequest,
)
from app.domains.asset.discovery_service import DiscoveryService

router = APIRouter(prefix="/discovery", tags=["资产发现"])


def _get_svc(db: AsyncSession = Depends(get_db)) -> DiscoveryService:
    return DiscoveryService(db)


@router.post("/tasks")
async def create_discovery_task(data: DiscoveryTaskCreate, svc: DiscoveryService = Depends(_get_svc)):
    """创建发现任务."""
    task = await svc.create_task(data.model_dump())
    return success(task)


@router.post("/tasks/{task_id}/start")
async def start_discovery_task(task_id: str, svc: DiscoveryService = Depends(_get_svc)):
    """启动发现任务 - 开始真实扫描."""
    result = await svc.start_task(task_id)
    if "error" in result:
        return error(result["error"])
    return success(result)


@router.get("/tasks/{task_id}")
async def get_discovery_task(task_id: str, svc: DiscoveryService = Depends(_get_svc)):
    """获取任务详情."""
    task = await svc.get_task(task_id)
    if not task:
        return error("任务不存在", 404)
    return success(task)


@router.get("/tasks")
async def list_discovery_tasks(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    svc: DiscoveryService = Depends(_get_svc),
):
    """列出发现任务."""
    items, total = await svc.list_tasks(page, page_size)
    return paginate(items, total, page, page_size)


@router.get("/results")
async def get_discovery_results(
    task_id: str | None = Query(None),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    svc: DiscoveryService = Depends(_get_svc),
):
    """获取发现结果."""
    items, total = await svc.get_results(task_id, page, page_size)
    return paginate(items, total, page, page_size)


@router.post("/onboard")
async def onboard_discovered_assets(
    data: DiscoveryOnboardRequest,
    svc: DiscoveryService = Depends(_get_svc),
):
    """纳管发现的资产."""
    try:
        if not data.result_ids:
            # 纳管所有discovered状态的结果
            from sqlalchemy import select
            from app.domains.asset.discovery_models import DiscoveryResult
            result = await svc.db.execute(
                select(DiscoveryResult).where(DiscoveryResult.status == "discovered")
            )
            data.result_ids = [str(r.id) for r in result.scalars().all()]

        result = await svc.onboard_results(data.result_ids, data.asset_type)
        await svc.db.commit()
        return success(result)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Onboard error: {e}", exc_info=True)
        return error(str(e))


@router.post("/import")
async def import_asset(
    data: dict,
    svc: DiscoveryService = Depends(_get_svc),
):
    """手动导入资产."""
    try:
        asset = await svc.import_asset(data)
        from app.common.crud_service import model_to_dict
        return success(model_to_dict(asset))
    except ValueError as e:
        return error(str(e))
