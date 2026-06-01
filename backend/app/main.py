"""AUTOPS 后端应用入口.

职责:
1. 创建 FastAPI app
2. 初始化配置和基础设施
3. 注册中间件、异常处理器、路由
4. 注册事件处理器 (dev模式)
5. 可选启动scheduler (dev模式, 通过AUTOPS_ENABLE_SCHEDULER控制)

生产环境应使用独立worker进程运行scheduler和事件消费者。
"""

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
from app.infra.database import init_db_engine
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
    config = get_config()
    init_db_engine()

    from app.common.events import get_event_bus, AssetEvents
    bus = get_event_bus()
    bus.enable_outbox()

    if config.allow_inprocess_events:
        # 开发模式: 注册 handler 并 in-process 分发事件
        register_all_handlers()
        register_ws_event_bridges()
        logger.info("EventBus mode: in-process (allow_inprocess_events=True)")

        # 注册资产创建事件 -> 立即采集
        from app.workers.scheduler import on_asset_created_run_collection
        bus.subscribe(AssetEvents.ASSET_CREATED, on_asset_created_run_collection)
    else:
        # 生产模式: 仅写入 outbox，handler 由 worker 进程消费
        logger.info("EventBus mode: outbox-only (allow_inprocess_events=False, worker consumes)")
        # 仍然注册 WebSocket 桥接（推送事件给前端）
        register_ws_event_bridges()

    # 仅在dev模式且显式启用时启动scheduler (生产环境应使用独立worker)
    scheduler = None
    if config.enable_scheduler:
        from app.workers.scheduler import get_scheduler
        scheduler = get_scheduler()
        await scheduler.start(interval=300)
        logger.info("Scheduler started (in-process, dev mode)")
    else:
        logger.info("Scheduler NOT started (use AUTOPS_ENABLE_SCHEDULER=true or worker runner)")

    yield

    # Shutdown
    if scheduler:
        await scheduler.stop()
    from app.infra.database import close_db_engine
    await close_db_engine()
    await close_redis()
    logger.info("AUTOPS stopped")


def create_app() -> FastAPI:
    """创建 FastAPI 应用."""
    config = get_config()

    app = FastAPI(
        title=config.app_name,
        version=config.version,
        docs_url="/docs" if config.enable_openapi_ui else None,
        redoc_url="/redoc" if config.enable_openapi_ui else None,
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
    app.include_router(health_router)
    app.include_router(api_router, prefix=config.api_prefix)

    return app


app = create_app()
