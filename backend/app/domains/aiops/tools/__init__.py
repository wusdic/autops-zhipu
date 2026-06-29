"""AI Agent 工具框架.

关键：导入本包即注册所有工具。历史上 readonly/execution 从未被任何地方导入，
其模块级 @registry.register 装饰器从不执行 → ToolRegistry 单例为空 → ReAct Agent
(/aiops/agent/run) 与 AI 助手都拿不到任何工具，永远无法查询 DB。
在此显式导入工具模块，确保只要用到工具框架（react.py 通过本包导入 registry）即完成注册。
"""
from app.domains.aiops.tools.registry import ToolRegistry, tool
from app.domains.aiops.tools.guard import ToolGuard, RiskLevel

# 触发工具注册（模块级 @registry.register 副作用）；放在末尾避免循环导入
from app.domains.aiops.tools import readonly as _readonly  # noqa: E402,F401
from app.domains.aiops.tools import execution as _execution  # noqa: E402,F401

__all__ = ["ToolRegistry", "ToolGuard", "RiskLevel", "tool"]
