"""Policy domain query service — lightweight read-only queries for cross-domain use."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.policy.models import PolicyExecution


async def get_policy_executions_by_asset(asset_id: str, session: AsyncSession) -> list[dict]:
    """获取匹配到指定资产的策略执行记录，返回 dict 列表（不暴露 ORM 对象）."""
    stmt = (
        select(PolicyExecution)
        .where(PolicyExecution.matched_assets.contains(asset_id))
        .order_by(PolicyExecution.created_at.desc())
    )
    result = await session.execute(stmt)
    executions = result.scalars().all()
    return [
        {
            "id": e.id,
            "policy_id": e.policy_id,
            "policy_version": e.policy_version,
            "alert_id": e.alert_id,
            "trigger_event": e.trigger_event,
            "status": e.status,
            "result": e.result,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in executions
    ]
