"""AUTOPS 数据库基础配置."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.infra.config import get_config
from app.infra.db_dialect import DialectAdapter

logger = logging.getLogger(__name__)

engine = None
async_session_factory = None


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类."""

    pass


def init_db_engine():
    """初始化数据库引擎."""
    global engine, async_session_factory
    config = get_config()
    db_conf = config.database
    adapter = DialectAdapter(db_conf.dialect)
    logger.info("Initializing DB engine: dialect=%s, connector=%s", adapter.config.name, adapter.config.connector)
    engine = create_async_engine(
        db_conf.url,
        pool_size=db_conf.pool_size,
        max_overflow=db_conf.max_overflow,
        echo=db_conf.echo,
        pool_pre_ping=True,
    )
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """获取 session factory（供非 DI 场景使用，如 worker/event outbox）."""
    if async_session_factory is None:
        init_db_engine()
    return async_session_factory


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：获取数据库会话.

    请求结束后自动 commit；异常时 rollback。
    注意：SQLAlchemy AsyncSession 不支持在 yield 之后检查 dirty/new/deleted
    集合（会触发 IllegalStateChangeError），因此无条件 commit。
    """
    if async_session_factory is None:
        init_db_engine()
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_db_engine() -> None:
    """关闭数据库引擎（graceful shutdown 用）."""
    global engine
    if engine:
        await engine.dispose()
        logger.info("DB engine disposed")
