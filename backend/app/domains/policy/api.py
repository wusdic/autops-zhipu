"""策略中心 Service + API."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.exceptions import DuplicateError, NotFoundError
from app.common.repository import BaseRepository
from app.common.response import paginate, success
from app.infra.database import get_db
from app.domains.policy.models import Policy, PolicyExecution
from app.domains.policy.schemas import PolicyCreate, PolicySimulate


class PolicyService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.policy_repo = BaseRepository(session, Policy)
        self.exec_repo = BaseRepository(session, PolicyExecution)

    async def create_policy(self, **kwargs) -> Policy:
        name = kwargs.get('name')
        existing = await self.session.execute(select(Policy).where(Policy.name == name))
        if existing.scalar():
            raise DuplicateError(f"策略 '{name}' 已存在")
        policy = await self.policy_repo.create(**kwargs)
        await self.session.flush()
        await self.session.refresh(policy)
        return policy

    async def list_policies(self, trigger_type: str | None = None, status: str | None = None, page: int = 1, page_size: int = 20):
        stmt = select(Policy)
        count_stmt = select(func.count()).select_from(Policy)
        if trigger_type:
            stmt = stmt.where(Policy.trigger_type == trigger_type)
            count_stmt = count_stmt.where(Policy.trigger_type == trigger_type)
        if status:
            stmt = stmt.where(Policy.status == status)
            count_stmt = count_stmt.where(Policy.status == status)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0
        result = await self.session.execute(stmt.order_by(Policy.created_at.desc()).offset((page-1)*page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def get_policy(self, policy_id: str) -> Policy:
        p = await self.policy_repo.get_by_id(policy_id)
        if not p:
            raise NotFoundError(f"策略 {policy_id} 不存在")
        return p

    async def update_policy(self, policy_id: str, **kwargs) -> Policy:
        p = await self.get_policy(policy_id)
        for k, v in kwargs.items():
            if v is not None and hasattr(p, k):
                setattr(p, k, v)
        p.version += 1
        await self.session.flush()
        await self.session.refresh(p)
        return p

    async def simulate(self, policy_id: str, trigger_event: str, asset_ids: list | None = None):
        policy = await self.get_policy(policy_id)
        # Parse trigger condition
        condition = json.loads(policy.trigger_condition) if isinstance(policy.trigger_condition, str) else policy.trigger_condition
        matched = False
        if isinstance(condition, dict):
            event_type = condition.get("event_type")
            if event_type and trigger_event == event_type:
                matched = True
        return {
            "policy_id": policy.id,
            "policy_name": policy.name,
            "trigger_matched": matched,
            "risk_level": policy.risk_level,
            "requires_approval": policy.requires_approval,
            "action_chain": json.loads(policy.action_chain) if isinstance(policy.action_chain, str) else policy.action_chain,
            "affected_assets": asset_ids or [],
        }

    async def delete_policy(self, policy_id: str):
        p = await self.get_policy(policy_id)
        p.status = "disabled"
        p.enabled = False
        await self.session.flush()


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
