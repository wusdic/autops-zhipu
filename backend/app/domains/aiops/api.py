"""AIops 中心 Service + API."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.exceptions import NotFoundError
from app.common.repository import BaseRepository
from app.common.response import paginate, success
from app.infra.config import get_config
from app.infra.database import get_db
from app.domains.aiops.models import AIAnalysis
from app.domains.aiops.schemas import AIAnalysisRequest, AIFeedback


class AIOpsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BaseRepository(session, AIAnalysis)
        self._config = None

    @property
    def llm_config(self):
        if self._config is None:
            self._config = get_config()
        return self._config

    async def request_analysis(self, data: AIAnalysisRequest) -> AIAnalysis:
        config = self.llm_config
        analysis = await self.repo.create(
            analysis_type=data.analysis_type,
            alert_id=data.alert_id,
            asset_ids=json.dumps(data.asset_ids) if data.asset_ids else None,
            model_name=getattr(config, 'llm_model', 'qwen3.5-0.8b'),
            status="running",
        )
        await self.session.flush()
        await self.session.refresh(analysis)

        # Build context
        input_context = await self._build_context(data)
        analysis.input_context = json.dumps(input_context, ensure_ascii=False)

        # Call LLM
        try:
            result = await self._call_llm(analysis)
            analysis.status = "completed"
            analysis.summary = result.get("summary", "")
            analysis.root_causes = json.dumps(result.get("root_causes", []), ensure_ascii=False)
            analysis.recommended_actions = json.dumps(result.get("recommended_actions", []), ensure_ascii=False)
            analysis.raw_output = json.dumps(result, ensure_ascii=False)
        except Exception as e:
            analysis.status = "failed"
            analysis.error_message = str(e)

        from datetime import timezone as _tz
        analysis.duration_ms = int((datetime.now(_tz.utc) - analysis.created_at).total_seconds() * 1000)
        await self.session.flush()
        await self.session.refresh(analysis)
        return analysis

    async def _build_context(self, data: AIAnalysisRequest) -> dict:
        context = {"analysis_type": data.analysis_type}
        if data.alert_id:
            context["alert_id"] = data.alert_id
        if data.asset_ids:
            context["asset_ids"] = data.asset_ids
        return context

    async def _call_llm(self, analysis: AIAnalysis) -> dict:
        config = self.llm_config
        base_url = getattr(config, 'llm_base_url', 'http://127.0.0.1:8000/v1')
        model = getattr(config, 'llm_model', 'qwen3.5-0.8b')

        prompt = f"""你是运维分析专家。请分析以下问题并给出结构化的JSON响应。
分析类型: {analysis.analysis_type}
上下文: {analysis.input_context}

请返回JSON格式:
{{
  "summary": "简要分析摘要",
  "root_causes": [{{"cause": "原因", "confidence": 0.8}}],
  "recommended_actions": [{{"action": "动作描述", "risk_level": "low"}}]
}}"""

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 1024,
                    },
                )
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"]
                    # Try to parse JSON from response
                    try:
                        # Find JSON block in response
                        start = content.find("{")
                        end = content.rfind("}") + 1
                        if start >= 0 and end > start:
                            return json.loads(content[start:end])
                    except json.JSONDecodeError:
                        pass
                    return {"summary": content, "root_causes": [], "recommended_actions": []}
                else:
                    raise Exception(f"LLM 返回状态码 {resp.status_code}")
        except httpx.ConnectError:
            # Model unavailable - graceful degradation
            return {
                "summary": "模型服务不可用，已降级处理",
                "root_causes": [],
                "recommended_actions": [],
            }

    async def list_analyses(
        self, analysis_type: str | None = None, status: str | None = None,
        page: int = 1, page_size: int = 20,
    ):
        stmt = select(AIAnalysis)
        if analysis_type:
            stmt = stmt.where(AIAnalysis.analysis_type == analysis_type)
        if status:
            stmt = stmt.where(AIAnalysis.status == status)
        total_result = await self.session.execute(select(func.count()).select_from(AIAnalysis))
        total = total_result.scalar() or 0
        result = await self.session.execute(stmt.order_by(AIAnalysis.created_at.desc()).offset((page-1)*page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def get_analysis(self, analysis_id: str) -> AIAnalysis:
        a = await self.repo.get_by_id(analysis_id)
        if not a:
            raise NotFoundError(f"AI 分析 {analysis_id} 不存在")
        return a

    async def submit_feedback(self, analysis_id: str, data: AIFeedback) -> AIAnalysis:
        a = await self.get_analysis(analysis_id)
        a.feedback_rating = data.rating
        a.feedback_comment = data.comment
        await self.session.flush()
        await self.session.refresh(a)
        return a


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


@router.post("/analyses/{analysis_id}/feedback")
async def submit_feedback(analysis_id: str, data: AIFeedback, svc: AIOpsService = Depends(_get_svc)):
    a = await svc.submit_feedback(analysis_id, data)
    return success(model_to_dict(a))
