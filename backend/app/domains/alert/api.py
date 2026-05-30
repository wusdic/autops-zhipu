"""告警中心 Service + API."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.exceptions import NotFoundError
from app.common.repository import BaseRepository
from app.common.response import paginate, success
from app.infra.database import get_db
from app.domains.alert.models import Alert, AlertRule
from app.domains.alert.schemas import AlertRuleCreate, AlertCreateBody


class AlertService:
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


router = APIRouter(prefix="/alerts", tags=["告警中心"])
rule_router = APIRouter(prefix="/alert-rules", tags=["告警规则"])


def _get_svc(db: AsyncSession = Depends(get_db)) -> AlertService:
    return AlertService(db)


@rule_router.get("")
async def list_rules(enabled: bool | None = None, svc: AlertService = Depends(_get_svc)):
    items = await svc.list_rules(enabled)
    return success([model_to_dict(i) for i in items])


@rule_router.post("")
async def create_rule(data: AlertRuleCreate, svc: AlertService = Depends(_get_svc)):
    rule = await svc.create_rule(**data.model_dump())
    return success(model_to_dict(rule))


@router.get("")
async def list_alerts(
    status: str | None = None, severity: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    svc: AlertService = Depends(_get_svc),
):
    items, total = await svc.list_alerts(status, severity, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@router.get("/{alert_id}")
async def get_alert(alert_id: str, svc: AlertService = Depends(_get_svc)):
    alert = await svc.alert_repo.get_by_id(alert_id)
    if not alert:
        raise NotFoundError(f"告警 {alert_id} 不存在")
    return success(model_to_dict(alert))


@router.post("")
async def create_alert(
    data: AlertCreateBody,
    svc: AlertService = Depends(_get_svc),
):
    alert = await svc.create_alert(**data.model_dump())
    return success(model_to_dict(alert))


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, svc: AlertService = Depends(_get_svc)):
    alert = await svc.acknowledge(alert_id)
    return success(model_to_dict(alert))


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str, svc: AlertService = Depends(_get_svc)):
    alert = await svc.resolve(alert_id)
    return success(model_to_dict(alert))
