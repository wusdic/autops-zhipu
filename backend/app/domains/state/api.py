"""状态中心 Service + API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.repository import BaseRepository
from app.common.response import paginate, success
from app.infra.database import get_db
from app.domains.state.models import StateSnapshot, StateChange
from app.domains.state.schemas import StateSnapshotCreate


class StateService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.snap_repo = BaseRepository(session, StateSnapshot)
        self.change_repo = BaseRepository(session, StateChange)

    async def record_snapshot(self, data: StateSnapshotCreate) -> StateSnapshot:
        # Check if status changed
        latest = await self._get_latest(data.asset_id, data.state_type)
        if latest and latest.status != data.status:
            await self.change_repo.create(
                asset_id=data.asset_id,
                state_type=data.state_type,
                old_status=latest.status,
                new_status=data.status,
                old_value=latest.value,
                new_value=data.value,
            )
        snap = await self.snap_repo.create(**data.model_dump())
        await self.session.flush()
        await self.session.refresh(snap)
        return snap

    async def _get_latest(self, asset_id: str, state_type: str):
        result = await self.session.execute(
            select(StateSnapshot)
            .where(StateSnapshot.asset_id == asset_id, StateSnapshot.state_type == state_type)
            .order_by(StateSnapshot.collected_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_states(self, asset_id: str):
        result = await self.session.execute(
            select(StateSnapshot)
            .where(StateSnapshot.asset_id == asset_id)
            .order_by(StateSnapshot.collected_at.desc())
        )
        seen = set()
        items = []
        for snap in result.scalars().all():
            if snap.state_type not in seen:
                seen.add(snap.state_type)
                items.append(snap)
        return items

    async def get_changes(self, asset_id: str, state_type: str | None = None, page: int = 1, page_size: int = 20):
        stmt = select(StateChange).where(StateChange.asset_id == asset_id)
        if state_type:
            stmt = stmt.where(StateChange.state_type == state_type)
        total_result = await self.session.execute(
            select(func.count()).select_from(StateChange).where(StateChange.asset_id == asset_id)
        )
        total = total_result.scalar() or 0
        result = await self.session.execute(stmt.order_by(StateChange.created_at.desc()).offset((page-1)*page_size).limit(page_size))
        return list(result.scalars().all()), total


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
