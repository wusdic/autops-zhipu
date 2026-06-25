"""AI 助手对话 API.

为前端 AiAssistantPage 提供真实后端：
- POST /ai/chat    : 与大模型对话（运行时模型配置 + 降级提示）
- POST /ai/execute : 由对话触发自动化执行（创建执行记录，复用执行链路）
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
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


class ExecuteRequest(BaseModel):
    script_id: str
    asset_id: str
    dry_run: bool = True


def _valid_id(v: str) -> bool:
    return bool(v) and bool(re.fullmatch(r"[A-Za-z0-9_-]+", v))


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


@router.post("/execute")
async def ai_execute(req: ExecuteRequest, db: AsyncSession = Depends(get_db)):
    """由 AI 助手触发脚本执行：创建一条执行记录（默认 dry-run），交由执行链路处理。"""
    if not _valid_id(req.script_id) or not _valid_id(req.asset_id):
        from app.common.exceptions import ValidationError

        raise ValidationError("script_id / asset_id 非法")

    exec_id = str(uuid4())
    await db.execute(
        text(
            "INSERT INTO executions (id, execution_type, target_id, asset_ids, status, "
            "is_dry_run, created_at) VALUES (:id, 'script', :target, :assets, 'pending', "
            ":dry, :ts)"
        ),
        {
            "id": exec_id,
            "target": req.script_id,
            "assets": json.dumps([req.asset_id]),
            "dry": req.dry_run,
            "ts": datetime.now(timezone.utc),
        },
    )
    await db.commit()
    return success(
        {
            "execution_id": exec_id,
            "status": "pending",
            "is_dry_run": req.dry_run,
            "message": "执行已创建，请在自动化中心查看进度",
        }
    )
