"""资产发现 Service."""
from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.domains.asset.models import Asset


class DiscoveryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, data: dict) -> dict:
        """创建发现任务（模拟）."""
        return {
            "id": "mock-task-001",
            "ip_range": data.get("ip_range", ""),
            "scan_type": data.get("scan_type", "ping"),
            "status": "completed",
            "discovered_count": 0,
        }

    async def list_tasks(self, page: int, page_size: int) -> tuple[list, int]:
        """列出发现任务."""
        return [], 0

    async def get_results(self, page: int, page_size: int) -> tuple[list[dict], int]:
        """获取发现结果（从已有资产中模拟）."""
        q = select(Asset).where(Asset.is_deleted == False).order_by(Asset.created_at.desc())
        total_q = select(func.count()).select_from(Asset).where(Asset.is_deleted == False)

        total = (await self.db.execute(total_q)).scalar() or 0
        result = await self.db.execute(q.offset((page - 1) * page_size).limit(page_size))
        items = [model_to_dict(a) for a in result.scalars().all()]
        return items, total

    async def import_asset(self, data: dict) -> Asset:
        """导入发现的资产."""
        asset = Asset(
            hostname=data.get("hostname", data.get("ip", "unknown")),
            ip=data.get("ip", "0.0.0.0"),
            asset_type=data.get("asset_type", "linux_server"),
            status="offline",
        )
        self.db.add(asset)
        await self.db.commit()
        await self.db.refresh(asset)
        return asset
