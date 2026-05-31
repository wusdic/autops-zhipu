"""国产化数据库方言适配模拟测试."""
from __future__ import annotations

import pytest

from app.infra.db_dialect import DialectAdapter, DialectConfig, SUPPORTED_DIALECTS


# ---------------------------------------------------------------------------
# Helper — 模拟 DatabaseConfig 构建 URL 的逻辑 (不连接真实数据库)
# ---------------------------------------------------------------------------
def _build_url(adapter: DialectAdapter, user: str = "autops", password: str = "autops_2026",
               host: str = "127.0.0.1", port: int | None = None, database: str = "autops") -> str:
    """模拟 DatabaseConfig.url 属性的逻辑."""
    effective_port = port if port is not None else adapter.config.default_port
    base_url = adapter.build_connection_url(user, password, host, effective_port, database)
    if adapter.is_mysql_compatible:
        return f"{base_url}?charset=utf8mb4"
    return base_url


# ========================== 测试用例 ========================================


class TestDialectAdapter:
    """国产化数据库方言适配器测试."""

    # 1. 默认 MySQL — 连接URL不变
    def test_mysql_dialect(self):
        adapter = DialectAdapter("mysql")
        url = _build_url(adapter)

        assert adapter.config.name == "mysql"
        assert adapter.config.connector == "mysql+aiomysql"
        assert adapter.config.default_port == 3306
        assert url.startswith("mysql+aiomysql://")
        assert ":3306/" in url
        assert "charset=utf8mb4" in url

    # 2. 达梦 (DM) — URL 从 mysql:// 变为 dm://, 端口 5236
    def test_dm_dialect(self):
        adapter = DialectAdapter("dm")
        url = _build_url(adapter)

        assert adapter.config.name == "dm"
        assert adapter.config.connector == "dm+dmPython"
        assert adapter.config.default_port == 5236
        assert url.startswith("dm+dmPython://")
        assert ":5236/" in url
        # DM 不兼容 MySQL, 无 charset 参数
        assert "charset" not in url

    # 3. OpenGauss — postgresql+asyncpg://, 端口 5432
    def test_opengauss_dialect(self):
        adapter = DialectAdapter("opengauss")
        url = _build_url(adapter)

        assert adapter.config.name == "opengauss"
        assert adapter.config.connector == "postgresql+asyncpg"
        assert adapter.config.default_port == 5432
        assert url.startswith("postgresql+asyncpg://")
        assert ":5432/" in url
        # OpenGauss 不兼容 MySQL, 无 charset
        assert "charset" not in url

    # 4. TiDB — MySQL 兼容, 保持 mysql+aiomysql://, 添加 charset
    def test_tidb_dialect(self):
        adapter = DialectAdapter("tidb")
        url = _build_url(adapter)

        assert adapter.config.name == "tidb"
        assert adapter.config.connector == "mysql+aiomysql"
        assert adapter.is_mysql_compatible is True
        assert url.startswith("mysql+aiomysql://")
        assert "charset=utf8mb4" in url
        # TiDB 默认端口 4000
        assert ":4000/" in url

    # 5. OceanBase — MySQL 兼容, 保持 mysql+aiomysql://, 添加 charset
    def test_oceanbase_dialect(self):
        adapter = DialectAdapter("oceanbase")
        url = _build_url(adapter)

        assert adapter.config.name == "oceanbase"
        assert adapter.config.connector == "mysql+aiomysql"
        assert adapter.is_mysql_compatible is True
        assert url.startswith("mysql+aiomysql://")
        assert "charset=utf8mb4" in url
        # OceanBase 默认端口 2881
        assert ":2881/" in url

    # 6. 未知 dialect 回退到 MySQL
    def test_unknown_dialect_fallback(self):
        adapter = DialectAdapter("some_unknown_db")

        # 应回退到 MySQL 配置 (config), 但 dialect_name 仍为传入值
        assert adapter.config.name == "mysql"
        assert adapter.config.connector == "mysql+aiomysql"
        assert adapter.config.default_port == 3306
        # is_mysql_compatible 基于 dialect_name 判断, 非 mysql/tidb/oceanbase → False
        assert adapter.is_mysql_compatible is False

        # _build_url 使用 adapter.is_mysql_compatible, 因此未知 dialect 无 charset 参数
        url = _build_url(adapter)
        assert url.startswith("mysql+aiomysql://")
        assert ":3306/" in url
        assert "charset" not in url

    # 7. 各 dialect 的 SQL 类型映射差异
    def test_dialect_type_mapping(self):
        # MySQL: LIMIT/OFFSET, JSON, AUTO_INCREMENT
        mysql = DialectAdapter("mysql")
        assert "LIMIT" in mysql.paginate("SELECT * FROM t", 0, 10)
        assert mysql.json_column_type() == "JSON"
        assert "AUTO_INCREMENT" in mysql.auto_increment_id()

        # DM (达梦): ROWNUM 分页, TEXT 代替 JSON, AUTO_INCREMENT (uses default True)
        dm = DialectAdapter("dm")
        paginated = dm.paginate("SELECT * FROM t", 0, 10)
        assert "ROWNUM" in paginated
        assert "LIMIT" not in paginated
        assert dm.json_column_type() == "TEXT"  # DM 不支持 JSON 类型
        assert "AUTO_INCREMENT" in dm.auto_increment_id()  # DM uses default

        # OpenGauss: LIMIT/OFFSET, JSON, SERIAL
        og = DialectAdapter("opengauss")
        assert "LIMIT" in og.paginate("SELECT * FROM t", 0, 10)
        assert og.json_column_type() == "JSON"
        assert og.auto_increment_id() == "SERIAL"
        assert "AUTO_INCREMENT" not in og.auto_increment_id()

        # TiDB: 完全 MySQL 兼容
        tidb = DialectAdapter("tidb")
        assert "LIMIT" in tidb.paginate("SELECT * FROM t", 0, 10)
        assert tidb.json_column_type() == "JSON"
        assert "AUTO_INCREMENT" in tidb.auto_increment_id()

        # OceanBase: 完全 MySQL 兼容
        ob = DialectAdapter("oceanbase")
        assert "LIMIT" in ob.paginate("SELECT * FROM t", 0, 10)
        assert ob.json_column_type() == "JSON"
        assert "AUTO_INCREMENT" in ob.auto_increment_id()

    # --- 额外边界测试 ---

    def test_build_connection_url_format(self):
        """验证 build_connection_url 输出格式."""
        adapter = DialectAdapter("mysql")
        url = adapter.build_connection_url("root", "pass123", "10.0.0.1", 3307, "testdb")
        assert url == "mysql+aiomysql://root:pass123@10.0.0.1:3307/testdb"

    def test_dm_build_connection_url(self):
        """验证达梦 URL 格式."""
        adapter = DialectAdapter("dm")
        url = adapter.build_connection_url("sysdba", "pwd", "192.168.1.100", 5236, "dmdb")
        assert url == "dm+dmPython://sysdba:pwd@192.168.1.100:5236/dmdb"

    def test_opengauss_build_connection_url(self):
        """验证 OpenGauss URL 格式."""
        adapter = DialectAdapter("opengauss")
        url = adapter.build_connection_url("gaussdb", "secret", "10.0.0.5", 5432, "postgres")
        assert url == "postgresql+asyncpg://gaussdb:secret@10.0.0.5:5432/postgres"

    def test_get_diagnostics(self):
        """验证 get_diagnostics 返回完整信息."""
        adapter = DialectAdapter("dm")
        diag = adapter.get_diagnostics()

        assert diag["dialect"] == "dm"
        assert diag["driver"] == "dmPython"
        assert diag["connector"] == "dm+dmPython"
        assert diag["mysql_compatible"] is False
        assert diag["supports_limit_offset"] is False
        assert diag["supports_json"] is False
        assert diag["default_port"] == 5236

    def test_all_supported_dialects_present(self):
        """验证所有声明的方言都可用."""
        expected = {"mysql", "dm", "opengauss", "tidb", "oceanbase"}
        assert set(SUPPORTED_DIALECTS.keys()) == expected

    def test_case_insensitive_dialect_name(self):
        """验证方言名大小写不敏感."""
        upper = DialectAdapter("MySQL")
        assert upper.config.name == "mysql"

        mixed = DialectAdapter("OpenGauss")
        assert mixed.config.name == "opengauss"

    def test_dm_rown_pagination_bounds(self):
        """验证达梦 ROWNUM 分页边界."""
        dm = DialectAdapter("dm")
        # offset=0, limit=10 → ROWNUM <= 10, rn > 0
        sql = dm.paginate("SELECT * FROM t", offset=0, limit=10)
        assert "ROWNUM <= 10" in sql
        assert "rn > 0" in sql

        # offset=20, limit=5 → ROWNUM <= 25, rn > 20
        sql2 = dm.paginate("SELECT * FROM t", offset=20, limit=5)
        assert "ROWNUM <= 25" in sql2
        assert "rn > 20" in sql2
