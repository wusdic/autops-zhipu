"""资产中心 API."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import Response, paginate, success
from app.domains.asset.schemas import (
    AssetCreate, AssetGroupCreate, AssetGroupResponse, AssetImportItem,
    AssetRelationCreate, AssetRelationResponse, AssetResponse,
    AssetTimelineResponse, AssetUpdate,
)
from app.domains.asset.service import AssetService
from app.infra.database import get_db

router = APIRouter(prefix="/assets", tags=["资产"])


def _get_service(db: AsyncSession = Depends(get_db)) -> AssetService:
    return AssetService(db)


def _to_dict(asset) -> dict:
    """手动转 dict 避免 lazy load 问题."""
    return {
        "id": asset.id,
        "name": asset.name,
        "asset_type": asset.asset_type,
        "ip": asset.ip,
        "port": asset.port,
        "hostname": asset.hostname,
        "os_type": asset.os_type,
        "os_version": asset.os_version,
        "description": asset.description,
        "business_system": asset.business_system,
        "environment": asset.environment,
        "location": asset.location,
        "status": asset.status,
        "health_status": asset.health_status,
        "reachability": asset.reachability,
        "tags": asset.tags,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
        "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
    }


def _rel_to_dict(r) -> dict:
    return {
        "id": r.id, "source_asset_id": r.source_asset_id,
        "target_asset_id": r.target_asset_id, "relation_type": r.relation_type,
        "description": r.description,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _timeline_to_dict(t) -> dict:
    return {
        "id": t.id, "asset_id": t.asset_id, "event_type": t.event_type,
        "title": t.title, "detail": t.detail, "source": t.source,
        "source_id": t.source_id,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


# --- 资产 CRUD ---
@router.get("")
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    asset_type: str | None = None,
    status: str | None = None,
    health_status: str | None = None,
    business_system: str | None = None,
    environment: str | None = None,
    search: str | None = None,
    svc: AssetService = Depends(_get_service),
):
    items, total = await svc.list_assets(
        page=page, page_size=page_size, asset_type=asset_type,
        status=status, health_status=health_status,
        business_system=business_system, environment=environment,
        search=search,
    )
    return paginate([_to_dict(a) for a in items], total, page, page_size)


@router.post("")
async def create_asset(data: AssetCreate, svc: AssetService = Depends(_get_service)):
    asset = await svc.create_asset(data)
    return success(_to_dict(asset))


@router.get("/{asset_id}")
async def get_asset(asset_id: str, svc: AssetService = Depends(_get_service)):
    asset = await svc.get_asset(asset_id)
    return success(_to_dict(asset))


@router.put("/{asset_id}")
async def update_asset(
    asset_id: str, data: AssetUpdate, svc: AssetService = Depends(_get_service)
):
    asset = await svc.update_asset(asset_id, data)
    return success(_to_dict(asset))


@router.delete("/{asset_id}")
async def delete_asset(asset_id: str, svc: AssetService = Depends(_get_service)):
    await svc.delete_asset(asset_id)
    return success(message="删除成功")


@router.post("/import")
async def import_assets(
    items: list[AssetImportItem], svc: AssetService = Depends(_get_service)
):
    created = await svc.import_assets(items)
    return success({"imported": len(created)})


# --- 资产关系 ---
@router.get("/{asset_id}/relations")
async def get_relations(asset_id: str, svc: AssetService = Depends(_get_service)):
    rels = await svc.get_relations(asset_id)
    return success([_rel_to_dict(r) for r in rels])


@router.post("/{asset_id}/relations")
async def add_relation(
    asset_id: str, data: AssetRelationCreate,
    svc: AssetService = Depends(_get_service),
):
    rel = await svc.add_relation(asset_id, data)
    return success(_rel_to_dict(rel))


# --- 资产时间线 ---
@router.get("/{asset_id}/timeline")
async def get_timeline(asset_id: str, svc: AssetService = Depends(_get_service)):
    events = await svc.get_timeline(asset_id)
    return success([_timeline_to_dict(e) for e in events])


# --- 分组 ---
group_router = APIRouter(prefix="/asset-groups", tags=["资产分组"])


@group_router.get("")
async def list_groups(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: AssetService = Depends(_get_service),
):
    items, total = await svc.list_groups(page=page, page_size=page_size)
    return paginate(
        [{"id": g.id, "name": g.name, "description": g.description,
          "parent_id": g.parent_id} for g in items],
        total, page, page_size,
    )


@group_router.post("")
async def create_group(data: AssetGroupCreate, svc: AssetService = Depends(_get_service)):
    group = await svc.create_group(data)
    return success({"id": group.id, "name": group.name, "description": group.description})


@group_router.post("/{group_id}/members")
async def add_member(group_id: str, asset_id: str, svc: AssetService = Depends(_get_service)):
    await svc.add_group_member(group_id, asset_id)
    return success(message="添加成功")


@group_router.delete("/{group_id}/members/{asset_id}")
async def remove_member(group_id: str, asset_id: str, svc: AssetService = Depends(_get_service)):
    await svc.remove_group_member(group_id, asset_id)
    return success(message="移除成功")
