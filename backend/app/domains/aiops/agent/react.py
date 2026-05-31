"""ReAct (Reasoning + Acting) Agent 推理循环."""
from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field
from typing import Any
from app.domains.aiops.tools.registry import ToolRegistry
from app.domains.aiops.tools.guard import ToolGuard, GuardResult

logger = logging.getLogger(__name__)

@dataclass
class AgentStep:
    """Agent 单步记录."""
    thought: str
    action: str | None = None
    action_input: dict | None = None
    observation: Any = None
    final_answer: str | None = None

@dataclass
class AgentResult:
    """Agent 执行结果."""
    answer: str
    steps: list[AgentStep] = field(default_factory=list)
    pending_approval: GuardResult | None = None
    total_iterations: int = 0
    tool_calls: list[str] = field(default_factory=list)

class ReActAgent:
    """ReAct 推理循环 Agent.
    
    Thought → Action → Observation → Thought → ... → Final Answer
    """

    MAX_ITERATIONS = 10

    def __init__(self, llm_client=None, tool_registry: ToolRegistry | None = None, tool_guard: ToolGuard | None = None):
        self.llm = llm_client
        self.registry = tool_registry or ToolRegistry.get_instance()
        self.guard = tool_guard or ToolGuard()

    async def run(self, task: str, context: dict | None = None) -> AgentResult:
        """执行 ReAct 推理循环."""
        steps: list[AgentStep] = []

        system_prompt = self._build_system_prompt(context)
        user_prompt = f"任务: {task}\n\n请开始分析和处理。"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for i in range(self.MAX_ITERATIONS):
            # 调用 LLM
            try:
                response = await self._call_llm(messages)
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return AgentResult(
                    answer=f"LLM 调用失败: {e}",
                    steps=steps,
                    total_iterations=i + 1,
                )

            # 解析响应
            parsed = self._parse_response(response)

            step = AgentStep(thought=parsed.get("thought", ""))

            # Final Answer
            if "final_answer" in parsed:
                step.final_answer = parsed["final_answer"]
                steps.append(step)
                return AgentResult(
                    answer=parsed["final_answer"],
                    steps=steps,
                    total_iterations=i + 1,
                    tool_calls=[s.action for s in steps if s.action],
                )

            # Action
            tool_name = parsed.get("action")
            tool_args = parsed.get("action_input", {})

            if not tool_name:
                step.final_answer = response
                steps.append(step)
                return AgentResult(
                    answer=response,
                    steps=steps,
                    total_iterations=i + 1,
                )

            step.action = tool_name
            step.action_input = tool_args

            # ToolGuard 安全检查
            tool_def = self.registry.get_tool(tool_name)
            if tool_def is None:
                step.observation = f"错误: 工具 '{tool_name}' 不存在。可用工具: {[t['name'] for t in self.registry.list_tools()]}"
                steps.append(step)
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": f"Observation: {step.observation}"})
                continue

            guard_result = self.guard.evaluate(tool_name, tool_def.risk_level, tool_args)
            if not guard_result.allowed:
                step.observation = f"安全拦截: {guard_result.reason}"
                steps.append(step)
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": f"Observation: {step.observation}"})
                continue

            if guard_result.needs_approval:
                steps.append(step)
                return AgentResult(
                    answer=f"工具 '{tool_name}' 需要人工审批后才能执行。原因: {guard_result.reason}",
                    steps=steps,
                    pending_approval=guard_result,
                    total_iterations=i + 1,
                    tool_calls=[s.action for s in steps if s.action],
                )

            # 执行工具
            try:
                result = await self.registry.execute(tool_name, **tool_args)
                step.observation = json.dumps(result, ensure_ascii=False, default=str) if not isinstance(result, str) else result
            except Exception as e:
                step.observation = f"工具执行失败: {e}"

            steps.append(step)
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": f"Observation: {step.observation}"})

        return AgentResult(
            answer="达到最大迭代次数，未能得出结论。",
            steps=steps,
            total_iterations=self.MAX_ITERATIONS,
            tool_calls=[s.action for s in steps if s.action],
        )

    def _build_system_prompt(self, context: dict | None = None) -> str:
        tools_desc = "\n".join(
            f"- {t['name']}: {t['description']} (风险: {t['risk_level']}, 参数: {json.dumps(t['parameters'], ensure_ascii=False)})"
            for t in self.registry.list_tools()
        )
        ctx_str = ""
        if context:
            ctx_str = f"\n当前上下文:\n{json.dumps(context, ensure_ascii=False, indent=2, default=str)}\n"

        return f"""你是 AUTOPS 运维平台的 AI Agent。你需要分析告警、诊断问题并推荐修复方案。

可用工具:
{tools_desc}
{ctx_str}
请按 ReAct 格式响应:
Thought: 你的分析思考
Action: 要调用的工具名
Action Input: 工具参数(JSON)
或者:
Thought: 你的分析思考
Final Answer: 最终结论和建议

注意:
- 先用只读工具收集信息，再考虑执行操作
- 高风险操作需要人工审批
- 每步都要解释你的推理过程
"""

    async def _call_llm(self, messages: list[dict]) -> str:
        """调用 LLM."""
        if self.llm:
            return await self.llm.chat(messages)
        # 降级模式：返回固定响应
        return "Thought: 需要更多信息\nFinal Answer: LLM 服务暂不可用，请稍后重试。"

    def _parse_response(self, response: str) -> dict:
        """解析 LLM 响应."""
        result = {}
        lines = response.strip().split("\n")
        for line in lines:
            if line.startswith("Thought:"):
                result["thought"] = line[8:].strip()
            elif line.startswith("Action:"):
                result["action"] = line[7:].strip()
            elif line.startswith("Action Input:"):
                try:
                    result["action_input"] = json.loads(line[13:].strip())
                except json.JSONDecodeError:
                    result["action_input"] = {}
            elif line.startswith("Final Answer:"):
                result["final_answer"] = line[14:].strip()
        if "thought" not in result:
            result["thought"] = response[:200]
        return result
