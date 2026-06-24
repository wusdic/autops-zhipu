"""全局认证中间件.

基于 Starlette 中间件实现，按路径白名单放行公开端点（login/refresh/health/docs），
其余所有 ``/api/v1/`` 请求强制要求有效 JWT。

相比 FastAPI ``dependencies=[Depends(require_auth)]`` 的方案，
中间件不需要修改 210 个路由文件，且可以细粒度按路径白名单控制。
"""
from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.common.auth import decode_token
from app.common.response import error

logger = logging.getLogger(__name__)

# ── 不需要认证的路径前缀（精确匹配或前缀匹配）──
PUBLIC_PATHS: frozenset[str] = frozenset({
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
})

PUBLIC_PREFIXES: tuple[str, ...] = (
    "/health",
    "/ready",
    "/docs",
    "/redoc",
    "/openapi.json",
)

# WebSocket 升级请求由 WebSocket 路由内部处理 token，不走 HTTP 中间件


class AuthMiddleware(BaseHTTPMiddleware):
    """JWT 认证中间件.

    - 放行 PUBLIC_PATHS / PUBLIC_PREFIXES / 非 /api 前缀的请求
    - 其余请求要求 ``Authorization: Bearer <token>``，解析失败返回 401
    - 成功后将 user_id 注入 ``request.state.user_id``
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 静态资源 / 健康检查 / API 文档 — 放行
        if path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES):
            return await call_next(request)

        # 非 API 路径（如 /）放行
        if not path.startswith("/api"):
            return await call_next(request)

        # WebSocket 升级请求 — 由 ws 路由内部鉴权，中间件放行
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        # 提取 Bearer token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return _unauthorized("缺少认证 Token")

        token = auth_header[7:]  # len("Bearer ") == 7

        try:
            payload = decode_token(token)
        except Exception:
            return _unauthorized("Token 无效或已过期")

        user_id = payload.get("sub")
        if not user_id:
            return _unauthorized("Token 中缺少用户标识")

        # 注入到 request.state 供后续 handler 使用
        request.state.user_id = user_id
        request.state.username = payload.get("username", "")

        return await call_next(request)


def _unauthorized(message: str = "未认证") -> JSONResponse:
    """返回 401 JSON 响应，保持与 AppError 相同的响应结构."""
    return JSONResponse(
        status_code=401,
        content=error(code=100, message=message).model_dump(),
    )
