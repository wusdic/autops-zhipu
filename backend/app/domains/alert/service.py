"""告警中心 Service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.common.repository import BaseRepository
from app.domains.alert.models import Alert, AlertRule


class AlertService:
    """告警业务逻辑."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.alert_repo = BaseRepository(session, Alert)
        self.rule_repo = BaseRepository(session, AlertRule)

    # --- Rules ---
    async def create_rule(self, **kwargs) -> AlertRule:
        rule = await self.rule_repo.create(**kwargs)
        await self.session.flush()
        await self.session.refresh(rule)
        return rule

    async def list_rules(self, enabled: bool | None = None):
        stmt = select(AlertRule)
        if enabled is not None:
            stmt = stmt.where(AlertRule.enabled == enabled)
        result = await self.session.execute(stmt.order_by(AlertRule.created_at.desc()))
        return list(result.scalars().all())

    # --- Alerts ---
    async def create_alert(self, title: str, severity: str, **kwargs) -> Alert:
        alert = await self.alert_repo.create(title=title, severity=severity, **kwargs)
        await self.session.flush()
        await self.session.refresh(alert)
        return alert

    async def list_alerts(
        self, status: str | None = None, severity: str | None = None,
        page: int = 1, page_size: int = 20,
    ):
        stmt = select(Alert)
        count_stmt = select(func.count()).select_from(Alert)
        if status:
            stmt = stmt.where(Alert.status == status)
            count_stmt = count_stmt.where(Alert.status == status)
        if severity:
            stmt = stmt.where(Alert.severity == severity)
            count_stmt = count_stmt.where(Alert.severity == severity)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0
        result = await self.session.execute(stmt.order_by(Alert.created_at.desc()).offset((page-1)*page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def get_alert(self, alert_id: str) -> Alert:
        alert = await self.alert_repo.get_by_id(alert_id)
        if not alert:
            raise NotFoundError(f"告警 {alert_id} 不存在")
        return alert

    async def acknowledge(self, alert_id: str, user_id: str | None = None) -> Alert:
        alert = await self.alert_repo.get_by_id(alert_id)
        if not alert:
            raise NotFoundError(f"告警 {alert_id} 不存在")
        alert.status = "acknowledged"
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(alert)
        return alert

    async def resolve(self, alert_id: str, user_id: str | None = None) -> Alert:
        alert = await self.alert_repo.get_by_id(alert_id)
        if not alert:
            raise NotFoundError(f"告警 {alert_id} 不存在")
        alert.status = "resolved"
        alert.resolved_by = user_id
        alert.resolved_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(alert)
        return alert
