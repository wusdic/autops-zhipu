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
        changed = bool(latest and latest.status != data.status)
        old_status = latest.status if latest else None
        if changed:
            await self.change_repo.create(
                asset_id=data.asset_id,
                state_type=data.state_type,
                old_status=old_status,
                new_status=data.status,
                old_value=latest.value,
                new_value=data.value,
            )
        snap = await self.snap_repo.create(**data.model_dump())
        await self.session.flush()
        await self.session.refresh(snap)
        await self._publish_state_events(data, changed, old_status)
        return snap

    async def _publish_state_events(
        self, data: StateSnapshotCreate, changed: bool, old_status: str | None
    ) -> None:
        """发布状态领域事件（与快照同事务）.

        - 始终发 SNAPSHOT_RECORDED；
        - 状态变化时发 STATE_CHANGED；并按新状态补发 STATE_CRITICAL / STATE_RECOVERED，
          打通 状态→事件→告警→策略 链路（此前 API 直接写快照不触发任何下游）。
        """
        from app.common.events import DomainEvent, StateEvents, get_event_bus

        bus = get_event_bus()
        base = {
            "asset_id": data.asset_id,
            "state_type": data.state_type,
            "status": data.status,
            "value": data.value,
        }

        async def _pub(event_type: str, extra: dict | None = None) -> None:
            await bus.publish(
                DomainEvent(
                    domain="state",
                    event_type=event_type,
                    payload={**base, **(extra or {})},
                    source="state_service",
                ),
                session=self.session,
            )

        await _pub(StateEvents.SNAPSHOT_RECORDED)
        if changed:
            await _pub(StateEvents.STATE_CHANGED, {"old_status": old_status, "new_status": data.status})
            if data.status in ("critical", "offline"):
                await _pub(StateEvents.STATE_CRITICAL, {"new_status": data.status})
            elif data.status in ("normal", "online"):
                await _pub(StateEvents.STATE_RECOVERED, {"new_status": data.status})

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
