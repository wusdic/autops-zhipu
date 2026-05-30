"""状态中心 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.response import paginate, success
from app.domains.state.schemas import StateSnapshotCreate
from app.domains.state.service import StateService
from app.infra.database import get_db

router = APIRouter(prefix="/states", tags=["状态中心"])


def _get_svc(db: AsyncSession = Depends(get_db)) -> StateService:
    return StateService(db)


@router.post("/snapshots")
async def create_snapshot(data: StateSnapshotCreate, svc: StateService = Depends(_get_svc)):
    snap = await svc.record_snapshot(data)
    return success(model_to_dict(snap))


@router.get("/latest/{asset_id}")
async def get_latest_states(asset_id: str, svc: StateService = Depends(_get_svc)):
    items = await svc.get_latest_states(asset_id)
    return success([model_to_dict(i) for i in items])


@router.get("/changes/{asset_id}")
async def get_state_changes(
    asset_id: str, state_type: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    svc: StateService = Depends(_get_svc),
):
    items, total = await svc.get_changes(asset_id, state_type, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)
