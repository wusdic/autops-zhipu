"""Config domain query service — lightweight read-only queries for cross-domain use."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.config.models import CredentialBinding


async def get_bindings_by_asset(asset_id: str, session: AsyncSession) -> list[dict]:
    """获取资产关联的凭证绑定列表，返回 dict 列表（不暴露 ORM 对象）."""
    stmt = select(CredentialBinding).where(CredentialBinding.asset_id == asset_id)
    result = await session.execute(stmt)
    bindings = result.scalars().all()
    return [
        {
            "id": b.id,
            "credential_id": b.credential_id,
            "asset_id": b.asset_id,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in bindings
    ]
