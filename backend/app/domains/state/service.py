"""状态中心 Service."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.repository import BaseRepository
from app.domains.state.models import StateChange, StateSnapshot
from app.domains.state.schemas import StateSnapshotCreate


class StateService:
    """状态中心业务逻辑."""

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
        count_stmt = select(func.count()).select_from(StateChange).where(
            StateChange.asset_id == asset_id
        )
        if state_type:
            stmt = stmt.where(StateChange.state_type == state_type)
            count_stmt = count_stmt.where(StateChange.state_type == state_type)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0
        result = await self.session.execute(stmt.order_by(StateChange.created_at.desc()).offset((page-1)*page_size).limit(page_size))
        return list(result.scalars().all()), total
