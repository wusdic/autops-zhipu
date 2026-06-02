"""异常检测 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.response import paginate, success
from app.domains.anomaly.schemas import (
    AnomalyCreate,
    AnomalyUpdate,
    AssignBody,
    ConvertTicketBody,
    EscalateBody,
)
from app.domains.anomaly.service import AnomalyService
from app.infra.database import get_db

router = APIRouter(prefix="/anomalies", tags=["异常检测"])


def _get_svc(db: AsyncSession = Depends(get_db)) -> AnomalyService:
    return AnomalyService(db)


def _to_dict(anomaly) -> dict:
    """Convert model -> response dict with `metadata` key."""
    d = model_to_dict(anomaly)
    # Rename `meta` (DB column) -> `metadata` for API surface
    d["metadata"] = d.pop("meta", None)
    return d


# ----------------------------------------------------------------------
# Stats endpoint (declared before {id} routes to avoid path conflicts)
# ----------------------------------------------------------------------
@router.get("/stats")
async def anomaly_stats(svc: AnomalyService = Depends(_get_svc)):
    """异常统计：按状态、严重程度分组."""
    result = await svc.stats()
    return success(result)


# ----------------------------------------------------------------------
# CRUD
# ----------------------------------------------------------------------
@router.get("")
async def list_anomalies(
    status: str | None = None,
    severity: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: AnomalyService = Depends(_get_svc),
):
    items, total = await svc.list_anomalies(status, severity, page, page_size)
    return paginate([_to_dict(i) for i in items], total, page, page_size)


@router.post("")
async def create_anomaly(
    data: AnomalyCreate,
    svc: AnomalyService = Depends(_get_svc),
):
    payload = data.model_dump(by_alias=True, exclude_unset=False)
    anomaly = await svc.create_anomaly(**payload)
    return success(_to_dict(anomaly))


@router.get("/{anomaly_id}")
async def get_anomaly(anomaly_id: str, svc: AnomalyService = Depends(_get_svc)):
    anomaly = await svc.get_anomaly(anomaly_id)
    return success(_to_dict(anomaly))


@router.put("/{anomaly_id}")
async def update_anomaly(
    anomaly_id: str,
    data: AnomalyUpdate,
    svc: AnomalyService = Depends(_get_svc),
):
    payload = data.model_dump(by_alias=True, exclude_unset=True)
    anomaly = await svc.update_anomaly(anomaly_id, **payload)
    return success(_to_dict(anomaly))


@router.delete("/{anomaly_id}")
async def delete_anomaly(anomaly_id: str, svc: AnomalyService = Depends(_get_svc)):
    await svc.delete_anomaly(anomaly_id)
    return success({"id": anomaly_id, "deleted": True})


# ----------------------------------------------------------------------
# Lifecycle endpoints
# ----------------------------------------------------------------------
@router.post("/{anomaly_id}/acknowledge")
async def acknowledge_anomaly(
    anomaly_id: str, svc: AnomalyService = Depends(_get_svc)
):
    anomaly = await svc.acknowledge(anomaly_id)
    return success(_to_dict(anomaly))


@router.post("/{anomaly_id}/assign")
async def assign_anomaly(
    anomaly_id: str,
    body: AssignBody,
    svc: AnomalyService = Depends(_get_svc),
):
    anomaly = await svc.assign(anomaly_id, body.assignee_id)
    return success(_to_dict(anomaly))


@router.post("/{anomaly_id}/close")
async def close_anomaly(anomaly_id: str, svc: AnomalyService = Depends(_get_svc)):
    anomaly = await svc.close(anomaly_id)
    return success(_to_dict(anomaly))


@router.post("/{anomaly_id}/escalate")
async def escalate_anomaly(
    anomaly_id: str,
    body: EscalateBody,
    svc: AnomalyService = Depends(_get_svc),
):
    anomaly = await svc.escalate(
        anomaly_id, body.target_severity, body.reason
    )
    return success(_to_dict(anomaly))


@router.post("/{anomaly_id}/convert-ticket")
async def convert_to_ticket(
    anomaly_id: str,
    body: ConvertTicketBody,
    svc: AnomalyService = Depends(_get_svc),
):
    result = await svc.convert_to_ticket(
        anomaly_id, body.title, body.description, body.priority
    )
    return success(result)


@router.get("/{anomaly_id}/impact-analysis")
async def impact_analysis(
    anomaly_id: str, svc: AnomalyService = Depends(_get_svc)
):
    result = await svc.impact_analysis(anomaly_id)
    return success(result)
