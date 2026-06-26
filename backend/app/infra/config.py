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
from pydantic import AliasChoices, Field, field_validator
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
    # env_prefix="DB_" + 字段名 db_pass 会映射成 DB_DB_PASS，与 .env / compose 使用的
    # DB_PASS 不一致。显式 alias 兼容 DB_PASS（推荐）与 DB_DB_PASS（历史）两种写法。
    db_pass: str = Field(
        default="",
        validation_alias=AliasChoices("DB_PASS", "DB_DB_PASS"),
    )
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
    # 同 db_pass：REDIS_ + redis_pass = REDIS_REDIS_PASS，与 .env 的 REDIS_PASS 不一致。
    redis_pass: str = Field(
        default="",
        validation_alias=AliasChoices("REDIS_PASS", "REDIS_REDIS_PASS"),
    )
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
    # 兼容 .env 中的 JWT_ALGORITHM（否则 env_prefix 会要求 SECURITY_JWT_ALGORITHM）。
    jwt_algorithm: str = Field(
        default="HS256",
        validation_alias=AliasChoices("JWT_ALGORITHM", "SECURITY_JWT_ALGORITHM"),
    )
    access_token_expire_minutes: int = 1440
    refresh_token_expire_days: int = 7
    # 凭证加密主密钥（独立于 JWT 密钥）。优先读 CREDENTIAL_ENCRYPT_KEY，
    # 回退到 SECURITY_CREDENTIAL_ENCRYPT_KEY，再回退到 jwt_secret（兼容旧配置）。
    credential_encrypt_key: str = ""

    def __init__(self, **kwargs):
        # Support JWT_SECRET env var in addition to SECURITY_JWT_SECRET
        jwt_env = os.getenv("JWT_SECRET")
        if jwt_env and "jwt_secret" not in kwargs:
            kwargs["jwt_secret"] = jwt_env
        # 凭证加密密钥独立注入：CREDENTIAL_ENCRYPT_KEY 优先
        cred_env = os.getenv("CREDENTIAL_ENCRYPT_KEY")
        if cred_env and "credential_encrypt_key" not in kwargs:
            kwargs["credential_encrypt_key"] = cred_env
        super().__init__(**kwargs)

    @field_validator("jwt_secret")
    @classmethod
    def validate_secret(cls, v: str) -> str:
        env = os.getenv("AUTOPS_ENV", "dev")
        if env == "prod" and not v:
            raise ValueError("JWT_SECRET must be set in production")
        if v in cls.INSECURE_SECRETS and env == "prod":
            raise ValueError(f"insecure JWT_SECRET in production: '{v}' is not allowed")
        if env == "prod" and len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters in production")
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

    # API进程是否允许注册业务handler（生产必须false）
    allow_inprocess_events: bool = False
    # API进程是否启动scheduler（生产必须false，由worker负责）
    enable_scheduler: bool = False
    # 进程角色: api / worker（用于决定上述开关的合法性）
    process_role: Literal["api", "worker"] = "api"
    # 自动化执行器: auto(生产→ssh, 其余→local_dev) / local_dev / ssh
    executor: Literal["auto", "local_dev", "ssh"] = "auto"

    # 子配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # --- 从yaml文件覆盖配置 (env vars always win) ---
        yaml_sources = {
            "database": (_load_yaml("database.yaml"), "DB_"),
            "redis": (_load_yaml("redis.yaml"), "REDIS_"),
            "llm": (_load_yaml("llm.yaml"), "LLM_"),
            "security": (_load_yaml("security.yaml"), "SECURITY_"),
        }

        for attr_name, (yaml_data, env_prefix) in yaml_sources.items():
            if not yaml_data:
                continue
            obj = getattr(self, attr_name)
            for k, v in yaml_data.items():
                if not hasattr(obj, k):
                    continue
                # Env vars always win over yaml — check os.environ directly.
                # pydantic-settings model_fields_set is unreliable for this purpose
                # when no env_file is configured (the default).
                env_key = (env_prefix + k).upper()
                # Handle pydantic field name → env var name mapping (e.g. db_pass → DB_PASS)
                if env_key in os.environ:
                    continue
                setattr(obj, k, v)

        # --- Production hardening (applied after all config sources) ---
        if self.env == "prod":
            if self.cors_origins == ["*"]:
                raise ValueError("cors_origins=['*'] is not allowed in production")
            self.enable_openapi_ui = False
            # 只对 API 进程检查：不允许注册业务 handler 和 scheduler
            if self.process_role == "api":
                if self.allow_inprocess_events:
                    raise ValueError(
                        "allow_inprocess_events is not allowed in API process (production)"
                    )
                if self.enable_scheduler:
                    raise ValueError(
                        "enable_scheduler is not allowed in API process (production); use worker"
                    )

    class Config:
        env_prefix = "AUTOPS_"


@lru_cache
def get_config() -> AppConfig:
    return AppConfig()
