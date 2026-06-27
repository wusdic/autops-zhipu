"""AI Agent 上下文构建器."""
from __future__ import annotations
import json
import logging

logger = logging.getLogger(__name__)

class ContextBuilder:
    """为 AI Agent 构建完整上下文."""

    def __init__(self, db_session=None):
        self.db = db_session

    async def build_alert_context(self, alert_id: str) -> dict:
        """构建告警上下文."""
        from sqlalchemy import text
        context = {"alert_id": alert_id}

        # 告警详情
        result = await self.db.execute(text("SELECT * FROM alerts WHERE id=:id"), {"id": alert_id})
        alert = result.mappings().first()
        if alert:
            context["alert"] = dict(alert)

        # 关联资产
        if alert and alert.get("asset_ids"):
            asset_ids = json.loads(alert["asset_ids"]) if isinstance(alert["asset_ids"], str) else alert["asset_ids"]
            if asset_ids:
                result = await self.db.execute(
                    text("SELECT id, name, asset_type, status, health_status FROM assets WHERE id IN :ids"),
                    {"ids": tuple(asset_ids)}
                )
                context["assets"] = [dict(r) for r in result.mappings().all()]

        # 最近事件
        result = await self.db.execute(
            text("SELECT event_type, title, severity, created_at FROM events ORDER BY created_at DESC LIMIT 10")
        )
        context["recent_events"] = [dict(r) for r in result.mappings().all()]

        # 知识库匹配
        if alert:
            title = alert.get("title", "")
            result = await self.db.execute(
                text("SELECT id, title, diagnosis_steps, action_steps FROM knowledge_articles WHERE title LIKE :kw LIMIT 3"),
                {"kw": f"%{title[:10]}%"}
            )
            context["knowledge"] = [dict(r) for r in result.mappings().all()]

        return context
