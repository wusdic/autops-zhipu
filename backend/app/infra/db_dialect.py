"""数据库方言适配层 — 支持MySQL/达梦/OpenGauss/TiDB/OceanBase."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DialectConfig:
    """方言配置."""

    name: str  # mysql, dm, opengauss, tidb, oceanbase
    driver: str  # aiomysql, dmPython, asyncpg
    connector: str  # mysql+aiomysql, dm+dmPython, postgresql+asyncpg
    supports_limit_offset: bool = True
    supports_auto_increment: bool = True
    supports_json: bool = True
    default_port: int = 3306


SUPPORTED_DIALECTS: dict[str, DialectConfig] = {
    "mysql": DialectConfig(
        name="mysql",
        driver="aiomysql",
        connector="mysql+aiomysql",
        supports_limit_offset=True,
        default_port=3306,
    ),
    "dm": DialectConfig(
        name="dm",
        driver="dmPython",
        connector="dm+dmPython",
        supports_limit_offset=False,
        supports_json=False,
        default_port=5236,
    ),
    "opengauss": DialectConfig(
        name="opengauss",
        driver="asyncpg",
        connector="postgresql+asyncpg",
        supports_limit_offset=True,
        supports_auto_increment=False,
        default_port=5432,
    ),
    "tidb": DialectConfig(
        name="tidb",
        driver="aiomysql",
        connector="mysql+aiomysql",
        supports_limit_offset=True,
        default_port=4000,
    ),
    "oceanbase": DialectConfig(
        name="oceanbase",
        driver="aiomysql",
        connector="mysql+aiomysql",
        supports_limit_offset=True,
        default_port=2881,
    ),
}


class DialectAdapter:
    """数据库方言适配器."""

    def __init__(self, dialect_name: str = "mysql"):
        self.dialect_name = dialect_name.lower()
        if self.dialect_name not in SUPPORTED_DIALECTS:
            # 未知方言快速失败，避免拼写错误（如 "opengaus"）被静默当作 MySQL
            raise ValueError(
                f"不支持的数据库方言: {dialect_name!r}，"
                f"支持的有: {sorted(SUPPORTED_DIALECTS)}"
            )
        self.config = SUPPORTED_DIALECTS[self.dialect_name]

    @property
    def is_mysql_compatible(self) -> bool:
        return self.dialect_name in ("mysql", "tidb", "oceanbase")

    def build_connection_url(
        self, user: str, password: str, host: str, port: int, database: str
    ) -> str:
        """构建SQLAlchemy连接URL."""
        connector = self.config.connector
        return f"{connector}://{user}:{password}@{host}:{port}/{database}"

    def paginate(self, query: str, offset: int = 0, limit: int = 20) -> str:
        """方言分页包装.

        强制 offset/limit 为非负整数，防止调用方误传字符串导致 SQL 注入。
        注意：核心查询已统一使用 ORM 的 .offset().limit()，此方法仅用于个别裸 SQL 场景。
        """
        offset = int(offset)
        limit = int(limit)
        if offset < 0 or limit < 0:
            raise ValueError(f"offset/limit 不能为负: offset={offset}, limit={limit}")
        if self.config.supports_limit_offset:
            return f"{query} LIMIT {limit} OFFSET {offset}"
        # DM uses ROWNUM
        return f"SELECT * FROM (SELECT a.*, ROWNUM rn FROM ({query}) a WHERE ROWNUM <= {offset + limit}) WHERE rn > {offset}"

    def json_column_type(self) -> str:
        """JSON列类型."""
        if self.config.supports_json:
            return "JSON"
        return "TEXT"

    def auto_increment_id(self) -> str:
        """自增ID语法."""
        if self.config.supports_auto_increment:
            return "INT AUTO_INCREMENT"
        if self.dialect_name == "opengauss":
            return "SERIAL"
        return "INT GENERATED ALWAYS AS IDENTITY"

    def get_diagnostics(self) -> dict[str, Any]:
        """获取方言诊断信息."""
        return {
            "dialect": self.config.name,
            "driver": self.config.driver,
            "connector": self.config.connector,
            "mysql_compatible": self.is_mysql_compatible,
            "supports_limit_offset": self.config.supports_limit_offset,
            "supports_json": self.config.supports_json,
            "default_port": self.config.default_port,
        }
