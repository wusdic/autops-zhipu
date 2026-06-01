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
from typing import ClassVar, Literal

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
    """Security / JWT configuration.

    Reads from ``SECURITY_*`` env vars by default, but also accepts the
    legacy ``JWT_SECRET`` env var for the secret field.
    """

    INSECURE_SECRETS: ClassVar[set[str]] = {
        "change-me",
        "change-me-in-production",
        "autops-secret-key-change-in-production",
        "secret",
        "admin",
        "password",
    }

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    refresh_token_expire_days: int = 7

    def __init__(self, **kwargs):
        # Support JWT_SECRET env var in addition to SECURITY_JWT_SECRET
        jwt_env = os.getenv("JWT_SECRET")
        if jwt_env and "jwt_secret" not in kwargs:
            kwargs["jwt_secret"] = jwt_env
        super().__init__(**kwargs)

    @field_validator("jwt_secret")
    @classmethod
    def validate_secret(cls, v: str) -> str:
        env = os.getenv("AUTOPS_ENV", "dev")
        if env == "prod" and not v:
            raise ValueError("JWT_SECRET must be set in production")
        if v in cls.INSECURE_SECRETS and env == "prod":
            raise ValueError(
                f"insecure JWT_SECRET in production: '{v}' is not allowed"
            )
        if env == "prod" and len(v) < 32:
            raise ValueError(
                "JWT_SECRET must be at least 32 characters in production"
            )
        return v

    class Config:
        env_prefix = "SECURITY_"


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
    allow_inprocess_events: bool = False

    # 子配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # --- 从yaml文件覆盖配置 (env vars always win) ---
        yaml_sources = {
            "database": _load_yaml("database.yaml"),
            "redis": _load_yaml("redis.yaml"),
            "llm": _load_yaml("llm.yaml"),
            "security": _load_yaml("security.yaml"),
        }

        for attr_name, yaml_data in yaml_sources.items():
            if not yaml_data:
                continue
            obj = getattr(self, attr_name)
            for k, v in yaml_data.items():
                if not hasattr(obj, k):
                    continue
                # Skip if field was explicitly set from env var — env wins over yaml
                if k in obj.model_fields_set:
                    continue
                setattr(obj, k, v)

        # --- Production hardening (applied after all config sources) ---
        if self.env == "prod":
            if self.cors_origins == ["*"]:
                raise ValueError("cors_origins=['*'] is not allowed in production")
            self.enable_openapi_ui = False

    class Config:
        env_prefix = "AUTOPS_"


@lru_cache
def get_config() -> AppConfig:
    return AppConfig()
