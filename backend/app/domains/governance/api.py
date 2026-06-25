"""治理中心 API 路由."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth_dependency import require_admin
from app.common.response import paginate, success
from app.domains.governance.schemas import (
    ApiKeyCreate,
    ApiKeyCreateResponse,
    ApiKeyResponse,
    LoginRequest,
    PasswordChange,
    RoleCreate,
    RoleResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.domains.governance.service import ApiKeyService, AuthService, UserService
from app.infra.database import get_db

router = APIRouter(tags=["认证"])
user_router = APIRouter(prefix="/users", tags=["用户管理"])
role_router = APIRouter(prefix="/roles", tags=["角色管理"])
apikey_router = APIRouter(prefix="/api-keys", tags=["API Key"])


def _get_auth(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


def _get_user_svc(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


# --- 认证 ---
@router.post("/auth/login")
async def login(
    data: LoginRequest, request: Request, svc: AuthService = Depends(_get_auth)
):
    result = await svc.login(data, ip=request.client.host if request.client else None)
    return success(result)


@router.post("/auth/logout")
async def logout():
    return success(message="已登出")


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/auth/refresh")
async def refresh(data: RefreshRequest, svc: AuthService = Depends(_get_auth)):
    # refresh_token 从请求体获取，不再走 query 参数（避免 token 进入日志/历史）
    result = await svc.refresh_token(data.refresh_token)
    return success(result)


@router.get("/auth/me")
async def me(request: Request, svc: AuthService = Depends(_get_auth)):
    auth_header = request.headers.get("Authorization", "")
    token = (
        auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    )
    if not token:
        from app.common.exceptions import ValidationError

        raise ValidationError("缺少认证 Token")
    user = await svc.get_current_user(token)
    return success(UserResponse.model_validate(user).model_dump())


@router.put("/auth/password")
async def change_password(
    data: PasswordChange,
    request: Request,
    auth: AuthService = Depends(_get_auth),
    user_svc: UserService = Depends(_get_user_svc),
):
    # 从 Authorization header 提取 token（不再从 query param 暴露）
    auth_header = request.headers.get("Authorization", "")
    token = (
        auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    )
    if not token:
        from app.common.exceptions import UnauthorizedError

        raise UnauthorizedError("缺少认证 Token")
    user = await auth.get_current_user(token)
    await user_svc.change_password(user.id, data.old_password, data.new_password)
    return success(message="密码已修改")


# --- 用户 CRUD ---
# 用户信息属敏感数据，所有读写均要求管理员权限，防止越权读取 PII / 改他人角色提权。
@user_router.get("", dependencies=[Depends(require_admin)])
async def list_users(
    page: int = 1,
    page_size: int = 20,
    svc: UserService = Depends(_get_user_svc),
):
    items, total = await svc.list_users(page=page, page_size=page_size)
    return paginate(
        [UserResponse.model_validate(u).model_dump() for u in items],
        total,
        page,
        page_size,
    )


@user_router.post("", dependencies=[Depends(require_admin)])
async def create_user(data: UserCreate, svc: UserService = Depends(_get_user_svc)):
    user = await svc.create_user(data)
    return success(UserResponse.model_validate(user).model_dump())


@user_router.get("/{user_id}", dependencies=[Depends(require_admin)])
async def get_user(user_id: str, svc: UserService = Depends(_get_user_svc)):
    user = await svc.get_user(user_id)
    return success(UserResponse.model_validate(user).model_dump())


@user_router.put("/{user_id}", dependencies=[Depends(require_admin)])
async def update_user(
    user_id: str, data: UserUpdate, svc: UserService = Depends(_get_user_svc)
):
    user = await svc.update_user(user_id, data)
    return success(UserResponse.model_validate(user).model_dump())


@user_router.delete("/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(user_id: str, svc: UserService = Depends(_get_user_svc)):
    await svc.delete_user(user_id)
    return success(message="用户已删除")


# --- 角色 ---
@role_router.get("", dependencies=[Depends(require_admin)])
async def list_roles(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from app.domains.governance.models import Role

    q = select(Role).order_by(Role.created_at)
    result = await db.execute(q)
    roles = result.scalars().all()
    data = []
    for r in roles:
        d = RoleResponse.model_validate(r)
        data.append(d.model_dump())
    return paginate(data, len(data), page, page_size)


@role_router.post("", dependencies=[Depends(require_admin)])
async def create_role(data: RoleCreate, db: AsyncSession = Depends(get_db)):
    from app.domains.governance.models import Role

    role = Role(
        name=data.name,
        display_name=data.display_name,
        description=data.description,
        permissions=json.dumps(data.permissions),
    )
    db.add(role)
    await db.flush()
    return success(RoleResponse.model_validate(role).model_dump())


# --- API Key ---
@apikey_router.get("")
async def list_api_keys(request: Request, auth: AuthService = Depends(_get_auth)):
    auth_header = request.headers.get("Authorization", "")
    token = (
        auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    )
    if not token:
        from app.common.exceptions import ValidationError

        raise ValidationError("缺少认证 Token")
    user = await auth.get_current_user(token)
    svc = ApiKeyService(auth.session)
    keys = await svc.list_keys(user.id)
    return success([ApiKeyResponse.model_validate(k).model_dump() for k in keys])


async def _current_user_from_header(request: Request, auth: AuthService):
    """从 Authorization Bearer 头解析当前用户（不再用 query token）."""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header[7:] if auth_header.startswith("Bearer ") else ""
    if not token:
        from app.common.exceptions import UnauthorizedError

        raise UnauthorizedError("缺少认证 Token")
    return await auth.get_current_user(token)


@apikey_router.post("")
async def create_api_key(
    data: ApiKeyCreate,
    request: Request,
    auth: AuthService = Depends(_get_auth),
):
    user = await _current_user_from_header(request, auth)
    svc = ApiKeyService(auth.session)
    api_key, raw_key = await svc.create_key(user.id, data)
    resp = ApiKeyCreateResponse.model_validate(api_key).model_dump()
    resp["key"] = raw_key
    return success(resp)


@apikey_router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str, request: Request, auth: AuthService = Depends(_get_auth)
):
    user = await _current_user_from_header(request, auth)
    svc = ApiKeyService(auth.session)
    await svc.revoke_key(key_id, user.id)
    return success(message="API Key 已撤销")


class ApiKeyPatch(BaseModel):
    name: str | None = None
    scope: list[str] | None = None
    expires_days: int | None = None


@apikey_router.patch("/{key_id}")
async def patch_api_key(
    key_id: str,
    data: ApiKeyPatch,
    request: Request,
    auth: AuthService = Depends(_get_auth),
):
    """部分更新 API Key."""
    user = await _current_user_from_header(request, auth)
    svc = ApiKeyService(auth.session)
    updated = await svc.update_key(
        key_id, user.id, **data.model_dump(exclude_unset=True)
    )
    return success(ApiKeyResponse.model_validate(updated).model_dump())
