"""LLM客户端 — OpenAI兼容接口."""
from __future__ import annotations
import logging
import httpx
from typing import Any

logger = logging.getLogger(__name__)


class LLMClient:
    """OpenAI兼容LLM客户端."""

    def __init__(self):
        from app.infra.config import get_config
        config = get_config()
        # AppConfig.llm is a LlmConfig instance
        llm_cfg = getattr(config, 'llm', None)
        if llm_cfg:
            self.base_url = getattr(llm_cfg, 'base_url', '') or 'http://127.0.0.1:8000/v1'
            self.model = getattr(llm_cfg, 'model_name', '') or 'qwen3.5-0.8b'
            self.api_key = getattr(llm_cfg, 'api_key', '') or 'EMPTY'
            self.timeout = 60
        else:
            self.base_url = getattr(config, 'llm_base_url', 'http://127.0.0.1:8000/v1')
            self.model = getattr(config, 'llm_model_name', getattr(config, 'llm_model', 'qwen3.5-0.8b'))
            self.api_key = getattr(config, 'llm_api_key', 'EMPTY')
            self.timeout = getattr(config, 'llm_timeout', 60)

    async def chat(self, messages: list[dict[str, str]]) -> str:
        """调用LLM，返回文本响应."""
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key and self.api_key != "EMPTY":
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 2048,
                },
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            logger.error(f"LLM error: {resp.status_code} {resp.text[:200]}")
            raise Exception(f"LLM returned status {resp.status_code}")

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
