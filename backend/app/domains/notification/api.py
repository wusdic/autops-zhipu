"""通知 API."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.response import paginate, success
from app.domains.notification.schemas import NotificationReadPatch
from app.infra.database import get_db

router = APIRouter(prefix="/notifications", tags=["通知"])


@router.get("")
async def list_notifications(
    read: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户通知列表."""
    from app.domains.notification.models import Notification
    stmt = select(Notification)
    count_stmt = select(func.count()).select_from(Notification)
    if read is not None:
        if read:
            stmt = stmt.where(Notification.read_at.isnot(None))
            count_stmt = count_stmt.where(Notification.read_at.isnot(None))
        else:
            stmt = stmt.where(Notification.read_at.is_(None))
            count_stmt = count_stmt.where(Notification.read_at.is_(None))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    result = await db.execute(
        stmt.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(result.scalars().all())
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    body: NotificationReadPatch,
    db: AsyncSession = Depends(get_db),
):
    """标记通知已读/未读."""
    from app.domains.notification.models import Notification
    n = await db.get(Notification, notification_id)
    if not n:
        from app.common.exceptions import NotFoundError
        raise NotFoundError(f"通知 {notification_id} 不存在")
    if body.read:
        n.read_at = datetime.now(timezone.utc)
    else:
        n.read_at = None
    await db.flush()
    return success(model_to_dict(n))


@router.post("/read-all")
async def mark_all_read(db: AsyncSession = Depends(get_db)):
    """标记所有通知已读."""
    from app.domains.notification.models import Notification
    stmt = (
        sa_update(Notification)
        .where(Notification.read_at.is_(None))
        .values(read_at=datetime.now(timezone.utc))
    )
    result = await db.execute(stmt)
    await db.flush()
    return success({"updated": result.rowcount})
