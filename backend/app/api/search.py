"""全局搜索 API.

跨域联合搜索：资产、告警、异常、工单、知识库、执行。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import success
from app.common.crud_service import model_to_dict
from app.infra.database import get_db

router = APIRouter(prefix="/search", tags=["全局搜索"])


@router.get("")
async def global_search(
    q: str = Query(..., min_length=1, max_length=128, description="搜索关键词"),
    type: str | None = Query(None, description="限定类型: asset/alert/anomaly/ticket/knowledge/execution"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """全局搜索."""
    results = {}
    keyword = f"%{q}%"

    # 1. Assets
    if type is None or type == "asset":
        try:
            from app.domains.asset.models import Asset
            rows = (await db.execute(
                select(Asset).where(
                    Asset.is_deleted == False,
                    or_(
                        Asset.name.ilike(keyword),
                        Asset.ip.ilike(keyword),
                        Asset.hostname.ilike(keyword),
                        Asset.description.ilike(keyword),
                    )
                ).limit(page_size)
            )).scalars().all()
            results["assets"] = [model_to_dict(r) for r in rows]
        except Exception:
            results["assets"] = []

    # 2. Alerts
    if type is None or type == "alert":
        try:
            from app.domains.alert.models import Alert
            rows = (await db.execute(
                select(Alert).where(
                    or_(
                        Alert.title.ilike(keyword),
                        Alert.context.ilike(keyword),
                    )
                ).limit(page_size)
            )).scalars().all()
            results["alerts"] = [model_to_dict(r) for r in rows]
        except Exception:
            results["alerts"] = []

    # 3. Anomalies
    if type is None or type == "anomaly":
        try:
            from app.domains.anomaly.models import Anomaly
            rows = (await db.execute(
                select(Anomaly).where(
                    or_(
                        Anomaly.title.ilike(keyword),
                        Anomaly.description.ilike(keyword),
                    )
                ).limit(page_size)
            )).scalars().all()
            results["anomalies"] = [model_to_dict(r) for r in rows]
        except Exception:
            results["anomalies"] = []

    # 4. Tickets
    if type is None or type == "ticket":
        try:
            from app.domains.ticket.models import Ticket
            rows = (await db.execute(
                select(Ticket).where(
                    or_(
                        Ticket.title.ilike(keyword),
                        Ticket.description.ilike(keyword),
                    )
                ).limit(page_size)
            )).scalars().all()
            results["tickets"] = [model_to_dict(r) for r in rows]
        except Exception:
            results["tickets"] = []

    # 5. Knowledge
    if type is None or type == "knowledge":
        try:
            from app.domains.knowledge.models import KnowledgeArticle
            rows = (await db.execute(
                select(KnowledgeArticle).where(
                    or_(
                        KnowledgeArticle.title.ilike(keyword),
                        KnowledgeArticle.content.ilike(keyword),
                    )
                ).limit(page_size)
            )).scalars().all()
            results["knowledge"] = [model_to_dict(r) for r in rows]
        except Exception:
            results["knowledge"] = []

    # 6. Executions
    if type is None or type == "execution":
        try:
            from app.domains.automation.models import Execution
            rows = (await db.execute(
                select(Execution).where(
                    Execution.name.ilike(keyword)
                ).limit(page_size)
            )).scalars().all()
            results["executions"] = [model_to_dict(r) for r in rows]
        except Exception:
            results["executions"] = []

    total = sum(len(v) for v in results.values())
    return success({"query": q, "total": total, "results": results})
