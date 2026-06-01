"""AUTOPS config loader.

配置优先级:
1. 环境变量 (最高优先级)
2. configs/{profile}.yaml
3. 代码默认值 (仅用于本地开发)
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


def _detect_config_dir() -> Path:
    """自动检测配置目录，不硬编码特定机器路径."""
    candidates = [
        os.getenv("AUTOPS_CONFIG_DIR"),
        "/app/configs",
        Path(__file__).resolve().parents[3] / "configs",
    ]
    for c in candidates:
        if c and Path(c).is_dir():
            return Path(c)
    return Path("/app/configs")


_CONFIG_DIR = _detect_config_dir()


def _load_yaml(filename: str) -> dict:
    filepath = _CONFIG_DIR / filename
    if filepath.exists():
        with open(filepath) as f:
            return yaml.safe_load(f) or {}
    return {}


class DatabaseConfig(BaseSettings):
    dialect: Literal["mysql", "postgresql", "opengauss", "dm", "kingbase"] = "mysql"
    host: str = "127.0.0.1"
    port: int = 3306
    user: str = "autops"
    db_pass: str = ""
    database: str = "autops"
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False

    @property
    def url(self) -> str:
        from app.infra.db_dialect import DialectAdapter
        adapter = DialectAdapter(self.dialect)
        cred = f":{self.db_pass}" if self.db_pass else ""
        base_url = adapter.build_connection_url(
            self.user, cred.lstrip(":"), self.host, self.port, self.database
        )
        if adapter.is_mysql_compatible:
            return f"{base_url}?charset=utf8mb4"
        return base_url

    class Config:
        env_prefix = "DB_"


class RedisConfig(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 6379
    redis_pass: str = ""
    db: int = 0

    @property
    def url(self) -> str:
        auth = f":{self.redis_pass}@" if self.redis_pass else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"

    class Config:
        env_prefix = "REDIS_"


class SecurityConfig(BaseSettings):
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    access_token_expire_minutes: int = 480
    refresh_token_expire_days: int = 7

    @field_validator("jwt_secret")
    @classmethod
    def validate_secret(cls, v: str) -> str:
        env = os.getenv("AUTOPS_ENV", "dev")
        if env == "prod" and not v:
            raise ValueError("JWT_SECRET must be set in production")
        if env == "prod" and v in {
            "autops-secret-key-change-in-production",
            "change-me",
            "secret",
        }:
            raise ValueError("insecure JWT_SECRET in production")
        return v

    class Config:
        env_prefix = "JWT_"


class LLMConfig(BaseSettings):
    base_url: str = "http://127.0.0.1:8000/v1"
    model_name: str = "qwen3.5-0.8b"
    api_key: str = ""
    timeout_seconds: int = 60
    max_tokens: int = 1024
    temperature: float = 0.2

    class Config:
        env_prefix = "LLM_"


class AppConfig(BaseSettings):
    app_name: str = "AUTOPS"
    version: str = "0.5.0"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    config_dir: str = str(_CONFIG_DIR)
    env: Literal["dev", "test", "prod"] = "dev"
    enable_openapi_ui: bool = True
    enable_scheduler: bool = False

    # 子配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 从yaml文件覆盖配置
        db_yaml = _load_yaml("database.yaml")
        redis_yaml = _load_yaml("redis.yaml")
        llm_yaml = _load_yaml("llm.yaml")
        security_yaml = _load_yaml("security.yaml")

        if db_yaml:
            for k, v in db_yaml.items():
                if hasattr(self.database, k):
                    setattr(self.database, k, v)
        if redis_yaml:
            for k, v in redis_yaml.items():
                if hasattr(self.redis, k):
                    setattr(self.redis, k, v)
        if llm_yaml:
            for k, v in llm_yaml.items():
                if hasattr(self.llm, k):
                    setattr(self.llm, k, v)
        if security_yaml:
            for k, v in security_yaml.items():
                if hasattr(self.security, k):
                    setattr(self.security, k, v)

    class Config:
        env_prefix = "AUTOPS_"


@lru_cache
def get_config() -> AppConfig:
    return AppConfig()
