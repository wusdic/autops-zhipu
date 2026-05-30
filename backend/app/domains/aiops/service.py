"""AIops 中心 Service."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.common.repository import BaseRepository
from app.infra.config import get_config
from app.domains.aiops.models import AIAnalysis
from app.domains.aiops.schemas import AIAnalysisRequest, AIFeedback


class AIOpsService:
    """AIops 业务逻辑."""

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
            model_name=getattr(config, 'model_name', getattr(config, 'llm_model', 'default')),
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

        analysis.duration_ms = int((datetime.now(timezone.utc) - analysis.created_at).total_seconds() * 1000)
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
        base_url = getattr(config, 'llm_base_url', '')
        model = getattr(config, 'model_name', getattr(config, 'llm_model', 'default'))

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

    # --- LLM 健康检查 ---

    @staticmethod
    async def check_llm_health() -> dict:
        """检查 LLM 服务是否可用."""
        try:
            config = get_config()
            base_url = getattr(config, 'llm_base_url', '')
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{base_url}/models")
                if resp.status_code == 200:
                    models = resp.json().get("data", [])
                    model_names = [m.get("id", "") for m in models]
                    return {"available": True, "models": model_names}
        except Exception:
            pass
        return {"available": False, "models": []}

    # --- 快捷诊断 ---

    async def diagnose(self, data: dict) -> dict:
        """前端快捷诊断."""
        from app.common.crud_service import model_to_dict

        question = data.get("question", "")
        context = data.get("context", "")
        asset_type = data.get("asset_type", "")
        alert_id = data.get("alert_id")
        alert_title = data.get("alert_title", "")
        # alert_context = data.get("alert_context", "")

        # 如果有告警ID，优先做告警分析
        if alert_id or alert_title:
            analysis_req = AIAnalysisRequest(
                analysis_type="root_cause",
                alert_id=alert_id,
                asset_ids=data.get("asset_ids"),
            )
            a = await self.request_analysis(analysis_req)
            result = model_to_dict(a)
            result["root_cause"] = result.get("summary", "")
            result["confidence"] = 75
            result["recommendations"] = []
            if result.get("recommended_actions"):
                try:
                    actions = json.loads(result["recommended_actions"]) if isinstance(result["recommended_actions"], str) else result["recommended_actions"]
                    result["recommendations"] = [{"action": act.get("action", str(act)), "risk": act.get("risk_level", "low"), "auto": True} for act in actions]
                except Exception:
                    pass
            if result.get("raw_output"):
                try:
                    raw = json.loads(result["raw_output"]) if isinstance(result["raw_output"], str) else result["raw_output"]
                    result["raw_response"] = json.dumps(raw, ensure_ascii=False, indent=2)
                except Exception:
                    result["raw_response"] = result.get("raw_output", "")
            return result

        # 自由问答模式
        config = self.llm_config
        base_url = getattr(config, 'llm_base_url', '')
        model = getattr(config, 'model_name', getattr(config, 'llm_model', 'default'))

        system_prompt = """你是 AUTOPS 自治运维系统的 AI 运维分析专家。你的职责是：
1. 分析运维问题的根因
2. 提供结构化的处置建议
3. 评估操作风险

请用 JSON 格式回复：
{"root_cause": "根因分析", "confidence": 85, "recommendations": [{"action": "具体动作", "risk": "low/medium/high", "auto": true/false}]}"""

        user_prompt = f"问题: {question}"
        if context:
            user_prompt += f"\n上下文: {context}"
        if asset_type:
            user_prompt += f"\n资产类型: {asset_type}"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1024,
                    },
                )
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"]
                    result = {"raw_response": content}
                    try:
                        start = content.find("{")
                        end = content.rfind("}") + 1
                        if start >= 0 and end > start:
                            parsed = json.loads(content[start:end])
                            result.update(parsed)
                    except json.JSONDecodeError:
                        result["root_cause"] = content
                        result["confidence"] = 50
                        result["recommendations"] = []
                    return result
                return {"error": f"LLM 返回 {resp.status_code}", "root_cause": "模型服务暂时不可用", "confidence": 0, "recommendations": []}
        except httpx.ConnectError:
            return {"error": "模型服务不可用", "root_cause": "vLLM 服务未启动", "confidence": 0, "recommendations": []}
        except Exception as e:
            return {"error": str(e), "root_cause": "分析失败", "confidence": 0, "recommendations": []}
