"""通知规则 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.response import paginate, success
from app.infra.database import get_db
from app.domains.notification.rule_models import NotificationRule

router = APIRouter(prefix="/notification-rules", tags=["通知规则"])


class NotificationRuleCreate(BaseModel):
    name: str
    description: str | None = None
    event_type: str
    target_type: str = "user"
    target_ids: str
    channels: str
    severity_filter: str | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    enabled: bool = True


class NotificationRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    event_type: str | None = None
    target_type: str | None = None
    target_ids: str | None = None
    channels: str | None = None
    severity_filter: str | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    enabled: bool | None = None


@router.get("")
async def list_notification_rules(
    event_type: str | None = None,
    target_type: str | None = None,
    enabled: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """列出通知规则."""
    stmt = select(NotificationRule).where(NotificationRule.id.isnot(None))
    count_stmt = select(sa_func.count()).select_from(NotificationRule)

    if event_type:
        stmt = stmt.where(NotificationRule.event_type == event_type)
        count_stmt = count_stmt.where(NotificationRule.event_type == event_type)
    if target_type:
        stmt = stmt.where(NotificationRule.target_type == target_type)
        count_stmt = count_stmt.where(NotificationRule.target_type == target_type)
    if enabled is not None:
        stmt = stmt.where(NotificationRule.enabled == enabled)
        count_stmt = count_stmt.where(NotificationRule.enabled == enabled)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    result = await db.execute(
        stmt.order_by(NotificationRule.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(result.scalars().all())
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@router.post("")
async def create_notification_rule(data: NotificationRuleCreate, db: AsyncSession = Depends(get_db)):
    """创建通知规则."""
    rule = NotificationRule(**data.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return success(model_to_dict(rule))


@router.get("/{rule_id}")
async def get_notification_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    """获取通知规则详情."""
    result = await db.execute(select(NotificationRule).where(NotificationRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        return success(None, message="规则不存在")
    return success(model_to_dict(rule))


@router.put("/{rule_id}")
async def update_notification_rule(rule_id: str, data: NotificationRuleUpdate, db: AsyncSession = Depends(get_db)):
    """更新通知规则."""
    result = await db.execute(select(NotificationRule).where(NotificationRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        return success(None, message="规则不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(rule, k, v)
    await db.commit()
    await db.refresh(rule)
    return success(model_to_dict(rule))


@router.delete("/{rule_id}")
async def delete_notification_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    """删除通知规则."""
    result = await db.execute(select(NotificationRule).where(NotificationRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        return success(None, message="规则不存在")
    await db.delete(rule)
    await db.commit()
    return success(message="已删除")


@router.post("/{rule_id}/toggle")
async def toggle_notification_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    """启用/禁用通知规则."""
    result = await db.execute(select(NotificationRule).where(NotificationRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        return success(None, message="规则不存在")
    rule.enabled = not rule.enabled
    await db.commit()
    await db.refresh(rule)
    return success(model_to_dict(rule))
