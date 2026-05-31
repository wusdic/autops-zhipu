"""告警中心 API."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.exceptions import NotFoundError
from app.common.response import paginate, success
from app.domains.alert.schemas import AlertRuleCreate, AlertCreateBody
from app.domains.alert.service import AlertService
from app.infra.database import get_db

router = APIRouter(prefix="/alerts", tags=["告警中心"])
rule_router = APIRouter(prefix="/alert-rules", tags=["告警规则"])


class AlertRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    event_types: str | None = None
    conditions: str | None = None
    severity: str | None = None
    suppress_duration: int | None = None
    enabled: bool | None = None


class AlertRulePatch(BaseModel):
    enabled: bool | None = None
    severity: str | None = None
    suppress_duration: int | None = None


class AlertEscalateBody(BaseModel):
    escalate_to: str | None = None
    reason: str | None = None


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


@rule_router.put("/{rule_id}")
async def update_rule(rule_id: str, data: AlertRuleUpdate, svc: AlertService = Depends(_get_svc)):
    rule = await svc.update_rule(rule_id, **data.model_dump(exclude_unset=True))
    return success(model_to_dict(rule))


@rule_router.patch("/{rule_id}")
async def patch_rule(rule_id: str, data: AlertRulePatch, svc: AlertService = Depends(_get_svc)):
    rule = await svc.update_rule(rule_id, **data.model_dump(exclude_unset=True))
    return success(model_to_dict(rule))


@rule_router.post("/{rule_id}/test")
async def test_rule(rule_id: str, svc: AlertService = Depends(_get_svc)):
    """测试告警规则（模拟触发）."""
    result = await svc.test_rule(rule_id)
    return success(result)


@router.get("")
async def list_alerts(
    status: str | None = None, severity: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    svc: AlertService = Depends(_get_svc),
):
    items, total = await svc.list_alerts(status, severity, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@router.get("/stats/overview")
async def alert_stats(db: AsyncSession = Depends(get_db)):
    """告警统计概览."""
    from sqlalchemy import func
    from app.domains.alert.models import Alert

    total = (await db.execute(select(func.count()).select_from(Alert))).scalar() or 0
    firing = (await db.execute(select(func.count()).select_from(Alert).where(Alert.status == "firing"))).scalar() or 0
    acknowledged = (await db.execute(select(func.count()).select_from(Alert).where(Alert.status == "acknowledged"))).scalar() or 0
    resolved = (await db.execute(select(func.count()).select_from(Alert).where(Alert.status == "resolved"))).scalar() or 0
    return success({"total": total, "firing": firing, "acknowledged": acknowledged, "resolved": resolved})


@router.get("/{alert_id}")
async def get_alert(alert_id: str, svc: AlertService = Depends(_get_svc)):
    alert = await svc.get_alert(alert_id)
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


@router.post("/{alert_id}/escalate")
async def escalate_alert(
    alert_id: str, body: AlertEscalateBody, svc: AlertService = Depends(_get_svc)
):
    """升级告警."""
    alert = await svc.escalate(alert_id, body.escalate_to, body.reason)
    return success(model_to_dict(alert))
