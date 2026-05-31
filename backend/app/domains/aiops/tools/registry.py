"""工具注册中心."""
from __future__ import annotations
import inspect
import logging
from typing import Any, Callable
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ToolDefinition(BaseModel):
    """工具定义."""
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema
    risk_level: str  # read_only, low, medium, high, forbidden
    func: Callable | None = None

    class Config:
        arbitrary_types_allowed = True

class ToolRegistry:
    """全局工具注册中心."""
    _instance: ToolRegistry | None = None
    _tools: dict[str, ToolDefinition]

    def __init__(self):
        self._tools = {}

    @classmethod
    def get_instance(cls) -> ToolRegistry:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, name: str, description: str, parameters: dict, risk_level: str = "read_only"):
        """装饰器：注册工具."""
        def decorator(func: Callable):
            self._tools[name] = ToolDefinition(
                name=name,
                description=description,
                parameters=parameters,
                risk_level=risk_level,
                func=func,
            )
            return func
        return decorator

    def get_tool(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        return [
            {"name": t.name, "description": t.description, "parameters": t.parameters, "risk_level": t.risk_level}
            for t in self._tools.values()
        ]

    async def execute(self, name: str, **kwargs) -> Any:
        tool_def = self._tools.get(name)
        if tool_def is None:
            raise ValueError(f"Tool not found: {name}")
        if tool_def.func is None:
            raise ValueError(f"Tool has no implementation: {name}")
        result = tool_def.func(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return result


def tool(name: str, description: str, parameters: dict, risk_level: str = "read_only"):
    """便捷装饰器."""
    registry = ToolRegistry.get_instance()
    return registry.register(name, description, parameters, risk_level)
