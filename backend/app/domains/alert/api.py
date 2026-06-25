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


@rule_router.delete("/{rule_id}")
async def delete_rule(rule_id: str, svc: AlertService = Depends(_get_svc)):
    await svc.delete_rule(rule_id)
    return success(message="告警规则已删除")


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


@router.get("/{alert_id}/evidence-chain")
async def get_evidence_chain(alert_id: str, db: AsyncSession = Depends(get_db)):
    """获取告警的完整证据链（时间线聚合）."""
    import json as _json

    from app.domains.event.service import EventService
    from app.domains.aiops.models import AIAnalysis
    from app.domains.automation.models import Execution
    from app.domains.ticket.service import TicketService

    alert_svc = AlertService(db)
    alert = await alert_svc.get_alert(alert_id)

    timeline = []
    # 告警本身
    timeline.append({
        "time": alert.created_at.isoformat() if alert.created_at else None,
        "type": "alert_created",
        "severity": alert.severity,
        "title": alert.title,
        "data": {"alert_id": str(alert.id), "status": alert.status}
    })

    # 关联事件
    event_ids_raw = alert.event_ids
    if event_ids_raw:
        try:
            event_ids = _json.loads(event_ids_raw) if isinstance(event_ids_raw, str) else event_ids_raw
        except Exception:
            event_ids = []
        if event_ids:
            event_svc = EventService(db)
            for eid in event_ids:
                try:
                    event = await event_svc.get_event(eid)
                    timeline.append({
                        "time": event.created_at.isoformat() if event.created_at else None,
                        "type": "event",
                        "title": event.title,
                        "data": {"event_id": str(event.id), "event_type": event.event_type, "severity": event.severity}
                    })
                except Exception:
                    pass

    # 关联AI分析 — 直接按 alert_id 查询
    analyses_result = await db.execute(
        select(AIAnalysis).where(AIAnalysis.alert_id == alert_id).order_by(AIAnalysis.created_at)
    )
    for a in analyses_result.scalars().all():
        summary_text = a.summary or "N/A"
        timeline.append({
            "time": a.created_at.isoformat() if a.created_at else None,
            "type": "ai_analysis",
            "title": f"AI分析: {summary_text[:50]}",
            "data": {"analysis_id": str(a.id), "root_causes": a.root_causes, "recommendations": a.recommended_actions}
        })

    # 关联自动化执行 — 直接按 trigger_source_id 查询
    executions_result = await db.execute(
        select(Execution).where(Execution.trigger_source_id == alert_id).order_by(Execution.created_at)
    )
    for e in executions_result.scalars().all():
        timeline.append({
            "time": e.created_at.isoformat() if e.created_at else None,
            "type": "execution",
            "title": f"自动化执行: {e.execution_type}",
            "data": {"execution_id": str(e.id), "status": e.status, "is_dry_run": e.is_dry_run}
        })

    # 按时间排序
    timeline.sort(key=lambda x: x["time"] or "")

    # 关联工单
    ticket_info = None
    if alert.ticket_id:
        try:
            ticket_svc = TicketService(db)
            ticket = await ticket_svc.get_ticket(alert.ticket_id)
            ticket_info = {"ticket_id": str(ticket.id), "status": ticket.status, "title": ticket.title}
        except Exception:
            pass

    return success({
        "alert": {"id": str(alert.id), "title": alert.title, "severity": alert.severity, "status": alert.status},
        "timeline": timeline,
        "related_ticket": ticket_info
    })
