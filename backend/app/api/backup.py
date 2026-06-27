"""平台备份恢复 API（DB 持久化 + 尽力生成真实产物）.

备份记录落 backups 表；产物用 mysqldump 尽力生成（缺工具/非 MySQL 时降级为
逻辑导出占位并标注）。备份/恢复属高危操作，仅管理员可用。设置存 system_settings。
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth_dependency import require_admin
from app.common.exceptions import NotFoundError
from app.common.response import paginate, success
from app.infra.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/backups", tags=["备份恢复"], dependencies=[Depends(require_admin)]
)

_running: set[asyncio.Task] = set()
_DEFAULT_SETTINGS = {
    "auto_backup": False,
    "schedule": "0 2 * * *",
    "retention_days": 30,
    "storage_type": "local",
    "compression": True,
}


def _backup_dir() -> Path:
    candidate = os.getenv("AUTOPS_BACKUP_DIR") or str(Path.cwd() / "data" / "backups")
    try:
        Path(candidate).mkdir(parents=True, exist_ok=True)
        return Path(candidate)
    except Exception:  # noqa: BLE001
        fb = Path(tempfile.gettempdir()) / "autops_backups"
        fb.mkdir(parents=True, exist_ok=True)
        return fb


async def _run_backup(backup_id: str) -> None:
    """后台执行备份：尽力 mysqldump，更新记录状态。"""
    from app.infra.config import get_config
    from app.infra.database import async_session_factory

    async with async_session_factory() as session:
        await session.execute(
            text("UPDATE backups SET status='running', started_at=:ts WHERE id=:id"),
            {"ts": datetime.now(timezone.utc), "id": backup_id},
        )
        await session.commit()

        cfg = get_config().database
        out = _backup_dir() / f"backup_{backup_id}.sql"
        status, size, err = "completed", 0, None
        try:
            mysqldump = shutil.which("mysqldump")
            if mysqldump and cfg.dialect in ("mysql",):
                env = dict(os.environ, MYSQL_PWD=cfg.db_pass or "")
                proc = await asyncio.create_subprocess_exec(
                    mysqldump, "-h", cfg.host, "-P", str(cfg.port),
                    "-u", cfg.user, "--single-transaction", cfg.database,
                    stdout=open(out, "wb"), stderr=asyncio.subprocess.PIPE, env=env,
                )
                _, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)
                if proc.returncode != 0:
                    status, err = "failed", (stderr or b"").decode("utf-8", "replace")[:500]
                else:
                    size = out.stat().st_size if out.exists() else 0
            else:
                # 无 mysqldump / 非 MySQL：写占位说明，标记 degraded
                out.write_text(
                    f"-- AUTOPS backup placeholder ({datetime.now(timezone.utc).isoformat()})\n"
                    f"-- mysqldump 不可用或非 MySQL 方言({cfg.dialect})，未生成真实物理备份。\n",
                    encoding="utf-8",
                )
                # 占位文件不是可恢复备份，必须标记 degraded（而非 completed），
                # 否则用户会下载到不可恢复的"已完成备份"。
                size, status = out.stat().st_size, "degraded"
                err = "mysqldump 不可用，已生成占位文件（非真实备份，不可恢复）"
        except Exception as exc:  # noqa: BLE001
            logger.exception("备份执行失败 id=%s", backup_id)
            status, err = "failed", str(exc)[:500]

        await session.execute(
            text(
                "UPDATE backups SET status=:st, file_path=:fp, file_size=:sz, error=:err, "
                "completed_at=:ts WHERE id=:id"
            ),
            {
                "st": status, "fp": str(out), "sz": size, "err": err,
                "ts": datetime.now(timezone.utc), "id": backup_id,
            },
        )
        await session.commit()


@router.get("")
async def list_backups(db: AsyncSession = Depends(get_db)):
    """列出备份记录."""
    total = (await db.execute(text("SELECT COUNT(*) FROM backups"))).scalar() or 0
    rows = (
        (await db.execute(
            text("SELECT * FROM backups ORDER BY created_at DESC LIMIT 100")
        )).mappings().all()
    )
    return paginate([dict(r) for r in rows], total, 1, 100)


@router.post("")
async def create_backup(body: dict | None = None, db: AsyncSession = Depends(get_db)):
    """创建备份（后台执行）."""
    body = body or {}
    bid = str(uuid.uuid4())
    btype = body.get("type", "full")
    await db.execute(
        text(
            "INSERT INTO backups (id, name, backup_type, status, created_at) "
            "VALUES (:id, :name, :type, 'pending', :ts)"
        ),
        {
            "id": bid, "name": body.get("name", f"手动{btype}备份"),
            "type": btype, "ts": datetime.now(timezone.utc),
        },
    )
    await db.commit()
    t = asyncio.create_task(_run_backup(bid))
    _running.add(t)
    t.add_done_callback(_running.discard)
    return success({"id": bid, "status": "pending", "type": btype})


@router.get("/settings")
async def get_backup_settings(db: AsyncSession = Depends(get_db)):
    """获取备份配置."""
    row = (await db.execute(
        text("SELECT svalue FROM system_settings WHERE skey='backup_settings'")
    )).first()
    if row and row[0]:
        try:
            return success(json.loads(row[0]))
        except (json.JSONDecodeError, ValueError):
            pass
    return success(_DEFAULT_SETTINGS)


@router.put("/settings")
async def update_backup_settings(body: dict, db: AsyncSession = Depends(get_db)):
    """更新备份配置."""
    value = json.dumps({**_DEFAULT_SETTINGS, **(body or {})}, ensure_ascii=False)
    ts = datetime.now(timezone.utc)
    res = await db.execute(
        text("UPDATE system_settings SET svalue=:v, updated_at=:ts WHERE skey='backup_settings'"),
        {"v": value, "ts": ts},
    )
    if (res.rowcount or 0) == 0:
        await db.execute(
            text("INSERT INTO system_settings (skey, svalue, updated_at) VALUES ('backup_settings', :v, :ts)"),
            {"v": value, "ts": ts},
        )
    await db.commit()
    return success(json.loads(value))


@router.get("/storage")
async def get_backup_storage(db: AsyncSession = Depends(get_db)):
    """获取备份存储信息."""
    row = (await db.execute(
        text("SELECT COUNT(*) AS c, COALESCE(SUM(file_size),0) AS s FROM backups")
    )).mappings().first()
    return success(
        {
            "used_size": int(row["s"]) if row else 0,
            "backup_count": int(row["c"]) if row else 0,
            "storage_path": str(_backup_dir()),
        }
    )


@router.post("/{backup_id}/restore")
async def restore_backup(backup_id: str, db: AsyncSession = Depends(get_db)):
    """恢复备份（标记并尽力执行，需管理员）."""
    row = (await db.execute(
        text("SELECT * FROM backups WHERE id=:id"), {"id": backup_id}
    )).mappings().first()
    if not row:
        raise NotFoundError("备份记录不存在")
    if row["status"] != "completed" or not row.get("file_path"):
        return success({"status": "rejected", "message": "该备份不可恢复（未完成或无文件）"})
    # 恢复为高危且耗时操作，这里返回已受理；真实导入需运维在受控窗口执行。
    return success(
        {
            "status": "accepted",
            "backup_id": backup_id,
            "file_path": row["file_path"],
            "message": "恢复请求已受理，请在维护窗口由运维执行导入（mysql < 文件）",
        }
    )


@router.get("/{backup_id}")
async def get_backup(backup_id: str, db: AsyncSession = Depends(get_db)):
    """获取备份详情."""
    row = (await db.execute(
        text("SELECT * FROM backups WHERE id=:id"), {"id": backup_id}
    )).mappings().first()
    if not row:
        raise NotFoundError("备份记录不存在")
    return success(dict(row))


@router.get("/{backup_id}/download")
async def download_backup(backup_id: str, db: AsyncSession = Depends(get_db)):
    """下载备份文件."""
    row = (await db.execute(
        text("SELECT * FROM backups WHERE id=:id"), {"id": backup_id}
    )).mappings().first()
    if not row:
        raise NotFoundError("备份记录不存在")
    fp = row.get("file_path")
    if not fp or not Path(fp).exists():
        return success({"status": "unavailable", "message": "备份文件不存在或尚未生成"})
    return FileResponse(fp, filename=Path(fp).name, media_type="application/sql")
