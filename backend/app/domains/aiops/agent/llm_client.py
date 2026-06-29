"""LLM客户端 — OpenAI兼容接口 (增强版: 重试/缓存/超时/流式)."""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from collections import OrderedDict
from typing import AsyncIterator

import httpx

from app.common.exceptions import AppError, ErrorCode

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 内存 LRU 缓存 (Redis 不可用时的降级方案)，带 TTL 防止内存泄漏
# ---------------------------------------------------------------------------
_MAX_LRU_SIZE = 100
_LRU_TTL = 300  # 缓存条目存活秒数
_lru_cache: OrderedDict[str, tuple[str, float]] = OrderedDict()


def _lru_get(key: str) -> str | None:
    if key in _lru_cache:
        value, ts = _lru_cache[key]
        if time.monotonic() - ts < _LRU_TTL:
            _lru_cache.move_to_end(key)
            return value
        del _lru_cache[key]
    return None


def _lru_set(key: str, value: str) -> None:
    entry = (value, time.monotonic())
    if key in _lru_cache:
        _lru_cache.move_to_end(key)
    _lru_cache[key] = entry
    while len(_lru_cache) > _MAX_LRU_SIZE:
        _lru_cache.popitem(last=False)


# ---------------------------------------------------------------------------
# Redis 缓存辅助 (可选依赖, 失败自动降级)
# ---------------------------------------------------------------------------
async def _redis_get(key: str) -> str | None:
    """尝试从 Redis 读取缓存, 失败返回 None."""
    try:
        from app.infra.redis_client import get_redis
        redis = await get_redis()
        return await redis.get(key)
    except ImportError:
        return None
    except Exception:
        logger.debug("Redis get skipped (unavailable): %s", key[:24])
        return None


async def _redis_set(key: str, value: str, ttl: int = 300) -> None:
    """尝试写入 Redis 缓存, 失败静默忽略."""
    try:
        from app.infra.redis_client import get_redis
        redis = await get_redis()
        await redis.setex(key, ttl, value)
    except ImportError:
        pass
    except Exception:
        logger.debug("Redis set skipped (unavailable): %s", key[:24])


# ---------------------------------------------------------------------------
# LLM 配置加载辅助
# ---------------------------------------------------------------------------
def _load_llm_timeout() -> int:
    """从 configs/llm.yaml 读取 timeout, 默认 180s.

    带"思考块"的本地大模型单次推理可达数百秒，30s 默认会把正常推理误判为超时失败，
    故默认抬高到 180s（仍可在 llm.yaml 覆盖）。
    """
    try:
        from app.infra.config import _load_yaml
        cfg = _load_yaml("llm.yaml")
        return int(cfg.get("llm", {}).get("timeout", 180))
    except Exception:
        return 180


def _load_llm_max_tokens() -> int:
    """从 configs/llm.yaml 读取 max_tokens, 默认 2048."""
    try:
        from app.infra.config import _load_yaml
        cfg = _load_yaml("llm.yaml")
        return int(cfg.get("llm", {}).get("max_tokens", 2048))
    except Exception:
        return 2048


def _cache_key(messages: list[dict[str, str]]) -> str:
    """根据 messages 列表生成缓存 key."""
    raw = json.dumps(messages, sort_keys=True, ensure_ascii=False)
    return f"llm:cache:{hashlib.md5(raw.encode()).hexdigest()}"


