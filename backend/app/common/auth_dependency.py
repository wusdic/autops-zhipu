"""全局认证依赖.

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

from app.common.auth import decode_token
from app.common.exceptions import UnauthorizedError
from app.domains.governance.models import User
from app.infra.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

# Bearer token 提取器 — 自动从 Authorization header 读取
# auto=False 使得未提供 token 时不自动返回 403，而是交由 require_auth 处理
_bearer_scheme = HTTPBearer(auto=False)


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

    user = await db.get(User, user_id)
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
