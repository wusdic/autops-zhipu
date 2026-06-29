"""只读工具集 — 查询类工具，无副作用."""
from __future__ import annotations
from app.domains.aiops.tools.registry import ToolRegistry

registry = ToolRegistry.get_instance()

@registry.register(
    name="check_asset_status",
    description="查询资产当前状态和健康信息",
    parameters={
        "type": "object",
        "properties": {
            "asset_id": {"type": "string", "description": "资产ID"},
        },
        "required": ["asset_id"]
    },
    risk_level="read_only"
)
async def check_asset_status(asset_id: str) -> dict:
    """查询资产状态."""
    from app.infra.database import get_db
    from sqlalchemy import text
    async for db in get_db():
        result = await db.execute(
            text("SELECT id, name, asset_type, status, health_status FROM assets WHERE id=:id"),
            {"id": asset_id}
        )
        row = result.fetchone()
        if row:
            return {"id": str(row[0]), "name": row[1], "type": row[2], "status": row[3], "health": row[4]}
        return {"error": "Asset not found"}

@registry.register(
    name="query_alerts",
    description="查询告警列表",
    parameters={
        "type": "object",
        "properties": {
            "severity": {"type": "string", "description": "严重级别: critical,warning,info"},
            "status": {"type": "string", "description": "告警状态: active,acknowledged,resolved"},
            "limit": {"type": "integer", "description": "返回数量", "default": 10}
        }
    },
    risk_level="read_only"
)
async def query_alerts(severity: str | None = None, status: str = "active", limit: int = 10) -> list:
    """查询告警."""
    from app.infra.database import get_db
    from sqlalchemy import text
    async for db in get_db():
        conditions = ["status=:status"]
        params = {"status": status, "limit": limit}
        if severity:
            conditions.append("severity=:severity")
            params["severity"] = severity
        where = " AND ".join(conditions)
        result = await db.execute(
            text(f"SELECT id, title, severity, status, created_at FROM alerts WHERE {where} ORDER BY created_at DESC LIMIT :limit"),
            params
        )
        return [{"id": str(r[0]), "title": r[1], "severity": r[2], "status": r[3], "created_at": str(r[4])} for r in result.fetchall()]

@registry.register(
    name="query_knowledge",
    description="搜索知识库文章",
    parameters={
        "type": "object",
        "properties": {
            "keyword": {"type": "string", "description": "搜索关键词"},
            "limit": {"type": "integer", "description": "返回数量", "default": 5}
        },
        "required": ["keyword"]
    },
    risk_level="read_only"
)
async def query_knowledge(keyword: str, limit: int = 5) -> list:
    """搜索知识库."""
    from app.infra.database import get_db
    from sqlalchemy import text
    async for db in get_db():
        result = await db.execute(
            text("SELECT id, title, content, risk_level FROM knowledge_articles WHERE title LIKE :kw OR content LIKE :kw LIMIT :lim"),
            {"kw": f"%{keyword}%", "lim": limit}
        )
        return [{"id": str(r[0]), "title": r[1], "content": r[2][:200] if r[2] else "", "risk_level": r[3]} for r in result.fetchall()]

@registry.register(
    name="query_execution_logs",
    description="查询执行日志",
    parameters={
        "type": "object",
        "properties": {
            "execution_id": {"type": "string", "description": "执行ID"}
        },
        "required": ["execution_id"]
    },
    risk_level="read_only"
)
async def query_execution_logs(execution_id: str) -> dict:
    """查询执行日志."""
    from app.infra.database import get_db
    from sqlalchemy import text
    async for db in get_db():
        result = await db.execute(
            text("SELECT id, status, result, error_message, started_at, completed_at FROM executions WHERE id=:id"),
            {"id": execution_id}
        )
        row = result.fetchone()
        if row:
            return {"id": str(row[0]), "status": row[1], "result": str(row[2])[:500] if row[2] else None, "error": row[3], "started": str(row[4]), "completed": str(row[5])}
        return {"error": "Execution not found"}

@registry.register(
    name="query_events",
    description="查询事件列表",
    parameters={
        "type": "object",
        "properties": {
            "asset_id": {"type": "string", "description": "资产ID"},
            "event_type": {"type": "string", "description": "事件类型"},
            "limit": {"type": "integer", "description": "返回数量", "default": 20}
        }
    },
    risk_level="read_only"
)
async def query_events(asset_id: str | None = None, event_type: str | None = None, limit: int = 20) -> list:
    """查询事件."""
    from app.infra.database import get_db
    from sqlalchemy import text
    async for db in get_db():
        conditions = []
        params = {"limit": limit}
        if asset_id:
            conditions.append("asset_id=:asset_id")
            params["asset_id"] = asset_id
        if event_type:
            conditions.append("event_type=:event_type")
            params["event_type"] = event_type
        where = " AND ".join(conditions) if conditions else "1=1"
        result = await db.execute(
            text(f"SELECT id, event_type, title, severity, created_at FROM events WHERE {where} ORDER BY created_at DESC LIMIT :limit"),
            params
        )
        return [{"id": str(r[0]), "type": r[1], "title": r[2], "severity": r[3], "time": str(r[4])} for r in result.fetchall()]


@registry.register(
    name="query_assets",
    description="统计/查询资产清单：按类型、状态、关键词过滤，返回总数与样例列表。"
                "回答'我有多少资产/有哪些Linux服务器/在线资产数量'等问题时使用。",
    parameters={
        "type": "object",
        "properties": {
            "asset_type": {"type": "string", "description": "资产类型，如 linux/windows/database/network；留空=全部"},
            "status": {"type": "string", "description": "状态，如 active/online/offline；留空=全部"},
            "keyword": {"type": "string", "description": "名称/IP 关键词"},
            "limit": {"type": "integer", "description": "样例返回数量", "default": 20},
        },
    },
    risk_level="read_only",
)
async def query_assets(
    asset_type: str | None = None, status: str | None = None,
    keyword: str | None = None, limit: int = 20,
) -> dict:
    """统计并列出资产（带过滤）."""
    from app.infra.database import get_db
    from sqlalchemy import text
    async for db in get_db():
        conditions = ["(is_deleted = 0 OR is_deleted IS NULL)"]
        params: dict = {"limit": int(limit or 20)}
        if asset_type:
            conditions.append("asset_type = :atype")
            params["atype"] = asset_type
        if status:
            conditions.append("status = :status")
            params["status"] = status
        if keyword:
            conditions.append("(name LIKE :kw OR ip_address LIKE :kw)")
            params["kw"] = f"%{keyword}%"
        where = " AND ".join(conditions)
        total = (await db.execute(
            text(f"SELECT COUNT(*) FROM assets WHERE {where}"), params
        )).scalar() or 0
        rows = (await db.execute(
            text(f"SELECT name, asset_type, status, ip_address FROM assets WHERE {where} "
                 "ORDER BY created_at DESC LIMIT :limit"),
            params,
        )).fetchall()
        return {
            "total": int(total),
            "items": [
                {"name": r[0], "type": r[1], "status": r[2], "ip": r[3]} for r in rows
            ],
        }
