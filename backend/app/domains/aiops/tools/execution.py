"""执行工具集 — 有副作用，需要安全边界评估."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from app.domains.aiops.tools.registry import ToolRegistry

registry = ToolRegistry.get_instance()


def _validate_id(value: str, name: str) -> str:
    """校验 ID 参数：必须是非空字符串，且为合法 UUID 或安全字符（防 JSON/SQL 注入）."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} 不能为空")
    # 允许 UUID 或字母数字+短横线，拒绝含引号/方括号/分号等可破坏 JSON/SQL 的字符
    import re

    if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError(f"{name} 含非法字符")
    return value


@registry.register(
    name="execute_script",
    description="执行指定脚本",
    parameters={
        "type": "object",
        "properties": {
            "script_id": {"type": "string", "description": "脚本ID"},
            "asset_id": {"type": "string", "description": "目标资产ID"},
            "parameters": {"type": "object", "description": "脚本参数"},
        },
        "required": ["script_id", "asset_id"],
    },
    risk_level="medium",
)
async def execute_script(
    script_id: str, asset_id: str, parameters: dict | None = None
) -> dict:
    """执行脚本（通过自动化执行中心）."""
    # 参数校验，防止 LLM 提供的值破坏 JSON 或注入
    script_id = _validate_id(script_id, "script_id")
    asset_id = _validate_id(asset_id, "asset_id")
    # 实际执行由自动化中心完成，此处创建执行记录
    from sqlalchemy import text

    from app.infra.database import get_db

    async for db in get_db():
        exec_id = str(uuid4())
        # 用 json.dumps 构造 asset_ids，而非 f-string 拼接（防 JSON 注入）
        asset_ids_json = json.dumps([asset_id])
        await db.execute(
            text(
                "INSERT INTO executions (id, execution_type, target_id, asset_ids, status, is_dry_run, created_at) VALUES (:id, 'script', :target, :assets, 'pending', FALSE, :ts)"
            ),
            {
                "id": exec_id,
                "target": script_id,
                "assets": asset_ids_json,
                "ts": datetime.now(timezone.utc),
            },
        )
        await db.commit()
        return {
            "execution_id": exec_id,
            "status": "pending",
            "message": "执行已创建，等待处理",
        }


@registry.register(
    name="create_ticket",
    description="创建工单",
    parameters={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "工单标题"},
            "description": {"type": "string", "description": "工单描述"},
            "severity": {"type": "string", "description": "严重级别"},
            "source_type": {"type": "string", "description": "来源类型"},
            "source_id": {"type": "string", "description": "来源ID"},
        },
        "required": ["title", "description"],
    },
    risk_level="low",
)
async def create_ticket(
    title: str,
    description: str,
    severity: str = "medium",
    source_type: str = "ai_agent",
    source_id: str | None = None,
) -> dict:
    """创建工单."""
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title 不能为空")
    from sqlalchemy import text

    from app.infra.database import get_db

    async for db in get_db():
        tid = str(uuid4())
        await db.execute(
            text(
                "INSERT INTO tickets (id, title, description, severity, status, source_type, source_id, created_at) VALUES (:id, :title, :desc, :sev, 'open', :st, :si, :ts)"
            ),
            {
                "id": tid,
                "title": title,
                "desc": description,
                "sev": severity,
                "st": source_type,
                "si": source_id,
                "ts": datetime.now(timezone.utc),
            },
        )
        await db.commit()
        return {"ticket_id": tid, "status": "open"}
