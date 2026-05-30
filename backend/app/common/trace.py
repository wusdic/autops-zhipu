"""trace_id 中间件."""

from __future__ import annotations

import uuid

from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
from starlette.responses import Response


class TraceIdMiddleware:
    """为每个请求生成唯一 trace_id（纯 ASGI 实现）."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        trace_id = ""
        for name, value in scope.get("headers", []):
            if name == b"x-trace-id":
                trace_id = value.decode()
                break
        if not trace_id:
            trace_id = str(uuid.uuid4())

        scope["state"] = scope.get("state") or {}
        scope["state"]["trace_id"] = trace_id

        async def send_with_trace(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-trace-id", trace_id.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_trace)
