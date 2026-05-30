"""AIops 中心 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.response import paginate, success
from app.infra.database import get_db
from app.domains.aiops.schemas import AIAnalysisRequest, AIFeedback
from app.domains.aiops.service import AIOpsService

router = APIRouter(prefix="/aiops", tags=["AIops"])


def _get_svc(db: AsyncSession = Depends(get_db)) -> AIOpsService:
    return AIOpsService(db)


@router.get("/analyses")
async def list_analyses(
    analysis_type: str | None = None, status: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    svc: AIOpsService = Depends(_get_svc),
):
    items, total = await svc.list_analyses(analysis_type, status, page, page_size)
    return paginate([model_to_dict(i) for i in items], total, page, page_size)


@router.post("/analyses")
async def request_analysis(data: AIAnalysisRequest, svc: AIOpsService = Depends(_get_svc)):
    a = await svc.request_analysis(data)
    return success(model_to_dict(a))


@router.get("/analyses/{analysis_id}")
async def get_analysis(analysis_id: str, svc: AIOpsService = Depends(_get_svc)):
    a = await svc.get_analysis(analysis_id)
    return success(model_to_dict(a))


@router.get("/health")
async def check_llm_health():
    """检查 LLM 服务是否可用."""
    result = await AIOpsService.check_llm_health()
    return success(result)


@router.post("/diagnose")
async def diagnose(data: dict, svc: AIOpsService = Depends(_get_svc)):
    """前端快捷诊断接口."""
    result = await svc.diagnose(data)
    return success(result)


@router.post("/analyses/{analysis_id}/feedback")
async def submit_feedback(analysis_id: str, data: AIFeedback, svc: AIOpsService = Depends(_get_svc)):
    a = await svc.submit_feedback(analysis_id, data)
    return success(model_to_dict(a))
