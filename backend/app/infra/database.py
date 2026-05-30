"""AUTOPS 数据库基础配置."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.infra.config import get_config

engine = None
async_session_factory = None


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类."""

    pass


def init_db_engine():
    """初始化数据库引擎."""
    global engine, async_session_factory
    config = get_config()
    engine = create_async_engine(
        config.database.url,
        pool_size=config.database.pool_size,
        max_overflow=config.database.max_overflow,
        echo=config.database.echo,
        pool_pre_ping=True,
    )
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：获取数据库会话."""
    if async_session_factory is None:
        init_db_engine()
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
