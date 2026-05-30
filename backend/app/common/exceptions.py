"""统一异常处理."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from app.common.response import error


class AppError(Exception):
    """业务异常基类."""

    def __init__(self, code: int, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    """资源不存在."""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(code=200, message=message, status_code=404)


class DuplicateError(AppError):
    """资源重复."""

    def __init__(self, message: str = "资源已存在"):
        super().__init__(code=201, message=message, status_code=409)


class PermissionDeniedError(AppError):
    """权限不足."""

    def __init__(self, message: str = "权限不足"):
        super().__init__(code=103, message=message, status_code=403)


class UnauthorizedError(AppError):
    """未认证."""

    def __init__(self, message: str = "未认证"):
        super().__init__(code=100, message=message, status_code=401)


class ValidationError(AppError):
    """参数错误."""

    def __init__(self, message: str = "参数验证失败"):
        super().__init__(code=10, message=message, status_code=422)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """业务异常处理器."""
    trace_id = getattr(request.state, "trace_id", "")
    return JSONResponse(
        status_code=exc.status_code,
        content=error(exc.code, exc.message, trace_id).model_dump(),
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器."""
    trace_id = getattr(request.state, "trace_id", "")
    return JSONResponse(
        status_code=500,
        content=error(1, "服务器内部错误", trace_id).model_dump(),
    )
