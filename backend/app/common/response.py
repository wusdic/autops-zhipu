"""统一响应结构."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    """统一 API 响应."""

    code: int = 0
    message: str = "success"
    data: T | None = None
    trace_id: str = ""


class PageData(BaseModel, Generic[T]):
    """分页数据."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


def success(data: Any = None, message: str = "success", trace_id: str = "") -> Response:
    """成功响应.

    兼容两种调用方式::

        success(data)
        success(message="已删除")

    历史上大量删除/登出类路由使用 ``success(message=...)``，因此 ``message``
    必须作为显式参数存在，否则会在运行时抛 ``TypeError``。
    """
    return Response(code=0, message=message, data=data, trace_id=trace_id)


def error(code: int, message: str, trace_id: str = "") -> Response:
    """错误响应."""
    return Response(code=code, message=message, data=None, trace_id=trace_id)


def paginate(
    items: list, total: int, page: int, page_size: int, trace_id: str = ""
) -> Response:
    """分页响应."""
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return Response(
        code=0,
        message="success",
        data=PageData(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
        trace_id=trace_id,
    )
