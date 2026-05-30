"""通用 CRUD Service 基类."""

from __future__ import annotations

import json
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.common.repository import BaseRepository

ModelType = TypeVar("ModelType")


class CRUDService(Generic[ModelType]):
    """通用增删改查服务."""

    repo: BaseRepository[ModelType]

    def __init__(self, session: AsyncSession, repo: BaseRepository[ModelType]):
        self.session = session
        self.repo = repo

    async def get_by_id(self, id: str) -> ModelType:
        obj = await self.repo.get_by_id(id)
        if not obj:
            raise NotFoundError(f"记录 {id} 不存在")
        return obj

    async def list_paginated(
        self,
        filters: dict | None = None,
        page: int = 1,
        page_size: int = 20,
        order_by: str | None = None,
    ) -> tuple[list[ModelType], int]:
        stmt = select(self.repo.model_class)
        count_stmt = select(func.count()).select_from(self.repo.model_class)

        if filters:
            for key, value in filters.items():
                if hasattr(self.repo.model_class, key) and value is not None:
                    col = getattr(self.repo.model_class, key)
                    stmt = stmt.where(col == value)
                    count_stmt = count_stmt.where(col == value)

        if order_by and hasattr(self.repo.model_class, order_by):
            stmt = stmt.order_by(getattr(self.repo.model_class, order_by).desc())
        else:
            stmt = stmt.order_by(self.repo.model_class.id.desc())

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def create(self, **kwargs: Any) -> ModelType:
        obj = await self.repo.create(**kwargs)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, id: str, **kwargs: Any) -> ModelType:
        obj = await self.get_by_id(id)
        for key, value in kwargs.items():
            if hasattr(obj, key) and value is not None:
                setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: str) -> None:
        obj = await self.get_by_id(id)
        await self.session.delete(obj)
        await self.session.flush()


def model_to_dict(obj: Any) -> dict:
    """将 SQLAlchemy model 转为 dict，处理 JSON 字段."""
    result = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.key)
        if val is not None and isinstance(col.type, (
            __import__("sqlalchemy").DateTime,
        )):
            val = val.isoformat() if hasattr(val, "isoformat") else str(val)
        result[col.key] = val
    return result
