"""策略中心 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.response import paginate, success
from app.domains.policy.schemas import PolicyCreate, PolicySimulate
from app.domains.policy.service import PolicyService
from app.infra.database import get_db

router = APIRouter(prefix="/policies", tags=["策略中心"])


def _get_svc(db: AsyncSession = Depends(get_db)) -> PolicyService:
    return PolicyService(db)


@router.get("")
async def list_policies(
    trigger_type: str | None = None, status: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    svc: PolicyService = Depends(_get_svc),
):
    items, total = await svc.list_policies(trigger_type, status, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@router.post("")
async def create_policy(data: PolicyCreate, svc: PolicyService = Depends(_get_svc)):
    p = await svc.create_policy(**data.model_dump())
    return success(model_to_dict(p))


@router.get("/{policy_id}")
async def get_policy(policy_id: str, svc: PolicyService = Depends(_get_svc)):
    p = await svc.get_policy(policy_id)
    return success(model_to_dict(p))


@router.put("/{policy_id}")
async def update_policy(policy_id: str, data: PolicyCreate, svc: PolicyService = Depends(_get_svc)):
    p = await svc.update_policy(policy_id, **data.model_dump())
    return success(model_to_dict(p))


@router.post("/{policy_id}/simulate")
async def simulate_policy(policy_id: str, data: PolicySimulate, svc: PolicyService = Depends(_get_svc)):
    result = await svc.simulate(policy_id, data.trigger_event, data.asset_ids)
    return success(result)


@router.delete("/{policy_id}")
async def delete_policy(policy_id: str, svc: PolicyService = Depends(_get_svc)):
    await svc.delete_policy(policy_id)
    return success(message="策略已禁用")
