"""审计日志API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import AuditLog
from app.common.auth_dependency import require_admin
from app.common.response import paginate
from app.infra.database import get_db

# 审计日志含全平台操作明细，仅管理员可读
router = APIRouter(
    prefix="/audit-logs", tags=["audit"], dependencies=[Depends(require_admin)]
)


@router.get("")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    username: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """查询审计日志."""
    query = select(AuditLog).order_by(desc(AuditLog.created_at))
    count_query = select(func.count()).select_from(AuditLog)

    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
        count_query = count_query.where(AuditLog.resource_type == resource_type)
    if username:
        query = query.where(AuditLog.username == username)
        count_query = count_query.where(AuditLog.username == username)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = result.scalars().all()

    return paginate(
        [
            {
                "id": item.id,
                "trace_id": item.trace_id,
                "user_id": item.user_id,
                "username": item.username,
                "action": item.action,
                "resource_type": item.resource_type,
                "resource_id": item.resource_id,
                "detail": item.detail,
                "ip_address": item.ip_address,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ],
        total,
        page,
        page_size,
    )