# ---------------------------------------------------------------------------
# LLMClient
# ---------------------------------------------------------------------------
class LLMClient:
    """OpenAI兼容LLM客户端 (增强版)."""

    # 重试配置
    MAX_RETRIES = 3
    BACKOFF_BASE = 1.0  # 指数退避基数(秒)

    def __init__(self):
        from app.infra.config import get_config
        config = get_config()
        # AppConfig.llm is a LlmConfig instance
        llm_cfg = getattr(config, 'llm', None)
        if llm_cfg:
            self.base_url = getattr(llm_cfg, 'base_url', '') or 'http://127.0.0.1:8000/v1'
            self.model = getattr(llm_cfg, 'model_name', '') or 'qwen3.5-0.8b'
            self.api_key = getattr(llm_cfg, 'api_key', '') or 'EMPTY'
        else:
            self.base_url = getattr(config, 'llm_base_url', 'http://127.0.0.1:8000/v1')
            self.model = getattr(config, 'llm_model_name', getattr(config, 'llm_model', 'qwen3.5-0.8b'))
            self.api_key = getattr(config, 'llm_api_key', 'EMPTY')

        # timeout 从 llm.yaml 读取, 保持向后兼容
        self.timeout = _load_llm_timeout()
        self.max_tokens = _load_llm_max_tokens()

        # 透传给推理后端的 chat 模板参数（如 Qwen3 的 enable_thinking）。
        # None = 不发送（对云端/非 Qwen 最安全）；由 model_runtime 按模型配置注入。
        self.chat_template_kwargs: dict | None = None

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------
    async def chat(self, messages: list[dict[str, str]]) -> str:
        """调用LLM，返回文本响应 (带重试+缓存+超时降级)."""
        # 1) 尝试缓存
        cache_k = _cache_key(messages)
        cached = await self._get_cache(cache_k)
        if cached is not None:
            logger.debug("LLM cache hit: %s", cache_k[:24])
            return cached

        # 2) 带重试的调用
        last_exc: Exception | None = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                result = await self._do_chat(messages)
                # 写入缓存
                await self._set_cache(cache_k, result)
                return result
            except httpx.TimeoutException as exc:
                logger.warning("LLM timeout (attempt %d/%d): %s", attempt, self.MAX_RETRIES, exc)
                last_exc = exc
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(self.BACKOFF_BASE * (2 ** (attempt - 1)))
            except Exception as exc:
                logger.warning("LLM error (attempt %d/%d): %s", attempt, self.MAX_RETRIES, exc)
                last_exc = exc
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(self.BACKOFF_BASE * (2 ** (attempt - 1)))

        # 全部重试耗尽 — 超时降级
        if isinstance(last_exc, httpx.TimeoutException):
            logger.error("LLM调用超时, 已重试 %d 次", self.MAX_RETRIES)
            return "LLM调用超时"
        raise last_exc  # type: ignore[misc]

    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        """流式调用LLM, 逐块yield SSE chunk内容."""
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key and self.api_key != "EMPTY":
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": self.max_tokens,
            "stream": True,
        }
        if self.chat_template_kwargs is not None:
            payload["chat_template_kwargs"] = self.chat_template_kwargs

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status_code != 200:
                    error_text = await resp.aread()
                    logger.error("LLM stream error: %s %s", resp.status_code, error_text[:200])
                    raise AppError(ErrorCode.AI_UNAVAILABLE_ANALYSIS, f"LLM stream returned status {resp.status_code}", 502)

                async for line in resp.aiter_lines():
                    # SSE 格式: "data: {...}" 或 "data: [DONE]"
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    async def is_available(self) -> bool:
        """检查LLM服务是否可用."""
        try:
            base = self.base_url.rstrip("/")
            if base.endswith("/v1"):
                check_url = f"{base}/models"
            else:
                check_url = f"{base}/v1/models"
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(check_url)
                return resp.status_code == 200
        except Exception:
            return False

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------
    async def _do_chat(self, messages: list[dict[str, str]]) -> str:
        """单次 LLM HTTP 调用."""
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key and self.api_key != "EMPTY":
            headers["Authorization"] = f"Bearer {self.api_key}"

        chat_payload: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": self.max_tokens,
        }
        if self.chat_template_kwargs is not None:
            chat_payload["chat_template_kwargs"] = self.chat_template_kwargs

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json=chat_payload,
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                content = (data["choices"][0]["message"].get("content") or "").strip()
                if content:
                    return content
                # 某些模型/推理端（如 Qwen MTP + llama.cpp 内置 jinja 模板）chat 接口
                # 返回空内容；降级到 /completions + 手工 ChatML 拼接。
                logger.warning("LLM chat 返回空内容，降级到 /completions")
                return await self._do_completions(messages, headers)
            logger.error("LLM error: %s %s", resp.status_code, resp.text[:200])
            raise AppError(ErrorCode.AI_UNAVAILABLE_ANALYSIS, f"LLM returned status {resp.status_code}", 502)

    @staticmethod
    def _messages_to_chatml(messages: list[dict[str, str]]) -> str:
        """把 messages 拼成 ChatML prompt（用于 /completions 降级路径）."""
        parts = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")
        parts.append("<|im_start|>assistant\n")
        return "\n".join(parts)

    async def _do_completions(
        self, messages: list[dict[str, str]], headers: dict[str, str]
    ) -> str:
        """降级路径：调用 /completions（文本补全）端点."""
        base = self.base_url.rstrip("/")
        url = f"{base}/completions" if base.endswith("/v1") else f"{base}/v1/completions"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                url,
                json={
                    "model": self.model,
                    "prompt": self._messages_to_chatml(messages),
                    "temperature": 0.3,
                    "max_tokens": self.max_tokens,
                    "stop": ["<|im_end|>"],
                },
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                return (data["choices"][0].get("text") or "").strip()
            logger.error("LLM completions error: %s %s", resp.status_code, resp.text[:200])
            raise AppError(
                ErrorCode.AI_UNAVAILABLE_ANALYSIS,
                f"LLM completions returned status {resp.status_code}", 502,
            )

    async def _get_cache(self, key: str) -> str | None:
        """优先 Redis → 降级 LRU."""
        val = await _redis_get(key)
        if val is not None:
            return val
        return _lru_get(key)

    async def _set_cache(self, key: str, value: str) -> None:
        """写入 Redis + LRU."""
        await _redis_set(key, value, ttl=300)
        _lru_set(key, value)
