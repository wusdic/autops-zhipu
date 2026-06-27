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

    @staticmethod
    def _matches(policy: Policy, event_type: str, severity: str, context: dict | None) -> bool:
        """判断单条策略是否命中当前告警（统一匹配逻辑）."""
        tc = policy.trigger_condition
        if isinstance(tc, str):
            try:
                tc = json.loads(tc)
            except (json.JSONDecodeError, ValueError):
                tc = {}
        if not isinstance(tc, dict):
            tc = {}
        trigger_type = policy.trigger_type
        ctx = context or {}
        if trigger_type == "alert_severity":
            target = tc.get("severity", "")
            # severity 可能是单值或列表
            if isinstance(target, list):
                return bool(severity) and severity in target
            return bool(target) and severity == target
        if trigger_type in ("alert_type", "event_type"):
            target = tc.get("alert_type") or tc.get("event_type") or ""
            current = event_type or ctx.get("event_type", "")
            return bool(target) and current == target
        if trigger_type == "any_alert":
            return True
        return False

    async def match_and_record(
        self,
        event_type: str,
        severity: str,
        asset_ids: list,
        alert_id: str,
        context: dict | None = None,
    ) -> list[dict]:
        """根据告警匹配所有命中策略，逐条落 PolicyExecution，返回执行计划列表.

        统一收敛策略匹配 + 审计落库（审查 P0-02）：handler 只负责发事件编排，
        命中的每条策略都生成 PolicyExecution 记录（matched / awaiting_approval），
        并把 policy_execution_id 带入后续 POLICY_TRIGGERED/EXECUTION_CREATED，
        打通 Event→Alert→PolicyExecution→Execution 全链关联。
        """
        result = await self.session.execute(
            select(Policy).where(Policy.enabled == True, Policy.status == "active")
        )
        policies = list(result.scalars().all())

        plans: list[dict] = []
        for policy in policies:
            if not self._matches(policy, event_type, severity, context):
                continue
            ac = policy.action_chain
            if isinstance(ac, str):
                try:
                    ac = json.loads(ac)
                except (json.JSONDecodeError, ValueError):
                    ac = []
            if not isinstance(ac, list):
                ac = []

            status = "awaiting_approval" if policy.requires_approval else "matched"
            pe = await self.exec_repo.create(
                policy_id=policy.id,
                policy_version=policy.version,
                alert_id=alert_id,
                trigger_event=event_type,
                matched_assets=json.dumps(asset_ids) if isinstance(asset_ids, list) else str(asset_ids),
                status=status,
                result=json.dumps(
                    {"explanation": f"告警(type={event_type}, severity={severity}) 命中策略 '{policy.name}'"},
                    ensure_ascii=False,
                ),
            )
            await self.session.flush()
            plans.append(
                {
                    "policy_execution_id": str(pe.id),
                    "policy_id": str(policy.id),
                    "policy_name": policy.name,
                    "action_chain": ac,
                    "requires_approval": policy.requires_approval,
                    "risk_level": policy.risk_level,
                    "matched_assets": asset_ids,
                    "alert_id": alert_id,
                    "status": status,
                }
            )
        return plans

    async def mark_executing(self, policy_execution_id: str, execution_id: str) -> None:
        """策略执行创建出自动化执行后回填关联与状态."""
        pe = await self.exec_repo.get_by_id(policy_execution_id)
        if not pe:
            return
        pe.execution_id = execution_id
        pe.status = "executing"
        await self.session.flush()
