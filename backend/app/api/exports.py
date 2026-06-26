"""导出中心 API（真实生成 CSV 产物）.

create → 后台按 export_type 从白名单表导出 CSV → 落盘 + 更新状态；download 返回文件。
export_type 经白名单映射到具体表，避免 SQL 注入/越权读任意表。
"""

from __future__ import annotations

import asyncio
import csv
import json
import logging
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth_dependency import require_admin
from app.common.response import paginate, success
from app.infra.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exports", tags=["导出中心"])

_running: set[asyncio.Task] = set()

# export_type → 物理表（白名单，防注入/越权）
_EXPORT_TABLES: dict[str, str] = {
    "tickets": "tickets",
    "ticket_report": "tickets",
    "assets": "assets",
    "risk_grading": "assets",
    "alerts": "alerts",
    "events": "events",
    "executions": "executions",
    "audit": "audit_logs",
    "audit_logs": "audit_logs",
    "inspection": "inspection_results",
    "inspection_results": "inspection_results",
    "anomalies": "anomalies",
}


def _export_dir() -> Path:
    candidate = os.getenv("AUTOPS_EXPORT_DIR") or str(Path.cwd() / "data" / "exports")
    try:
        Path(candidate).mkdir(parents=True, exist_ok=True)
        return Path(candidate)
    except Exception:  # noqa: BLE001
        fb = Path(tempfile.gettempdir()) / "autops_exports"
        fb.mkdir(parents=True, exist_ok=True)
        return fb


async def _run_export(export_id: str, export_type: str) -> None:
    """后台生成导出文件。"""
    from app.infra.database import async_session_factory

    table = _EXPORT_TABLES.get(export_type)
    async with async_session_factory() as session:
        await session.execute(
            text("UPDATE exports SET status='running', updated_at=:ts WHERE id=:id"),
            {"ts": datetime.now(timezone.utc), "id": export_id},
        )
        await session.commit()

        out = _export_dir() / f"export_{export_id}.csv"
        status, rows, size, err = "completed", 0, 0, None
        try:
            if not table:
                out.write_text("export_type 不支持，无数据\n", encoding="utf-8")
                err = f"unknown export_type: {export_type}"
            else:
                # 白名单表名，安全
                result = await session.execute(text(f"SELECT * FROM {table} LIMIT 10000"))
                mappings = result.mappings().all()
                with open(out, "w", newline="", encoding="utf-8-sig") as f:
                    if mappings:
                        writer = csv.DictWriter(f, fieldnames=list(mappings[0].keys()))
                        writer.writeheader()
                        for m in mappings:
                            writer.writerow({k: ("" if v is None else v) for k, v in dict(m).items()})
                    else:
                        f.write("(无数据)\n")
                rows = len(mappings)
            size = out.stat().st_size if out.exists() else 0
        except Exception as exc:  # noqa: BLE001
            logger.exception("导出生成失败 id=%s", export_id)
            status, err = "failed", str(exc)[:500]

        await session.execute(
            text(
                "UPDATE exports SET status=:st, file_path=:fp, file_size=:sz, row_count=:rc, "
                "error=:err, updated_at=:ts WHERE id=:id"
            ),
            {
                "st": status, "fp": str(out), "sz": size, "rc": rows,
                "err": err, "ts": datetime.now(timezone.utc), "id": export_id,
            },
        )
        await session.commit()


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
    try:
        total = (await db.execute(
            text("SELECT COUNT(*) FROM exports WHERE " + where), params
        )).scalar() or 0
        params["limit"] = page_size
        params["offset"] = (page - 1) * page_size
        result = await db.execute(
            text("SELECT * FROM exports WHERE " + where + " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
            params,
        )
        items = [dict(r._mapping) for r in result.fetchall()]
    except Exception:
        items, total = [], 0
    return paginate(items, total, page, page_size)


@router.post("")
async def create_export(body: dict, db: AsyncSession = Depends(get_db)):
    """创建导出任务（后台生成 CSV）."""
    now = datetime.now(timezone.utc)
    item_id = str(uuid.uuid4())
    export_type = body.get("export_type", "report")
    try:
        await db.execute(
            text(
                "INSERT INTO exports (id, name, export_type, format, status, filters, "
                "created_by, created_at, updated_at) VALUES (:id, :name, :et, :fmt, 'pending', "
                ":filters, :by, :ts, :ts)"
            ),
            {
                "id": item_id, "name": body.get("name", "导出任务"), "et": export_type,
                "fmt": body.get("format", "csv"),
                "filters": json.dumps(body.get("filters", {}), ensure_ascii=False),
                "by": body.get("created_by", ""), "ts": now,
            },
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="创建导出任务失败")

    t = asyncio.create_task(_run_export(item_id, export_type))
    _running.add(t)
    t.add_done_callback(_running.discard)
    return success({"id": item_id, "status": "pending"})


@router.get("/{export_id}/download")
async def download_export(export_id: str, db: AsyncSession = Depends(get_db)):
    """下载导出文件."""
    row = (await db.execute(
        text("SELECT * FROM exports WHERE id=:id"), {"id": export_id}
    )).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="导出任务不存在")
    fp = row.get("file_path")
    if row.get("status") != "completed" or not fp or not Path(fp).exists():
        return success({"status": row.get("status"), "message": "文件尚未生成完成"})
    return FileResponse(fp, filename=Path(fp).name, media_type="text/csv")


@router.post("/{export_id}/cancel", dependencies=[Depends(require_admin)])
async def cancel_export(export_id: str, db: AsyncSession = Depends(get_db)):
    """取消导出任务."""
    try:
        await db.execute(
            text("UPDATE exports SET status='cancelled', updated_at=:ts WHERE id=:id"),
            {"ts": datetime.now(timezone.utc), "id": export_id},
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="取消失败")
    return success({"id": export_id, "status": "cancelled"})


@router.delete("/{export_id}", dependencies=[Depends(require_admin)])
async def delete_export(export_id: str, db: AsyncSession = Depends(get_db)):
    """删除导出任务."""
    try:
        await db.execute(text("DELETE FROM exports WHERE id = :id"), {"id": export_id})
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="删除失败")
    return success({"id": export_id})
