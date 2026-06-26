"""触发历史记录工具.

记录巡检规则 / 处置模板(Playbook) 的触发，供前端「历史」查看。
复用调用方 session（不自行 commit），失败不影响主流程。
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def record_trigger(
    session: AsyncSession,
    *,
    ref_type: str,
    ref_id: str,
    ref_name: str | None = None,
    action: str = "triggered",
    status: str = "success",
    detail: dict[str, Any] | None = None,
) -> None:
    """写一条触发历史（复用 session，由调用方 commit）。失败仅记日志。"""
    try:
        await session.execute(
            text(
                "INSERT INTO trigger_history (id, ref_type, ref_id, ref_name, action, "
                "status, detail, created_at) VALUES (:id, :rt, :ri, :rn, :ac, :st, :dt, :ts)"
            ),
            {
                "id": str(uuid.uuid4()), "rt": ref_type, "ri": str(ref_id),
                "rn": ref_name, "ac": action, "st": status,
                "dt": json.dumps(detail or {}, ensure_ascii=False, default=str),
                "ts": datetime.now(timezone.utc),
            },
        )
    except Exception:  # noqa: BLE001
        logger.warning("record_trigger 失败 ref_type=%s ref_id=%s", ref_type, ref_id, exc_info=True)
