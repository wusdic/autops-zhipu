"""触发历史 API（巡检规则 / 处置模板）."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import paginate
from app.infra.database import get_db

router = APIRouter(prefix="/trigger-history", tags=["触发历史"])


@router.get("")
async def list_trigger_history(
    ref_type: str | None = None,
    ref_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """触发历史列表（按 ref_type/ref_id 过滤）."""
    conds = ["1=1"]
    params: dict = {}
    if ref_type:
        conds.append("ref_type = :rt")
        params["rt"] = ref_type
    if ref_id:
        conds.append("ref_id = :ri")
        params["ri"] = ref_id
    where = " AND ".join(conds)
    try:
        total = (await db.execute(
            text("SELECT COUNT(*) FROM trigger_history WHERE " + where), params
        )).scalar() or 0
        params["limit"] = page_size
        params["offset"] = (page - 1) * page_size
        rows = (await db.execute(
            text(
                "SELECT * FROM trigger_history WHERE " + where
                + " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            ),
            params,
        )).mappings().all()
        items = []
        for r in rows:
            d = dict(r)
            if isinstance(d.get("detail"), str):
                try:
                    d["detail"] = json.loads(d["detail"])
                except (json.JSONDecodeError, ValueError):
                    pass
            items.append(d)
    except Exception:
        items, total = [], 0
    return paginate(items, total, page, page_size)
