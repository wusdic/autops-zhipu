"""AUTOPS 后端应用入口."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.health import router as health_router
from app.common.exceptions import AppError, app_error_handler, generic_error_handler
from app.common.event_handlers import register_all_handlers
from app.common.trace import TraceIdMiddleware
from app.api.websocket import register_ws_event_bridges
from app.infra.config import get_config
from app.infra.database import init_db_engine, Base
from app.infra.redis_client import close_redis

# 确保所有模型注册到Base.metadata
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


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期."""
    # Startup
    config = get_config()
    init_db_engine()
    # 自动建表
    from app.infra.database import engine as _engine
    if _engine:
        async with _engine.begin() as conn:
            from sqlalchemy import text
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ensured")
    register_all_handlers()
    register_ws_event_bridges()
    # 注册资产创建→立即采集事件
    from app.common.events import get_event_bus, AssetEvents
    from app.workers.scheduler import on_asset_created_run_collection
    bus = get_event_bus()
    bus.subscribe(AssetEvents.ASSET_CREATED, on_asset_created_run_collection)
    # 启动定时采集调度器 (5分钟间隔)
    from app.workers.scheduler import get_scheduler
    scheduler = get_scheduler()
    await scheduler.start(interval=300)
    logger.info("Scheduler started")
    yield
    # Shutdown
    await scheduler.stop()
    await close_redis()


def create_app() -> FastAPI:
    """创建 FastAPI 应用."""
    config = get_config()

    app = FastAPI(
        title=config.app_name,
        version=config.version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TraceIdMiddleware)

    # 异常处理
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)

    # 路由
    app.include_router(health_router)  # /health, /ready at root level
    app.include_router(api_router, prefix=config.api_prefix)

    return app


app = create_app()
