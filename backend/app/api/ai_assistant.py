"""AI 助手对话 API.

为前端 AiAssistantPage 提供真实后端：
- POST /ai/chat : 与大模型对话（运行时模型配置 + 降级提示）

说明：历史上还有 POST /ai/execute（对话触发自动化执行），但前端从不产出可执行
actions、该端点与前端字段也不一致，属未完成的死路径，已移除。后续若要做
「对话触发执行」，应由 chat/agent 产出结构化方案，统一走自动化中心的
执行/审批链路（PolicyExecution/Execution），而非此处的临时 INSERT。
"""

from __future__ import annotations

import json
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
    "当用户询问本系统内的数据（资产数量/告警/事件/知识等）时，调用提供的工具查询真实数据后再回答；"
    "普通问题直接回答即可。涉及高危操作时请提示需人工审批。"
)

# 单轮对话内最多工具调用轮数，避免小模型反复调用
_MAX_TOOL_ROUNDS = 4


def _readonly_tools_schema() -> list[dict]:
    """把已注册的只读工具转成 OpenAI function-calling 的 tools schema。

    仅暴露 read_only 工具：AI 助手只读查询，绝不在对话里触发有副作用的执行类工具。
    """
    from app.domains.aiops.tools.registry import ToolRegistry

    tools = []
    for t in ToolRegistry.get_instance().list_tools():
        if t.get("risk_level") != "read_only":
            continue
        tools.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            },
        })
    return tools


class ChatRequest(BaseModel):
    message: str
    history: list[dict] | None = None  # [{role, content}]


@router.post("/chat")
async def ai_chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """与大模型对话（OpenAI 原生 function calling）。

    用 OpenAI 标准 tools/tool_calls 协议而非 ReAct 文本解析：模型对"我有多少资产"等
    问题会返回结构化 tool_calls，我们执行只读工具并回灌结果；普通问题直接回答。
    这比 ReAct 文本协议稳健得多（无需小模型严格遵守 Thought/Action 文本格式）。
    端点不支持 tools 或模型不可用时，降级为纯聊天/降级提示，绝不返回硬编码假答案。
    """
    if not req.message or not req.message.strip():
        return success({"reply": "请输入内容。", "degraded": False})

    from app.domains.aiops.model_runtime import build_llm_client

    client = await build_llm_client(db)

    base_messages: list[dict] = [{"role": "system", "content": _SYSTEM_PROMPT}]
    if req.history:
        for h in req.history[-10:]:
            role = h.get("role")
            content = h.get("content")
            if role in ("user", "assistant") and content:
                base_messages.append({"role": role, "content": str(content)})
    base_messages.append({"role": "user", "content": req.message})
    messages = list(base_messages)  # 工具循环使用的工作副本（会追加 tool 消息）

    from app.domains.aiops.tools.registry import ToolRegistry
    registry = ToolRegistry.get_instance()
    tools_schema = _readonly_tools_schema()
    used_tools: list[str] = []

    try:
        reply = ""
        for _ in range(_MAX_TOOL_ROUNDS):
            msg = await client.chat_raw(messages, tools=tools_schema or None)
            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                reply = (msg.get("content") or "").strip()
                break
            # 记录本轮 assistant 消息（含 tool_calls），再逐个执行只读工具
            messages.append({
                "role": "assistant",
                "content": msg.get("content") or "",
                "tool_calls": tool_calls,
            })
            for tc in tool_calls:
                fn = tc.get("function", {}) or {}
                name = fn.get("name", "")
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except (json.JSONDecodeError, ValueError):
                    args = {}
                tdef = registry.get_tool(name)
                if tdef is None or tdef.risk_level != "read_only":
                    out: object = {"error": f"工具不可用或非只读: {name}"}
                else:
                    used_tools.append(name)
                    try:
                        out = await registry.execute(name, **args)
                    except Exception as e:  # noqa: BLE001
                        out = {"error": f"工具执行失败: {e}"}
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id"),
                    "content": json.dumps(out, ensure_ascii=False, default=str),
                })
        else:
            # 达到工具轮数上限：再要一次（不带 tools）让模型据已收集信息作答
            final = await client.chat_raw(messages)
            reply = (final.get("content") or "").strip()

        reply = reply or "（模型未返回内容）"
        return success({
            "reply": reply,
            "model": client.model,
            "degraded": reply == "（模型未返回内容）",
            "tool_calls": used_tools,
        })
    except Exception as exc:  # noqa: BLE001
        # 端点不支持 tools / 模型不可用 → 退回纯聊天（仍是真模型，不编造）
        logger.warning("AI chat function-calling 失败，降级纯聊天: %s", exc)
        try:
            reply = await client.chat(base_messages)
            reply = (reply or "").strip() or "（模型未返回内容）"
            degraded = reply in ("LLM调用超时", "（模型未返回内容）")
            return success({"reply": reply, "model": client.model, "degraded": degraded})
        except Exception as exc2:  # noqa: BLE001
            logger.warning("AI chat 纯聊天兜底也失败: %s", exc2)
            return success({
                "reply": "模型服务不可用，已降级。请检查「平台管理-模型服务」配置或本地模型是否启动。",
                "model": client.model,
                "degraded": True,
            })
