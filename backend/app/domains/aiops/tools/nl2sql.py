"""智能问数（NL2SQL）只读工具集.

让 AI 助手能基于真实数据库结构回答任意数据问题：
- get_database_schema：返回可查询的表与字段（自动排除敏感/鉴权表），供模型据此写 SQL
- run_sql_query：执行**只读、单条 SELECT**，多重安全闸门后返回结果

安全模型（纵深防御，缺一不可）：
1. 仅允许 SELECT/WITH，单条语句（禁分号串联）
2. 关键字黑名单（insert/update/delete/drop/alter/... / outfile / load_file 等）
3. 表白名单 = 库内全部表 − 敏感表黑名单（鉴权/密钥/凭证/密文配置）
4. 敏感字段名黑名单（password/api_key/secret/token/credential/...）
5. 强制 LIMIT 上限，结果行数硬截断
"""

from __future__ import annotations

import logging
import re

import sqlalchemy as sa
from sqlalchemy import text

from app.domains.aiops.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)
registry = ToolRegistry.get_instance()

# 永不暴露给问数的敏感表（鉴权/密钥/凭证/可能含密文的配置）
_DENY_TABLES = {
    "users", "roles", "user_roles", "permissions", "role_permissions",
    "api_keys", "credentials", "credential_bindings", "model_agents",
    "system_settings", "sessions", "refresh_tokens", "alembic_version",
    "config_versions", "config_bindings",
}
# 表名包含这些片段也一律排除
_DENY_TABLE_PAT = re.compile(r"(password|secret|token|credential|api_?key|oauth)", re.I)

# 查询语句中出现这些字段名即拒绝（防止 select 出密文/口令）
_DENY_COLUMN_PAT = re.compile(
    r"\b(password|passwd|pwd|api_key|api_key_enc|secret|token|salt|private_key|credential|access_key|svalue)\b",
    re.I,
)
# 非只读/危险关键字
_DENY_SQL_PAT = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|replace|merge|"
    r"call|exec|execute|attach|detach|pragma|vacuum|dumpfile|outfile|load_file|"
    r"into\s+outfile|into\s+dumpfile)\b",
    re.I,
)
_TABLE_REF_PAT = re.compile(r"(?:from|join)\s+`?([a-zA-Z_][a-zA-Z0-9_]*)`?", re.I)

_MAX_ROWS = 200

# 关键业务表中文释义（帮助模型写对 SQL；未列出的表仍可查，只是没有释义）
_TABLE_DESC = {
    "assets": "资产（is_deleted=0 有效；asset_type 类型，含 business_system 为业务系统；"
              "reachability=reachable/unreachable 可达性；health_status 健康；status 状态）",
    "alerts": "告警（status=open/acknowledged/resolved；severity 级别）",
    "anomalies": "异常（status=new/confirmed/analyzing/closed；severity）",
    "events": "事件（event_type 类型；severity）",
    "tickets": "工单（status=open/in_progress/resolved/closed；priority）",
    "executions": "自动化执行（status=running/completed/failed/awaiting_approval）",
    "policies": "自动化策略", "playbooks": "Playbook 剧本", "scripts": "脚本库",
    "inspection_tasks": "巡检任务（status=completed/failed/...）",
    "inspection_results": "巡检结果（status 项级结果）",
    "collectors": "采集器", "collection_jobs": "采集任务",
    "discovery_tasks": "资产发现任务", "discovery_results": "资产发现结果",
    "knowledge_articles": "知识库文章（status=published/draft）",
    "report_tasks": "报告任务", "asset_groups": "资产分组",
    "asset_relations": "资产关系（拓扑）", "state_changes": "状态变更记录",
}


async def _allowed_tables_and_columns() -> dict[str, list[str]]:
    """反射库结构，返回 {表: [字段...]}，已排除敏感表."""
    from app.infra.database import get_db

    def _grab(sync_session) -> dict[str, list[str]]:
        insp = sa.inspect(sync_session.connection())
        out: dict[str, list[str]] = {}
        for t in insp.get_table_names():
            if t in _DENY_TABLES or _DENY_TABLE_PAT.search(t):
                continue
            out[t] = [c["name"] for c in insp.get_columns(t)]
        return out

    async for db in get_db():
        return await db.run_sync(_grab)
    return {}


