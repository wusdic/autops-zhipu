"""通用 Repository 基类."""

from __future__ import annotations

import uuid
from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import Select, func, select

from app.infra.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """通用数据访问层基类."""

    def __init__(self, session_or_model, model_or_session=None):
        # Support both BaseRepository(session, Model) and BaseRepository(Model, session)
        from sqlalchemy.ext.asyncio import AsyncSession as _AS

        if isinstance(session_or_model, _AS):
            # First arg is session: BaseRepository(session, Model)
            self.session = session_or_model
            self.model = model_or_session
        elif isinstance(model_or_session, _AS):
            # Second arg is session: BaseRepository(Model, session)
            self.model = session_or_model
            self.session = model_or_session
        else:
            raise TypeError(
                f"Expected (AsyncSession, Model) or (Model, AsyncSession), got ({type(session_or_model)}, {type(model_or_session)})"
            )

    async def get_by_id(self, id: str) -> ModelType | None:
        """根据 ID 获取单条记录."""
        return await self.session.get(self.model, id)

    async def get_by_id_or_raise(self, id: str) -> ModelType:
        """根据 ID 获取，不存在则抛异常."""
        obj = await self.get_by_id(id)
        if obj is None:
            from app.common.exceptions import NotFoundError

            raise NotFoundError(f"{self.model.__name__} 不存在")
        return obj

    async def get_multi(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        filters: list | None = None,
        order_by: Any | None = None,
    ) -> tuple[Sequence[ModelType], int]:
        """分页查询."""
        query: Select = select(self.model)

        if filters:
            for f in filters:
                query = query.where(f)

        # 总数
        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_q)).scalar() or 0

        # 排序
        if order_by is not None:
            query = query.order_by(order_by)
        else:
            query = query.order_by(self.model.created_at.desc())

        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = result.scalars().all()

        return items, total

    async def create(self, **kwargs: Any) -> ModelType:
        """创建记录."""
        if "id" not in kwargs and hasattr(self.model, "id"):
            kwargs.setdefault("id", str(uuid.uuid4()))
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(self, id: str, **kwargs: Any) -> ModelType:
        """更新记录."""
        obj = await self.get_by_id_or_raise(id)
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        await self.session.flush()
        return obj

    async def delete(self, id: str) -> None:
        """物理删除."""
        obj = await self.get_by_id_or_raise(id)
        await self.session.delete(obj)
        await self.session.flush()

    async def soft_delete(self, id: str) -> ModelType:
        """软删除."""
        from datetime import datetime, timezone

        obj = await self.get_by_id_or_raise(id)
        obj.is_deleted = True
        obj.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
        return obj
