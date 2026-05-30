"""AUTOPS 后端应用入口."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.health import router as health_router
from app.common.exceptions import AppError, app_error_handler, generic_error_handler
from app.common.trace import TraceIdMiddleware
from app.infra.config import get_config
from app.infra.database import init_db_engine
from app.infra.redis_client import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期."""
    # Startup
    config = get_config()
    init_db_engine()
    yield
    # Shutdown
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
