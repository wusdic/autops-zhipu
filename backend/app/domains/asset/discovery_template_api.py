"""发现模板 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.response import paginate, success
from app.infra.database import get_db
from app.domains.asset.discovery_template_models import DiscoveryTemplate

router = APIRouter(prefix="/discovery-templates", tags=["发现模板"])


class DiscoveryTemplateCreate(BaseModel):
    name: str
    description: str | None = None
    protocol: str
    target_scope: str
    port_range: str | None = None
    credential_id: str | None = None
    scan_interval: int = 3600
    timeout: int = 300
    asset_type_mapping: str | None = None
    enabled: bool = True


class DiscoveryTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    protocol: str | None = None
    target_scope: str | None = None
    port_range: str | None = None
    credential_id: str | None = None
    scan_interval: int | None = None
    timeout: int | None = None
    asset_type_mapping: str | None = None
    enabled: bool | None = None


@router.get("")
async def list_discovery_templates(
    protocol: str | None = None,
    enabled: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """列出发发现模板."""
    stmt = select(DiscoveryTemplate).where(DiscoveryTemplate.id.isnot(None))
    count_stmt = select(sa_func.count()).select_from(DiscoveryTemplate)

    if protocol:
        stmt = stmt.where(DiscoveryTemplate.protocol == protocol)
        count_stmt = count_stmt.where(DiscoveryTemplate.protocol == protocol)
    if enabled is not None:
        stmt = stmt.where(DiscoveryTemplate.enabled == enabled)
        count_stmt = count_stmt.where(DiscoveryTemplate.enabled == enabled)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    result = await db.execute(
        stmt.order_by(DiscoveryTemplate.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(result.scalars().all())
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@router.post("")
async def create_discovery_template(data: DiscoveryTemplateCreate, db: AsyncSession = Depends(get_db)):
    """创建发现模板."""
    tmpl = DiscoveryTemplate(**data.model_dump())
    db.add(tmpl)
    await db.commit()
    await db.refresh(tmpl)
    return success(model_to_dict(tmpl))


@router.get("/{template_id}")
async def get_discovery_template(template_id: str, db: AsyncSession = Depends(get_db)):
    """获取发现模板详情."""
    result = await db.execute(select(DiscoveryTemplate).where(DiscoveryTemplate.id == template_id))
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        return success(None, message="模板不存在")
    return success(model_to_dict(tmpl))


@router.put("/{template_id}")
async def update_discovery_template(
    template_id: str, data: DiscoveryTemplateUpdate, db: AsyncSession = Depends(get_db)
):
    """更新发现模板."""
    result = await db.execute(select(DiscoveryTemplate).where(DiscoveryTemplate.id == template_id))
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        return success(None, message="模板不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(tmpl, k, v)
    await db.commit()
    await db.refresh(tmpl)
    return success(model_to_dict(tmpl))


@router.delete("/{template_id}")
async def delete_discovery_template(template_id: str, db: AsyncSession = Depends(get_db)):
    """删除发现模板."""
    result = await db.execute(select(DiscoveryTemplate).where(DiscoveryTemplate.id == template_id))
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        return success(None, message="模板不存在")
    if tmpl.is_builtin:
        return success(None, message="内置模板不可删除")
    await db.delete(tmpl)
    await db.commit()
    return success(message="已删除")


@router.post("/{template_id}/toggle")
async def toggle_discovery_template(template_id: str, db: AsyncSession = Depends(get_db)):
    """启用/禁用发现模板."""
    result = await db.execute(select(DiscoveryTemplate).where(DiscoveryTemplate.id == template_id))
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        return success(None, message="模板不存在")
    tmpl.enabled = not tmpl.enabled
    await db.commit()
    await db.refresh(tmpl)
    return success(model_to_dict(tmpl))
