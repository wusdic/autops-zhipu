"""ToolGuard 安全边界."""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

class RiskLevel(str, Enum):
    READ_ONLY = "read_only"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FORBIDDEN = "forbidden"

@dataclass
class GuardResult:
    """安全检查结果."""
    allowed: bool
    risk_level: RiskLevel
    needs_approval: bool
    reason: str
    tool_name: str

class ToolGuard:
    """AI 工具调用安全边界."""

    def __init__(self):
        self._approval_required = {RiskLevel.MEDIUM, RiskLevel.HIGH}
        self._forbidden = {RiskLevel.FORBIDDEN}
        self._blocked_tools: set[str] = set()

    def evaluate(self, tool_name: str, tool_risk: str, args: dict | None = None) -> GuardResult:
        risk = RiskLevel(tool_risk)

        if tool_name in self._blocked_tools:
            return GuardResult(
                allowed=False, risk_level=risk, needs_approval=False,
                reason=f"工具 '{tool_name}' 已被管理员禁止", tool_name=tool_name
            )

        if risk in self._forbidden:
            return GuardResult(
                allowed=False, risk_level=risk, needs_approval=False,
                reason=f"工具风险等级 '{risk.value}' 被禁止自动执行", tool_name=tool_name
            )

        if risk in self._approval_required:
            return GuardResult(
                allowed=True, risk_level=risk, needs_approval=True,
                reason=f"工具风险等级 '{risk.value}' 需要人工审批", tool_name=tool_name
            )

        return GuardResult(
            allowed=True, risk_level=risk, needs_approval=False,
            reason="通过安全检查", tool_name=tool_name
        )

    def block_tool(self, tool_name: str):
        self._blocked_tools.add(tool_name)

    def unblock_tool(self, tool_name: str):
        self._blocked_tools.discard(tool_name)
