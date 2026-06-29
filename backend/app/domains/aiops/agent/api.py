"""AI Agent API 端点."""
from __future__ import annotations
import json
import logging
from uuid import uuid4
from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infra.database import get_db
from app.common.response import error, success
from app.domains.aiops.agent.react import ReActAgent
from app.domains.aiops.agent.context import ContextBuilder
from app.domains.aiops.models import AIAnalysis

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Agent"])


class AgentRunRequest(BaseModel):
    task: str
    alert_id: str | None = None
    context: dict | None = None


class AgentApproveRequest(BaseModel):
    approved: bool
    reason: str | None = None


@router.post("/agent/run")
async def run_agent(req: AgentRunRequest, db: AsyncSession = Depends(get_db)):
    """运行AI Agent推理循环."""
    from app.domains.aiops.model_runtime import build_llm_client

    # 走统一运行时配置，让「模型服务」页注册的本地/默认模型对 Agent 同样生效
    llm = await build_llm_client(db)
    agent = ReActAgent(llm_client=llm)

    # 构建上下文
    context = req.context or {}
    if req.alert_id:
        try:
            builder = ContextBuilder(db)
            alert_ctx = await builder.build_alert_context(req.alert_id)
            context.update(alert_ctx)
        except Exception as e:
            logger.warning(f"Failed to build alert context: {e}")

    # 运行Agent
    result = await agent.run(task=req.task, context=context)

    # 持久化到ai_analyses
    analysis = AIAnalysis(
        id=str(uuid4()),
        analysis_type="agent",
        alert_id=req.alert_id,
        model_name=llm.model,
        input_context=json.dumps({"task": req.task, "context": context}, ensure_ascii=False, default=str),
        summary=result.answer[:500],
        root_causes=json.dumps([s.thought for s in result.steps[:3]], ensure_ascii=False),
        recommended_actions=json.dumps(result.tool_calls, ensure_ascii=False),
        status="completed" if not result.pending_approval else "pending_approval",
        created_at=datetime.now(timezone.utc),
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    return success({
        "id": str(analysis.id),
        "answer": result.answer,
        "steps": [
            {
                "thought": s.thought,
                "action": s.action,
                "action_input": s.action_input,
                "observation": s.observation if isinstance(s.observation, str) else str(s.observation)[:200],
                "final_answer": s.final_answer,
            }
            for s in result.steps
        ],
        "pending_approval": result.pending_approval is not None,
        "total_iterations": result.total_iterations,
        "tool_calls": result.tool_calls,
    })


@router.get("/agent/results")
async def list_agent_results(
    page: int = 1, page_size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """查询Agent运行历史."""
    from sqlalchemy import select, func
    stmt = select(AIAnalysis).where(AIAnalysis.analysis_type == "agent")
    total_q = await db.execute(select(func.count()).select_from(AIAnalysis).where(AIAnalysis.analysis_type == "agent"))
    total = total_q.scalar() or 0
    result = await db.execute(
        stmt.order_by(AIAnalysis.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    items = result.scalars().all()
    return success({
        "items": [
            {
                "id": str(a.id),
                "task": json.loads(a.input_context).get("task", "")[:100] if a.input_context else "",
                "summary": a.summary[:200] if a.summary else "",
                "status": a.status,
                "model": a.model_name,
                "created_at": str(a.created_at),
            }
            for a in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/agent/{analysis_id}")
async def get_agent_result(analysis_id: str, db: AsyncSession = Depends(get_db)):
    """查询单条 Agent 运行结果（供历史回看）。"""
    from sqlalchemy import select

    res = await db.execute(select(AIAnalysis).where(AIAnalysis.id == analysis_id))
    a = res.scalar_one_or_none()
    if not a:
        return error(1, "Analysis not found")

    def _loads(v, default):
        try:
            return json.loads(v) if v else default
        except (json.JSONDecodeError, ValueError, TypeError):
            return default

    thoughts = _loads(a.root_causes, [])
    return success({
        "id": str(a.id),
        "task": _loads(a.input_context, {}).get("task", "") if a.input_context else "",
        "summary": a.summary or "",
        "steps": [{"thought": t} for t in thoughts] if isinstance(thoughts, list) else [],
        "tool_calls": _loads(a.recommended_actions, []),
        "status": a.status,
        "model": a.model_name,
        "created_at": str(a.created_at),
    })


@router.post("/agent/{analysis_id}/approve")
async def approve_agent_action(
    analysis_id: str,
    req: AgentApproveRequest,
    db: AsyncSession = Depends(get_db),
):
    """审批Agent动作."""
    from sqlalchemy import select
    result = await db.execute(select(AIAnalysis).where(AIAnalysis.id == analysis_id))
    analysis = result.scalar_one_or_none()
    if not analysis:
        return error(1, "Analysis not found")

    if req.approved:
        analysis.status = "approved"
    else:
        analysis.status = "rejected"

    if req.reason:
        existing = json.loads(analysis.recommended_actions) if analysis.recommended_actions else []
        existing.append({"approval_note": req.reason})
        analysis.recommended_actions = json.dumps(existing, ensure_ascii=False)

    await db.commit()
    return success({"id": str(analysis.id), "status": analysis.status})
