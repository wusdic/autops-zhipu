"""AUTOPS config loader."""

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
    host: str = "127.0.0.1"
    port: int = 3306
    user: str = "autops"
    db_password: str = ""
    database: str = "autops"
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False

    @property
    def url(self) -> str:
        p = f":{self.db_password}" if self.db_password else ""
        return f"mysql+aiomysql://{self.user}{p}@{self.host}:{self.port}/{self.database}?charset=utf8mb4"

    class Config:
        env_prefix = "DB_"


class RedisConfig(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 6379
    redis_password: str = ""
    db: int = 0

    @property
    def url(self) -> str:
        a = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{a}{self.host}:{self.port}/{self.db}"

    class Config:
        env_prefix = "REDIS_"


class SecurityConfig(BaseSettings):
    secret_key: str = "autops-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    refresh_token_expire_days: int = 7

    class Config:
        env_prefix = "SECURITY_"


class LlmConfig(BaseSettings):
    base_url: str = ""
    api_key: str = ""
    model_name: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7


class AppConfig(BaseSettings):
    app_name: str = "AUTOPS"
    version: str = "0.1.0"
    debug: bool = False
    api_prefix: str = "/api/v1"
    cors_origins: list = Field(default_factory=lambda: ["*"])

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    llm: LlmConfig = Field(default_factory=LlmConfig)

    base_url: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for fname, attr in [
            ("database.yaml", "database"),
            ("redis.yaml", "redis"),
            ("security.yaml", "security"),
            ("llm.yaml", "llm"),
        ]:
            ydata = _load_yaml(fname).get(attr, {})
            if ydata:
                obj = getattr(self, attr)
                for k, v in ydata.items():
                    if hasattr(obj, k):
                        setattr(obj, k, v)
        app_yaml = _load_yaml("app.yaml").get("app", {})
        if app_yaml:
            for k, v in app_yaml.items():
                if k == "name":
                    self.app_name = v
                elif hasattr(self, k):
                    setattr(self, k, v)


@lru_cache
def get_config() -> AppConfig:
    return AppConfig()
