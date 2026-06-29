"""AI 助手对话 API.

为前端 AiAssistantPage 提供真实后端：
- POST /ai/chat : 与大模型对话（运行时模型配置 + 降级提示）

说明：历史上还有 POST /ai/execute（对话触发自动化执行），但前端从不产出可执行
actions、该端点与前端字段也不一致，属未完成的死路径，已移除。后续若要做
「对话触发执行」，应由 chat/agent 产出结构化方案，统一走自动化中心的
执行/审批链路（PolicyExecution/Execution），而非此处的临时 INSERT。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import success
from app.infra.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI助手"])

_SYSTEM_PROMPT = (
    "你是 AUTOPS 自治运维助手，面向私有化运维场景，回答需简洁、专业、可执行。"
    "涉及高危操作时请提示需人工审批。"
)


class ChatRequest(BaseModel):
    message: str
    history: list[dict] | None = None  # [{role, content}]


@router.post("/chat")
async def ai_chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """与大模型对话。模型不可用时返回降级提示，不抛错。"""
    if not req.message or not req.message.strip():
        return success({"reply": "请输入内容。", "degraded": False})

    from app.domains.aiops.model_runtime import build_llm_client

    client = await build_llm_client(db)
    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    if req.history:
        for h in req.history[-10:]:
            role = h.get("role")
            content = h.get("content")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": str(content)})
    messages.append({"role": "user", "content": req.message})

    try:
        reply = await client.chat(messages)
        degraded = reply == "LLM调用超时"
        return success({"reply": reply, "model": client.model, "degraded": degraded})
    except Exception as exc:  # noqa: BLE001
        logger.warning("AI chat 失败: %s", exc)
        return success(
            {
                "reply": "模型服务不可用，已降级。请检查「平台管理-模型服务」配置或本地模型是否启动。",
                "model": client.model,
                "degraded": True,
            }
        )