@registry.register(
    name="get_database_schema",
    description="获取可查询的数据库结构（表名+字段名+中文释义，已自动排除鉴权/密钥等敏感表）。"
                "在用其它结构化工具无法回答、需要自由查询数据时，先调用本工具了解表结构，再用 run_sql_query。",
    parameters={
        "type": "object",
        "properties": {
            "table": {"type": "string", "description": "只看某张表的字段；留空=列出全部可查表"},
        },
    },
    risk_level="read_only",
)
async def get_database_schema(table: str | None = None) -> dict:
    """返回库结构（白名单内）."""
    schema = await _allowed_tables_and_columns()
    if table:
        t = table.strip()
        if t not in schema:
            return {"error": f"表不存在或不可查询: {table}", "available_tables": sorted(schema)}
        return {"table": t, "desc": _TABLE_DESC.get(t, ""), "columns": schema[t]}
    return {
        "tables": [
            {"table": t, "desc": _TABLE_DESC.get(t, ""), "columns": cols}
            for t, cols in sorted(schema.items())
        ],
        "note": "仅可执行只读 SELECT；查询请加 WHERE/LIMIT。",
    }


def _validate_sql(sql: str, allowed: set[str]) -> tuple[bool, str, str]:
    """校验并规整 SQL；返回 (是否通过, 原因, 规整后SQL)."""
    s = (sql or "").strip().rstrip(";").strip()
    if not s:
        return False, "空查询", ""
    if ";" in s:
        return False, "仅允许单条查询（禁止分号串联）", ""
    low = s.lower()
    if not (low.startswith("select") or low.startswith("with")):
        return False, "仅允许 SELECT/WITH 只读查询", ""
    if _DENY_SQL_PAT.search(low):
        return False, "检测到非只读/危险关键字，已拒绝", ""
    if _DENY_COLUMN_PAT.search(low):
        return False, "查询涉及敏感字段（口令/密钥/凭证等），已拒绝", ""
    refs = {t.lower() for t in _TABLE_REF_PAT.findall(low)}
    bad = sorted(t for t in refs if t not in allowed)
    if bad:
        return False, f"不允许访问的表（可能是敏感表或不存在）: {bad}", ""
    # 强制 LIMIT 上限
    m = re.search(r"\blimit\s+(\d+)", low)
    if not m:
        s = f"{s} LIMIT {_MAX_ROWS}"
    elif int(m.group(1)) > _MAX_ROWS:
        s = re.sub(r"(?i)\blimit\s+\d+", f"LIMIT {_MAX_ROWS}", s)
    return True, "", s


@registry.register(
    name="run_sql_query",
    description="对平台数据库执行一条只读 SELECT 查询并返回结果（智能问数）。"
                "用于回答结构化工具覆盖不到的数据问题。SQL 由你根据 get_database_schema 的表结构生成；"
                "只能 SELECT、单条语句、会自动限制返回行数；涉及敏感表/字段会被拒绝。",
    parameters={
        "type": "object",
        "properties": {
            "sql": {"type": "string", "description": "单条只读 SELECT 语句（标准 SQL）"},
        },
        "required": ["sql"],
    },
    risk_level="read_only",
)
async def run_sql_query(sql: str) -> dict:
    """执行受限只读 SELECT."""
    from app.infra.database import get_db

    schema = await _allowed_tables_and_columns()
    allowed = set(schema.keys())
    ok, reason, safe_sql = _validate_sql(sql, allowed)
    if not ok:
        return {"error": reason}

    async for db in get_db():
        try:
            result = await db.execute(text(safe_sql))
        except Exception as e:  # noqa: BLE001
            return {"error": f"查询失败: {e}", "sql": safe_sql}
        cols = list(result.keys())
        raw = result.fetchmany(_MAX_ROWS)
        rows = [
            {c: (str(v) if v is not None else None) for c, v in zip(cols, r)}
            for r in raw
        ]
        return {"columns": cols, "row_count": len(rows), "rows": rows, "sql": safe_sql}
    return {"error": "无数据库连接"}
