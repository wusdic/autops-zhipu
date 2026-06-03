"""Agent 管理 API.

Agent 即 Edge Collector，本文件复用 collector 域的模型提供管理视图。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import success, paginate
from app.common.crud_service import model_to_dict
from app.infra.database import get_db

router = APIRouter(prefix="/agents", tags=["Agent管理"])


@router.get("")
async def list_agents(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """列出所有 Agent (Edge Collector)."""
    from app.domains.collector.models import Collector

    base = select(Collector).where(Collector.collector_type == "edge")
    if status:
        base = base.where(Collector.status == status)

    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar() or 0

    rows = (await db.execute(
        base.order_by(Collector.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).scalars().all()

    items = [model_to_dict(r) for r in rows]
    return paginate(items, total, page, page_size)


@router.get("/{agent_id}")
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取 Agent 详情."""
    from app.domains.collector.models import Collector

    row = (await db.execute(
        select(Collector).where(Collector.id == agent_id)
    )).scalar_one_or_none()
    if not row:
        return success(None, message="Agent不存在")
    return success(model_to_dict(row))


@router.post("/{agent_id}/upgrade")
async def upgrade_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """下发 Agent 升级指令(标记状态)."""
    from app.domains.collector.models import Collector

    row = (await db.execute(
        select(Collector).where(Collector.id == agent_id)
    )).scalar_one_or_none()
    if not row:
        return success(None, message="Agent不存在")

    row.status = "upgrading"
    await db.flush()
    await db.refresh(row)
    return success(model_to_dict(row))
