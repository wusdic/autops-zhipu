# AUTOPS AI Agent 架构设计

> 文档状态：current
> 是否为事实源：yes
> 建议路径：`docs/01-architecture/AI_AGENT_ARCHITECTURE.md`

---

## 1. 定位

AI 在 AUTOPS 中是**受控诊断与决策辅助层**，不是自由执行器。

**AI 可以做的：**
- 分析告警和事件
- 诊断根因
- 推荐处置方案
- 生成知识草稿
- 解释日志内容
- 调用只读工具查询信息

**AI 不可做的：**
- 直接执行任何变更动作
- 绕过策略中心
- 绕过审批机制
- 读取明文凭证
- 修改权限配置

---

## 2. AI 能力架构

```text
┌────────────────────────────────────────────────┐
│                 AI Request                      │
│  触发源: 告警 / 工单 / 手动 / 策略              │
├────────────────────────────────────────────────┤
│              Context Builder                    │
│  资产信息 + 状态 + 指标 + 事件 + 日志           │
│  + 配置变更 + 执行记录 + 工单 + 知识库          │
├────────────────────────────────────────────────┤
│             LLM Service                        │
│  配置化模型 (vLLM / Ollama / OpenAI兼容)        │
│  Prompt 模板管理                                │
├────────────────────────────────────────────────┤
│           Tool Guard Layer                      │
│  只读工具白名单 + 调用审计 + 超时控制            │
├────────────────────────────────────────────────┤
│         Output Parser                           │
│  结构化 JSON 输出 + 校验                        │
├────────────────────────────────────────────────┤
│         Action Recommendation                   │
│  推荐动作 → 策略校验 → 审批（如需）             │
└────────────────────────────────────────────────┘
```

---

## 3. LLM 配置

### 3.1 配置文件 configs/llm.yaml

```yaml
llm:
  provider: vllm
  base_url: http://127.0.0.1:8000/v1
  model: qwen3.5-0.8b
  timeout_seconds: 60
  max_tokens: 2048
  temperature: 0.2
  api_key: ""  # 可选

  # 备选模型（故障转移）
  fallback:
    provider: ollama
    base_url: http://127.0.0.1:11434/v1
    model: qwen2.5:0.5b

embedding:
  provider: local
  model: configurable-embedding-model
  base_url: http://127.0.0.1:8001

# 不同场景可配置不同模型
scene_models:
  root_cause_analysis:
    model: qwen3.5-0.8b
    temperature: 0.1
    max_tokens: 4096
  log_interpretation:
    model: qwen3.5-0.8b
    temperature: 0.2
    max_tokens: 2048
  knowledge_qa:
    model: qwen3.5-0.8b
    temperature: 0.3
    max_tokens: 2048
```

### 3.2 模型接口抽象

```python
class LLMProvider(Protocol):
    async def chat(self, messages: list[dict], **kwargs) -> dict: ...
    async def chat_with_tools(self, messages: list[dict], tools: list[dict], **kwargs) -> dict: ...
    async def embed(self, texts: list[str]) -> list[list[float]]: ...

class VLLMProvider(LLMProvider): ...
class OllamaProvider(LLMProvider): ...
class OpenAICompatibleProvider(LLMProvider): ...
```

### 3.3 降级策略

```text
主模型可用 → 使用主模型
主模型超时 → 使用备选模型
全部不可用 → 返回结构化降级响应，不阻塞平台
```

降级响应：
```json
{
  "status": "unavailable",
  "summary": "AI 分析服务暂时不可用",
  "recommendation": "请人工分析或稍后重试"
}
```

模型不可用时：告警、采集、策略、自动化不中断。

---

## 4. Context Builder（上下文构建器）

### 4.1 上下文收集

```python
class AIContextBuilder:
    async def build_incident_context(self, alert_id: str) -> dict:
        """构建故障分析上下文"""
        context = {}
        context["alert"] = await self._get_alert(alert_id)
        context["assets"] = await self._get_related_assets(alert)
        context["states"] = await self._get_current_states(asset_ids)
        context["metrics"] = await self._get_recent_metrics(asset_ids)
        context["events"] = await self._get_related_events(alert)
        context["logs"] = await self._get_related_logs(asset_ids)
        context["config_changes"] = await self._get_recent_config_changes(asset_ids)
        context["executions"] = await self._get_recent_executions(asset_ids)
        context["tickets"] = await self._get_related_tickets(alert)
        context["knowledge"] = await self._search_similar_knowledge(alert)
        context["policies"] = await self._get_applicable_policies(alert)
        return context
```

### 4.2 上下文结构

```json
{
  "incident": {
    "alert_id": "xxx",
    "title": "Linux 磁盘空间异常",
    "severity": "warning",
    "fired_at": "2026-01-01T00:00:00"
  },
  "affected_assets": [
    {
      "id": "asset-001",
      "name": "web-server-01",
      "type": "linux_server",
      "ip": "192.168.1.10",
      "health_status": "warning"
    }
  ],
  "current_states": [
    {"type": "disk", "status": "warning", "value": {"usage_pct": 92, "mount": "/"}}
  ],
  "metrics_trend": {
    "disk_usage": {"current": 92, "trend": "increasing", "history_24h": [...]}
  },
  "related_events": [...],
  "related_logs": [...],
  "recent_config_changes": [],
  "recent_executions": [],
  "similar_knowledge": [
    {"id": "kb-linux-disk-high", "title": "Linux 磁盘空间异常处置", "similarity": 0.95}
  ],
  "applicable_policies": [
    {"id": "policy-001", "name": "磁盘空间异常自动清理"}
  ],
  "risk_boundary": {
    "user_permissions": ["automation:execute", "automation:dry_run"],
    "max_risk_allowed": "medium"
  }
}
```

