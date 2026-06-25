"""配置中心 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import Response, paginate, success
from app.common.crud_service import model_to_dict
from app.infra.database import get_db
from app.domains.config.service import ConfigService
from app.domains.config.schemas import (
    ConfigDefinitionCreate, ConfigVersionCreate,
    CredentialCreate, ConfigBindingCreate,
)

router = APIRouter(prefix="/configs", tags=["配置中心"])
cred_router = APIRouter(prefix="/credentials", tags=["凭证管理"])


def _get_service(db: AsyncSession = Depends(get_db)) -> ConfigService:
    return ConfigService(db)


@router.get("/definitions")
async def list_definitions(
    config_type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: ConfigService = Depends(_get_service),
):
    items, total = await svc.list_definitions(config_type, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@router.post("/definitions")
async def create_definition(data: ConfigDefinitionCreate, svc: ConfigService = Depends(_get_service)):
    defn = await svc.create_definition(**data.model_dump())
    return success(model_to_dict(defn))


@router.get("/definitions/{def_id}")
async def get_definition(def_id: str, svc: ConfigService = Depends(_get_service)):
    defn = await svc.get_definition(def_id)
    return success(model_to_dict(defn))


@router.post("/definitions/{def_id}/versions")
async def create_version(def_id: str, data: ConfigVersionCreate, svc: ConfigService = Depends(_get_service)):
    ver = await svc.create_version(def_id, data.content)
    return success(model_to_dict(ver))


@router.get("/definitions/{def_id}/versions")
async def list_versions(def_id: str, svc: ConfigService = Depends(_get_service)):
    versions = await svc.list_versions(def_id)
    return success([model_to_dict(v) for v in versions])


@router.post("/versions/{version_id}/publish")
async def publish_version(version_id: str, svc: ConfigService = Depends(_get_service)):
    ver = await svc.publish_version(version_id)
    return success(model_to_dict(ver))


@router.get("/definitions/{def_id}/diff")
async def diff_versions(
    def_id: str,
    v_a: str = Query(..., description="版本A的ID"),
    v_b: str = Query(..., description="版本B的ID"),
    svc: ConfigService = Depends(_get_service),
):
    """对比两个配置版本的差异."""
    result = await svc.diff_versions(def_id, v_a, v_b)
    return success(result)


@router.post("/definitions/{def_id}/rollback")
async def rollback_version(
    def_id: str,
    data: dict,
    svc: ConfigService = Depends(_get_service),
):
    """回滚配置到指定版本."""
    target_version_id = data.get("target_version_id", "")
    user_id = data.get("user_id", "")
    ver = await svc.rollback_version(def_id, target_version_id, user_id)
    return success(model_to_dict(ver))


@router.get("/definitions/{def_id}/drift")
async def detect_drift(def_id: str, svc: ConfigService = Depends(_get_service)):
    """检测配置漂移."""
    result = await svc.detect_drift(def_id)
    return success(result)


@cred_router.get("")
async def list_credentials(
    cred_type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: ConfigService = Depends(_get_service),
):
    items, total = await svc.list_credentials(cred_type, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@cred_router.post("")
async def create_credential(data: CredentialCreate, svc: ConfigService = Depends(_get_service)):
    cred = await svc.create_credential(
        name=data.name, cred_type=data.cred_type,
        data=data.data, description=data.description,
    )
    return success(model_to_dict(cred))


@cred_router.get("/{cred_id}")
async def get_credential(cred_id: str, svc: ConfigService = Depends(_get_service)):
    cred = await svc.get_credential(cred_id)
    return success(model_to_dict(cred))


class CredentialUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    data: str | None = None


@cred_router.put("/{cred_id}")
async def update_credential(cred_id: str, body: CredentialUpdate, svc: ConfigService = Depends(_get_service)):
    cred = await svc.update_credential(
        cred_id, name=body.name, description=body.description, data=body.data
    )
    return success(model_to_dict(cred))


@cred_router.delete("/{cred_id}")
async def delete_credential(cred_id: str, svc: ConfigService = Depends(_get_service)):
    await svc.delete_credential(cred_id)
    return success(message="凭证已删除")


@cred_router.post("/{cred_id}/bind")
async def bind_credential(cred_id: str, data: ConfigBindingCreate, svc: ConfigService = Depends(_get_service)):
    binding = await svc.bind_credential(cred_id, data.target_id)
    return success(model_to_dict(binding))


@router.get("/inheritance")
async def get_config_inheritance(svc: ConfigService = Depends(_get_service)):
    """获取配置继承关系."""
    result = await svc.get_inheritance()
    return success(result)
