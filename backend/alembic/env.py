"""Alembic 环境配置."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.infra.config import get_config
from app.infra.database import Base

# 导入所有模型以确保 Base.metadata 包含所有表
import app.domains.asset.models          # noqa: F401
import app.domains.asset.discovery_models  # noqa: F401
import app.domains.config.models          # noqa: F401
import app.domains.collector.models       # noqa: F401
import app.domains.event.models           # noqa: F401
import app.domains.alert.models           # noqa: F401
import app.domains.policy.models          # noqa: F401
import app.domains.automation.models      # noqa: F401
import app.domains.log.models             # noqa: F401
import app.domains.knowledge.models       # noqa: F401
import app.domains.ticket.models          # noqa: F401
import app.domains.governance.models      # noqa: F401
import app.domains.state.models           # noqa: F401
import app.domains.notification.models    # noqa: F401
import app.domains.inspection.models      # noqa: F401
import app.domains.anomaly.models         # noqa: F401
import app.domains.report.models         # noqa: F401
import app.domains.alert.threshold_models  # noqa: F401
import app.domains.notification.rule_models  # noqa: F401
import app.domains.asset.discovery_template_models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式：生成 SQL 脚本."""
    url = get_config().database.url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """在线模式：异步执行迁移."""
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = get_config().database.url

    connectable = async_engine_from_config(
        cfg,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式入口."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
