"""AUTOPS 配置加载器."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


_CONFIG_DIR = Path(os.getenv("AUTOPS_CONFIG_DIR", "/home/zcxx/autops/configs"))


def _load_yaml(filename: str) -> dict:
    filepath = _CONFIG_DIR / filename
    if filepath.exists():
        with open(filepath) as f:
            return yaml.safe_load(f) or {}
    return {}


class DatabaseConfig(BaseSettings):
    """数据库配置."""

    host: str = "127.0.0.1"
    port: int = 3306
    user: str = "autops"
    password: str = ""
    database: str = "autops"
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False

    @property
    def url(self) -> str:
        return (
            f"mysql+aiomysql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}?charset=utf8mb4"
        )

    class Config:
        env_prefix = "DB_"


class RedisConfig(BaseSettings):
    """Redis 配置."""

    host: str = "127.0.0.1"
    port: int = 6379
    password: str = ""
    db: int = 0

    @property
    def url(self) -> str:
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"

    class Config:
        env_prefix = "REDIS_"


class LLMConfig(BaseSettings):
    """LLM 配置."""

    base_url: str = "http://127.0.0.1:8000/v1"
    model_name: str = "qwen3.5-0.8b"
    api_key: str = "EMPTY"
    timeout: int = 60
    max_tokens: int = 2048

    class Config:
        env_prefix = "LLM_"


class SecurityConfig(BaseSettings):
    """安全配置."""

    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    master_key_vault_path: str = "/opt/autops/secrets/master.key"

    class Config:
        env_prefix = "SECURITY_"


class AppConfig(BaseSettings):
    """应用总配置."""

    app_name: str = "AUTOPS"
    version: str = "0.1.0"
    debug: bool = False
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    class Config:
        env_prefix = "AUTOPS_"


@lru_cache
def get_config() -> AppConfig:
    """获取全局配置（单例）."""
    return AppConfig()
