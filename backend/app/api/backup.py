"""平台备份恢复 API."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter
from app.common.response import success, paginate

router = APIRouter(prefix="/backups", tags=["备份恢复"])

# 模拟备份记录存储（生产环境应使用数据库）
_mock_backups: list[dict] = []


@router.get("")
async def list_backups():
    """列出备份记录."""
    if not _mock_backups:
        # 创建一条模拟记录
        _mock_backups.append({
            "id": str(uuid.uuid4()),
            "type": "full",
            "status": "completed",
            "size": 52428800,
            "created_at": datetime.utcnow().isoformat(),
            "finished_at": datetime.utcnow().isoformat(),
            "description": "初始全量备份",
        })
    return paginate(_mock_backups, len(_mock_backups), 1, 20)


@router.post("")
async def create_backup(body: dict | None = None):
    """创建备份."""
    backup_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    backup = {
        "id": backup_id,
        "type": (body or {}).get("type", "full"),
        "status": "running",
        "size": 0,
        "created_at": now,
        "finished_at": None,
        "description": f"手动{(body or {}).get('type', 'full')}备份",
    }
    _mock_backups.insert(0, backup)
    # Simulate completion
    backup["status"] = "completed"
    backup["size"] = 31457280
    backup["finished_at"] = datetime.utcnow().isoformat()
    return success(backup)


@router.get("/settings")
async def get_backup_settings():
    """获取备份配置."""
    return success({
        "auto_backup": True,
        "schedule": "0 2 * * *",
        "retention_days": 30,
        "storage_type": "local",
        "compression": True,
    })


@router.get("/storage")
async def get_backup_storage():
    """获取备份存储信息."""
    return success({
        "total_size": 157286400,
        "used_size": 52428800,
        "backup_count": len(_mock_backups),
        "storage_path": "/data/backups",
    })


@router.post("/{backup_id}/restore")
async def restore_backup(backup_id: str):
    """恢复备份."""
    backup = next((b for b in _mock_backups if b["id"] == backup_id), None)
    if not backup:
        return success({"status": "not_found", "message": "备份记录不存在"})
    return success({
        "status": "started",
        "backup_id": backup_id,
        "message": "恢复任务已启动",
    })


@router.get("/{backup_id}")
async def get_backup(backup_id: str):
    """获取备份详情."""
    backup = next((b for b in _mock_backups if b["id"] == backup_id), None)
    if not backup:
        from app.common.exceptions import NotFoundError
        raise NotFoundError("备份记录不存在")
    return success(backup)


@router.get("/{backup_id}/download")
async def download_backup(backup_id: str):
    """下载备份文件（返回下载信息）."""
    backup = next((b for b in _mock_backups if b["id"] == backup_id), None)
    if not backup:
        from app.common.exceptions import NotFoundError
        raise NotFoundError("备份记录不存在")
    return success({
        "backup_id": backup_id,
        "download_url": f"/api/v1/backups/{backup_id}/file",
        "size": backup.get("size", 0),
        "expires_in": 3600,
    })
