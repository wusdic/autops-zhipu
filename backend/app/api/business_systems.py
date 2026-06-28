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
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar() or 0

    rows = (
        (
            await db.execute(
                base.order_by(Asset.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )

    # 关联资产数 + 健康度聚合（业务系统不应有静态健康度；按成员资产实时聚合）
    # 成员事实源为 business_system_id；兼容尚未回填 id 的历史数据（按名匹配）。
    items = []
    for r in rows:
        d = model_to_dict(r)
        members = (
            (
                await db.execute(
                    select(Asset.health_status).where(
                        ((Asset.business_system_id == r.id)
                         | (Asset.business_system == r.name)),
                        Asset.asset_type != "business_system",
                        Asset.is_deleted == False,
                    )
                )
            )
            .scalars()
            .all()
        )
        d["asset_count"] = len(members)
        if not members:
            d["health_status"] = "unknown"
        elif any(h == "critical" for h in members):
            d["health_status"] = "critical"
        elif any(h == "warning" for h in members):
            d["health_status"] = "warning"
        elif all(h == "healthy" for h in members):
            d["health_status"] = "healthy"
        else:
            d["health_status"] = "unknown"
        items.append(d)
    return paginate(items, total, page, page_size)


@router.post("")
async def create_business_system(
    data: BusinessSystemCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建业务系统(实际创建 asset_type=business_system 的资产)."""
    import json
    from app.domains.asset.models import Asset

    # 新建业务系统默认健康度 unknown：0 关联资产不应显示“健康”（误导）；
    # 健康度应由关联资产聚合得出（见 health 聚合）。
    asset = Asset(
        name=data.name,
        asset_type="business_system",
        hostname=data.code,
        description=data.description,
        status="active",
        health_status="unknown",
        reachability="unknown",
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

    row = (
        await db.execute(
            select(Asset).where(
                Asset.id == system_id,
                Asset.asset_type == "business_system",
                Asset.is_deleted == False,
            )
        )
    ).scalar_one_or_none()
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

    row = (
        await db.execute(
            select(Asset).where(
                Asset.id == system_id,
                Asset.asset_type == "business_system",
                Asset.is_deleted == False,
            )
        )
    ).scalar_one_or_none()
    if not row:
        return success(None, message="业务系统不存在")

    updates = data.model_dump(exclude_unset=True)
    if "tags" in updates and updates["tags"] is not None:
        import json

        updates["tags"] = json.dumps(updates["tags"])

    old_name = row.name
    for k, v in updates.items():
        if hasattr(row, k):
            setattr(row, k, v)
    await db.flush()
    # 改名 → 同步成员资产的名缓存（事实源是 business_system_id，仅同步展示名）
    if "name" in updates and updates["name"] != old_name:
        from sqlalchemy import update as _update

        await db.execute(
            _update(Asset)
            .where(Asset.business_system_id == row.id)
            .values(business_system=row.name)
        )
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
    from datetime import datetime, timezone

    row = (
        await db.execute(
            select(Asset).where(
                Asset.id == system_id,
                Asset.asset_type == "business_system",
                Asset.is_deleted == False,
            )
        )
    ).scalar_one_or_none()
    if not row:
        return success(None, message="业务系统不存在")

    row.is_deleted = True
    row.deleted_at = datetime.now(timezone.utc)
    # 解除成员归属，避免悬挂引用
    from sqlalchemy import update as _update

    await db.execute(
        _update(Asset)
        .where(Asset.business_system_id == system_id)
        .values(business_system_id=None, business_system=None)
    )
    await db.flush()
    return success({"id": system_id, "deleted": True})


# ======================================================================
# 成员资产管理：列表 / 添加 / 移除（事实源 = assets.business_system_id）
# ======================================================================
class MemberAssignBody(BaseModel):
    asset_ids: list[str] = Field(default_factory=list)


@router.get("/{system_id}/members")
async def list_members(
    system_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """列出业务系统下的成员资产."""
    from app.domains.asset.service import AssetService

    rows, total = await AssetService(db).list_business_members(system_id, page, page_size)
    return paginate([model_to_dict(a) for a in rows], total, page, page_size)


@router.post("/{system_id}/members")
async def add_members(
    system_id: str,
    body: MemberAssignBody,
    db: AsyncSession = Depends(get_db),
):
    """把若干资产归属到该业务系统."""
    from app.domains.asset.service import AssetService

    svc = AssetService(db)
    n = 0
    for aid in body.asset_ids:
        try:
            await svc.assign_business_system(aid, system_id)
            n += 1
        except Exception:  # noqa: BLE001 单个失败不影响整体
            continue
    return success({"assigned": n})


@router.delete("/{system_id}/members/{asset_id}")
async def remove_member(
    system_id: str,
    asset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """从业务系统移除某成员资产（解除归属）."""
    from app.domains.asset.service import AssetService

    await AssetService(db).assign_business_system(asset_id, None)
    return success({"asset_id": asset_id, "removed": True})
