"""AUTOPS 后端 API 进程入口.

职责（严格边界）:
1. 创建 FastAPI app
2. 初始化配置、数据库引擎、Redis
3. 注册中间件、异常处理器、HTTP路由
4. 启用 outbox 模式（事件写库，不直接处理）
5. 注册 WebSocket 桥接（推送事件给前端）

禁止事项:
- 不自动建表（使用 alembic upgrade head）
- 不注册业务事件 handler
- 不启动 scheduler
- 不订阅业务事件
- 不执行自动化脚本

后台事件消费、采集调度、自动化执行由 WorkerRunner（app.workers.runner）独立运行。
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.health import router as health_router
from app.common.exceptions import AppError, app_error_handler, generic_error_handler
from app.common.trace import TraceIdMiddleware
from app.common.auth_middleware import AuthMiddleware
from app.api.websocket import register_ws_event_bridges
from app.infra.config import get_config
from app.infra.database import init_db_engine, close_db_engine
from app.infra.redis_client import close_redis

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """API 进程生命周期 — 只负责基础设施，不启动任何后台业务逻辑."""
    config = get_config()
    init_db_engine()

    # 启用 outbox 模式：API 进程只写 outbox，不直接 dispatch
    from app.common.events import get_event_bus
    bus = get_event_bus()
    bus.enable_outbox()
    logger.info("API process: outbox mode enabled (events persisted, worker consumes)")

    # WebSocket 桥接：推送事件给前端
    register_ws_event_bridges()

    yield

    # Shutdown
    await close_db_engine()
    await close_redis()
    logger.info("AUTOPS API process stopped")


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
    # CORS: 当 allow_credentials=True 时，allow_origins 不能是 ["*"]（浏览器规范）
    # 如果 cors_origins 为 ["*"]，则关闭 credentials 以兼容
    cors_origins = config.cors_origins
    allow_credentials = "*" not in cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TraceIdMiddleware)
    # JWT 认证中间件 — 放行 login/refresh/health/docs，保护其余所有 /api/ 路由
    app.add_middleware(AuthMiddleware)

    # 异常处理
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)

    # 路由
    app.include_router(health_router)
    app.include_router(api_router, prefix=config.api_prefix)

    return app


app = create_app()
