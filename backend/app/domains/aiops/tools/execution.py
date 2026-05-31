"""执行工具集 — 有副作用，需要安全边界评估."""
from __future__ import annotations
from app.domains.aiops.tools.registry import ToolRegistry

registry = ToolRegistry.get_instance()

@registry.register(
    name="execute_script",
    description="执行指定脚本",
    parameters={
        "type": "object",
        "properties": {
            "script_id": {"type": "string", "description": "脚本ID"},
            "asset_id": {"type": "string", "description": "目标资产ID"},
            "parameters": {"type": "object", "description": "脚本参数"}
        },
        "required": ["script_id", "asset_id"]
    },
    risk_level="medium"
)
async def execute_script(script_id: str, asset_id: str, parameters: dict | None = None) -> dict:
    """执行脚本（通过自动化执行中心）."""
    # 实际执行由自动化中心完成，此处创建执行记录
    from app.infra.database import get_db
    from sqlalchemy import text
    from uuid import uuid4
    from datetime import datetime
    async for db in get_db():
        exec_id = str(uuid4())
        await db.execute(
            text("INSERT INTO executions (id, execution_type, target_id, asset_ids, status, is_dry_run, created_at) VALUES (:id, 'script', :target, :assets, 'pending', FALSE, :ts)"),
            {"id": exec_id, "target": script_id, "assets": f'["{asset_id}"]', "ts": datetime.utcnow()}
        )
        await db.commit()
        return {"execution_id": exec_id, "status": "pending", "message": "执行已创建，等待处理"}

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
            "source_id": {"type": "string", "description": "来源ID"}
        },
        "required": ["title", "description"]
    },
    risk_level="low"
)
async def create_ticket(title: str, description: str, severity: str = "medium", source_type: str = "ai_agent", source_id: str | None = None) -> dict:
    """创建工单."""
    from app.infra.database import get_db
    from sqlalchemy import text
    from uuid import uuid4
    from datetime import datetime
    async for db in get_db():
        tid = str(uuid4())
        await db.execute(
            text("INSERT INTO tickets (id, title, description, severity, status, source_type, source_id, created_at) VALUES (:id, :title, :desc, :sev, 'open', :st, :si, :ts)"),
            {"id": tid, "title": title, "desc": description, "sev": severity, "st": source_type, "si": source_id, "ts": datetime.utcnow()}
        )
        await db.commit()
        return {"ticket_id": tid, "status": "open"}
