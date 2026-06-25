"""全局认证与授权依赖.

提供 FastAPI 依赖函数 ``require_auth``，在请求进入业务路由前
校验 JWT Token 并将当前用户注入 ``request.state.current_user``。

使用方式（全局挂载）::

    from app.common.auth_dependency import require_auth

    app.include_router(api_router, prefix=..., dependencies=[Depends(require_auth)])

或在单个路由上::

    @router.get("/users", dependencies=[Depends(require_auth)])
    async def list_users(...): ...
"""

from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.auth import decode_token
from app.common.exceptions import PermissionDeniedError, UnauthorizedError
from app.domains.governance.models import User
from app.infra.database import get_db

# Bearer token 提取器 — 自动从 Authorization header 读取
# auto=False 使得未提供 token 时不自动返回 403，而是交由 require_auth 处理
_bearer_scheme = HTTPBearer(auto=False)

# 拥有这些角色之一的用户视为管理员，require_admin 会放行
_ADMIN_ROLES = {"super_admin", "admin"}


async def _load_user(db: AsyncSession, user_id: str) -> User | None:
    """加载用户并预加载 roles 关系（避免 async 上下文 lazy-load 报错）."""
    result = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """全局认证依赖.

    从 Authorization: Bearer <token> 中解析 JWT，
    验证用户存在且状态正常，将 User 对象挂到 ``request.state.current_user``。

    Raises:
        UnauthorizedError: 缺少 token / token 无效 / 用户不存在或已禁用。
    """
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("缺少认证 Token")

    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Token 中缺少用户标识")

    user = await _load_user(db, user_id)
    if user is None or user.is_deleted or user.status != "active":
        raise UnauthorizedError("用户不存在或已禁用")

    # 注入到 request.state 供后续 handler 使用
    request.state.current_user = user
    return user


async def get_current_user(request: Request) -> User:
    """从 request.state 获取当前已认证用户（require_auth 执行后可用）.

    在已经挂载 require_auth 的路由中，可直接用此函数获取用户::

        @router.get("/me")
        async def me(user: User = Depends(get_current_user)):
            return user
    """
    user = getattr(request.state, "current_user", None)
    if user is None:
        raise UnauthorizedError("未认证")
    return user


async def require_admin(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """授权依赖：仅允许管理员（super_admin / admin 角色）访问.

    自包含：会从 Authorization header 解析 token、加载用户与 roles、
    校验管理员角色，并把 current_user 注入 request.state。

    用法::

        @router.post("/users", dependencies=[Depends(require_admin)])
        async def create_user(...): ...

    Raises:
        UnauthorizedError: 缺少/无效 token 或用户不可用。
        PermissionDeniedError: 当前用户不具备管理员角色。
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise UnauthorizedError("缺少认证 Token")
    token = auth_header[7:]
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Token 中缺少用户标识")

    user = await _load_user(db, user_id)
    if user is None or user.is_deleted or user.status != "active":
        raise UnauthorizedError("用户不存在或已禁用")

    request.state.current_user = user

    role_names = {r.name for r in user.roles}
    if not (role_names & _ADMIN_ROLES):
        raise PermissionDeniedError("需要管理员权限")
    return user
