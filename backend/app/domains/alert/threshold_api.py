"""阈值规则 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.response import paginate, success
from app.infra.database import get_db
from app.domains.alert.threshold_models import ThresholdRule

router = APIRouter(prefix="/threshold-rules", tags=["阈值规则"])


class ThresholdRuleCreate(BaseModel):
    name: str
    description: str | None = None
    metric_name: str
    asset_type: str | None = None
    condition: str = "gt"
    threshold_value: float
    duration_seconds: int = 0
    severity: str = "warning"
    notify_channels: str | None = None
    enabled: bool = True


class ThresholdRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    metric_name: str | None = None
    asset_type: str | None = None
    condition: str | None = None
    threshold_value: float | None = None
    duration_seconds: int | None = None
    severity: str | None = None
    notify_channels: str | None = None
    enabled: bool | None = None


@router.get("")
async def list_threshold_rules(
    metric_name: str | None = None,
    asset_type: str | None = None,
    severity: str | None = None,
    enabled: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """列出阈值规则."""
    stmt = select(ThresholdRule).where(ThresholdRule.id.isnot(None))
    count_stmt = select(sa_func.count()).select_from(ThresholdRule)

    if metric_name:
        stmt = stmt.where(ThresholdRule.metric_name == metric_name)
        count_stmt = count_stmt.where(ThresholdRule.metric_name == metric_name)
    if asset_type:
        stmt = stmt.where(ThresholdRule.asset_type == asset_type)
        count_stmt = count_stmt.where(ThresholdRule.asset_type == asset_type)
    if severity:
        stmt = stmt.where(ThresholdRule.severity == severity)
        count_stmt = count_stmt.where(ThresholdRule.severity == severity)
    if enabled is not None:
        stmt = stmt.where(ThresholdRule.enabled == enabled)
        count_stmt = count_stmt.where(ThresholdRule.enabled == enabled)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    result = await db.execute(
        stmt.order_by(ThresholdRule.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(result.scalars().all())
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@router.post("")
async def create_threshold_rule(data: ThresholdRuleCreate, db: AsyncSession = Depends(get_db)):
    """创建阈值规则."""
    rule = ThresholdRule(**data.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return success(model_to_dict(rule))


@router.get("/{rule_id}")
async def get_threshold_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    """获取阈值规则详情."""
    result = await db.execute(select(ThresholdRule).where(ThresholdRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        return success(None, message="规则不存在")
    return success(model_to_dict(rule))


@router.put("/{rule_id}")
async def update_threshold_rule(rule_id: str, data: ThresholdRuleUpdate, db: AsyncSession = Depends(get_db)):
    """更新阈值规则."""
    result = await db.execute(select(ThresholdRule).where(ThresholdRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        return success(None, message="规则不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(rule, k, v)
    await db.commit()
    await db.refresh(rule)
    return success(model_to_dict(rule))


@router.delete("/{rule_id}")
async def delete_threshold_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    """删除阈值规则."""
    result = await db.execute(select(ThresholdRule).where(ThresholdRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        return success(None, message="规则不存在")
    await db.delete(rule)
    await db.commit()
    return success(message="已删除")


@router.post("/{rule_id}/toggle")
async def toggle_threshold_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    """启用/禁用阈值规则."""
    result = await db.execute(select(ThresholdRule).where(ThresholdRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        return success(None, message="规则不存在")
    rule.enabled = not rule.enabled
    await db.commit()
    await db.refresh(rule)
    return success(model_to_dict(rule))
