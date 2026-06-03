"""业务系统 API.

业务系统是资产(asset_type='business_system')的语义化封装。
底层复用 asset 域的模型和服务，本文件提供便捷的 CRUD 端点。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import success, paginate
from app.common.crud_service import model_to_dict
from app.infra.database import get_db

router = APIRouter(prefix="/business-systems", tags=["业务系统"])


class BusinessSystemCreate(BaseModel):
    name: str = Field(..., max_length=128)
    code: str | None = None
    description: str | None = None
    importance: str = Field("medium", pattern="^(low|medium|high|critical)$")
    sla_level: str = Field("standard", pattern="^(standard|premium|critical)$")
    owner: str | None = None
    tags: list[str] | None = None


class BusinessSystemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    importance: str | None = None
    sla_level: str | None = None
    owner: str | None = None
    tags: list[str] | None = None


@router.get("")
async def list_business_systems(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """列出所有业务系统."""
    from app.domains.asset.models import Asset

    base = select(Asset).where(
        Asset.asset_type == "business_system",
        Asset.is_deleted == False,
    )
    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar() or 0

    rows = (await db.execute(
        base.order_by(Asset.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).scalars().all()

    items = [model_to_dict(r) for r in rows]
    return paginate(items, total, page, page_size)


@router.post("")
async def create_business_system(
    data: BusinessSystemCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建业务系统(实际创建 asset_type=business_system 的资产)."""
    import json
    from app.domains.asset.models import Asset

    asset = Asset(
        name=data.name,
        asset_type="business_system",
        hostname=data.code,
        description=data.description,
        status="active",
        health_status="healthy",
        reachability="reachable",
        tags=json.dumps(data.tags or []),
    )
    db.add(asset)
    await db.flush()
    await db.refresh(asset)
    return success(model_to_dict(asset))


@router.get("/{system_id}")
async def get_business_system(
    system_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取业务系统详情."""
    from app.domains.asset.models import Asset

    row = (await db.execute(
        select(Asset).where(
            Asset.id == system_id,
            Asset.asset_type == "business_system",
            Asset.is_deleted == False,
        )
    )).scalar_one_or_none()
    if not row:
        return success(None, message="业务系统不存在")
    return success(model_to_dict(row))


@router.put("/{system_id}")
async def update_business_system(
    system_id: str,
    data: BusinessSystemUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新业务系统."""
    from app.domains.asset.models import Asset

    row = (await db.execute(
        select(Asset).where(
            Asset.id == system_id,
            Asset.asset_type == "business_system",
            Asset.is_deleted == False,
        )
    )).scalar_one_or_none()
    if not row:
        return success(None, message="业务系统不存在")

    updates = data.model_dump(exclude_unset=True)
    if "tags" in updates and updates["tags"] is not None:
        import json
        updates["tags"] = json.dumps(updates["tags"])

    for k, v in updates.items():
        if hasattr(row, k):
            setattr(row, k, v)
    await db.flush()
    await db.refresh(row)
    return success(model_to_dict(row))


@router.delete("/{system_id}")
async def delete_business_system(
    system_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除业务系统(软删除)."""
    from app.domains.asset.models import Asset
    from datetime import datetime

    row = (await db.execute(
        select(Asset).where(
            Asset.id == system_id,
            Asset.asset_type == "business_system",
            Asset.is_deleted == False,
        )
    )).scalar_one_or_none()
    if not row:
        return success(None, message="业务系统不存在")

    row.is_deleted = True
    row.deleted_at = datetime.utcnow()
    await db.flush()
    return success({"id": system_id, "deleted": True})
