"""资产发现 API."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import paginate, success
from app.infra.database import get_db
from app.domains.asset.discovery_schemas import DiscoveryTaskCreate
from app.domains.asset.discovery_service import DiscoveryService

router = APIRouter(prefix="/discovery", tags=["资产发现"])


def _get_svc(db: AsyncSession = Depends(get_db)) -> DiscoveryService:
    return DiscoveryService(db)


@router.post("/tasks")
async def create_discovery_task(data: DiscoveryTaskCreate, svc: DiscoveryService = Depends(_get_svc)):
    task = await svc.create_task(data.model_dump())
    return success(task)


@router.get("/tasks")
async def list_discovery_tasks(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    svc: DiscoveryService = Depends(_get_svc),
):
    items, total = await svc.list_tasks(page, page_size)
    return paginate(items, total, page, page_size)


@router.get("/results")
async def get_discovery_results(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    svc: DiscoveryService = Depends(_get_svc),
):
    items, total = await svc.get_results(page, page_size)
    return paginate(items, total, page, page_size)