### 4.3 上下文窗口管理

- 总上下文限制在模型 max_tokens 内
- 日志和指标只保留最近相关数据
- 优先级：告警详情 > 资产状态 > 指标趋势 > 日志 > 事件
- 超出时截断低优先级内容

---

## 5. Prompt 模板管理

### 5.1 模板存储

Prompt 模板存储在数据库或配置文件中，不硬编码。

```yaml
templates:
  incident_root_cause:
    system: |
      你是 AUTOPS 运维平台的 AI 分析助手。
      你的任务是基于提供的故障上下文，分析根因并推荐处置方案。
      
      规则：
      1. 必须基于提供的事实数据进行分析
      2. 不确定的信息必须标注
      3. 推荐动作必须标注风险等级
      4. 高风险动作必须标注需要审批
      5. 输出必须严格遵循 JSON 格式
      
    user: |
      请分析以下故障：
      
      ## 告警信息
      {{alert}}
      
      ## 受影响资产
      {{assets}}
      
      ## 当前状态
      {{states}}
      
      ## 相关日志
      {{logs}}
      
      ## 相似案例
      {{knowledge}}
      
      请按以下 JSON 格式输出分析结果：
      {{output_schema}}
```

### 5.2 输出格式

```json
{
  "summary": "故障摘要",
  "impact": "影响范围描述",
  "probable_causes": [
    {
      "cause": "可能原因描述",
      "confidence": 0.82,
      "evidence": ["证据1", "证据2"]
    }
  ],
  "recommended_actions": [
    {
      "action": "建议动作描述",
      "risk": "low",
      "requires_approval": false,
      "related_playbook": "playbook-id-or-null",
      "estimated_impact": "预期效果"
    }
  ],
  "verification_plan": [
    "验证步骤1",
    "验证步骤2"
  ],
  "uncertainties": [
    "不确定信息1"
  ]
}
```

---

## 6. Tool Calling（工具调用）

### 6.1 工具白名单

| 工具名 | 类型 | 说明 |
|---|---|---|
| query_asset | 只读 | 查询资产信息 |
| query_state | 只读 | 查询资产状态 |
| query_metrics | 只读 | 查询指标趋势 |
| query_alerts | 只读 | 查询告警信息 |
| query_events | 只读 | 查询事件列表 |
| query_logs | 只读 | 查询日志（自动脱敏） |
| query_tickets | 只读 | 查询工单信息 |
| query_knowledge | 只读 | 搜索知识库 |
| query_config | 只读 | 查询配置（脱敏） |
| query_execution_history | 只读 | 查询执行历史 |

### 6.2 工具调用约束

- 所有工具只读，不可写
- 每次调用有超时限制（默认 10 秒）
- 单次分析最多调用 20 次工具
- 工具调用结果自动脱敏
- 每次调用记录审计日志

### 6.3 工具调用流程

```text
AI 请求工具调用
  ↓
Tool Guard 检查（白名单？）
  ↓
权限检查（用户有权限？）
  ↓
参数验证
  ↓
执行工具调用
  ↓
结果脱敏
  ↓
返回给 AI
  ↓
记录审计日志
```

---

## 7. Agentic Workflow 阶段

### 阶段一：结构化分析（M2 实现）

AI 接收上下文，输出结构化分析结果，不做工具调用。

```text
告警触发 → Context Builder → LLM 分析 → 结构化 JSON → 展示给用户
```

### 阶段二：只读工具调用（M5 实现）

AI 可以调用白名单中的只读工具获取额外信息。

```text
告警触发 → 初始上下文 → LLM 分析 → 需要更多信息？
  ↓ 是
工具调用 → 获取额外信息 → 继续分析 → 结构化 JSON
```

### 阶段三：执行计划生成（M5 实现）

AI 生成执行计划，但必须经过策略中心校验。

```text
AI 推荐动作 → 策略匹配 → 策略校验 → 审批（如需）→ 执行
```

### 阶段四：Human-in-the-loop（M5 实现）

高风险动作必须人工确认。

```text
AI 推荐 → 策略校验 → 风险评估
  ↓ 低风险 → 自动执行（策略允许时）
  ↓ 高风险 → 生成审批请求 → 人工审批 → 执行
```

---

## 8. 知识库 RAG

### 8.1 知识向量化

- 标准知识库导入时自动向量化
- 向量存储在 Qdrant/Chroma
- 索引包含：标题、内容、触发条件、资产类型、标签

### 8.2 检索流程

```text
分析请求 → 提取查询向量 → 向量检索 Top-K
  → 相关度过滤（threshold > 0.7）
  → 返回相似知识条目
```

### 8.3 知识反馈循环

```text
AI 分析 → 用户反馈（helpful/unhelpful）
  → 知识条目评分更新
  → 反馈用于优化检索排序
```

---

## 9. 模型配置变更影响

| 变更 | 影响 | 要求 |
|---|---|---|
| 更换模型 | 只改配置，不改代码 | 配置化 |
| 调整温度 | 影响输出确定性 | 场景级别配置 |
| 调整 max_tokens | 影响输出长度 | 场景级别配置 |
| 模型不可用 | 平台降级 | AI 分析显示不可用，不阻塞 |
| 新增场景模型 | 新增配置项 | 场景级别配置 |
