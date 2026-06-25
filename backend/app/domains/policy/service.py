"""策略中心 Service."""

from __future__ import annotations

import json

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import DuplicateError, NotFoundError
from app.common.repository import BaseRepository
from app.domains.policy.models import Policy, PolicyExecution


class PolicyService:
    """策略业务逻辑."""

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

    async def match_and_plan(self, event_type: str, severity: str, asset_ids: list, alert_id: str):
        """根据告警匹配策略并创建执行计划（不直接执行命令）."""
        q = select(Policy).where(Policy.enabled == True, Policy.status == "active")
        result = await self.session.execute(q)
        policies = list(result.scalars().all())

        matched = []
        for policy in policies:
            tc = policy.trigger_condition
            if isinstance(tc, str):
                tc = json.loads(tc)
            if isinstance(tc, dict) and tc.get("event_type") == event_type:
                if severity in tc.get("severity", []):
                    matched.append(policy)

        if not matched:
            return None

        best = matched[0]

        # 创建 PolicyExecution 记录
        import uuid as _uuid
        from datetime import datetime as _dt, timezone
        pe = PolicyExecution(
            id=str(_uuid.uuid4()),
            policy_id=best.id,
            policy_version=best.version,
            alert_id=alert_id,
            trigger_event=event_type,
            matched_assets=json.dumps(asset_ids) if isinstance(asset_ids, list) else str(asset_ids),
            status="matched",
            result=json.dumps({"explanation": f"告警类型 '{event_type}' 严重级别 '{severity}' 匹配策略 '{best.name}'"}, ensure_ascii=False),
            created_at=_dt.now(timezone.utc)
        )
        self.session.add(pe)
        await self.session.flush()

        # 如果需要审批，发事件
        if best.requires_approval:
            pe.status = "awaiting_approval"
            await self.session.flush()
        else:
            # 自动执行
            pe.status = "executing"
            await self.session.flush()

        return {"policy_execution_id": pe.id, "policy_name": best.name, "status": pe.status}
