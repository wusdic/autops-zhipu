"""导出中心 API."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth_dependency import require_admin
from app.common.response import paginate, success
from app.infra.database import get_db

router = APIRouter(prefix="/exports", tags=["导出中心"])


@router.get("")
async def list_exports(
    status: str | None = None,
    export_type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """列出导出任务."""
    conditions = ["1=1"]
    params: dict = {}
    if status:
        conditions.append("status = :status")
        params["status"] = status
    if export_type:
        conditions.append("export_type = :export_type")
        params["export_type"] = export_type

    where = " AND ".join(conditions)
    count_sql = "SELECT COUNT(*) as cnt FROM exports WHERE " + where
    data_sql = (
        "SELECT * FROM exports WHERE "
        + where
        + " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
    )

    try:
        cnt_result = await db.execute(text(count_sql), params)
        total = cnt_result.scalar() or 0
        params["limit"] = page_size
        params["offset"] = (page - 1) * page_size
        result = await db.execute(text(data_sql), params)
        items = [dict(row._mapping) for row in result.fetchall()]
    except Exception:
        items = []
        total = 0

    return paginate(items, total, page, page_size)


@router.post("")
async def create_export(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """创建导出任务."""
    now = datetime.now(timezone.utc)
    item_id = str(uuid.uuid4())
    sql = text("""INSERT INTO exports
        (id, name, export_type, format, status, filters, created_by, created_at, updated_at)
        VALUES (:id, :name, :export_type, :format, :status, :filters, :created_by, :created_at, :updated_at)
    """)
    try:
        await db.execute(
            sql,
            {
                "id": item_id,
                "name": body.get("name", "导出任务"),
                "export_type": body.get("export_type", "report"),
                "format": body.get("format", "xlsx"),
                "status": "pending",
                "filters": json.dumps(body.get("filters", {}), ensure_ascii=False),
                "created_by": body.get("created_by", ""),
                "created_at": now,
                "updated_at": now,
            },
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="创建导出任务失败")

    return success({"id": item_id, "status": "pending"})


@router.post("/{export_id}/cancel", dependencies=[Depends(require_admin)])
async def cancel_export(
    export_id: str,
    db: AsyncSession = Depends(get_db),
):
    """取消导出任务."""
    try:
        await db.execute(
            text(
                "UPDATE exports SET status = :status, updated_at = :updated_at WHERE id = :id"
            ),
            {
                "status": "cancelled",
                "updated_at": datetime.now(timezone.utc),
                "id": export_id,
            },
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="取消失败")

    return success({"id": export_id, "status": "cancelled"})


@router.delete("/{export_id}", dependencies=[Depends(require_admin)])
async def delete_export(
    export_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除导出任务."""
    try:
        await db.execute(text("DELETE FROM exports WHERE id = :id"), {"id": export_id})
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="删除失败")

    return success({"id": export_id})
