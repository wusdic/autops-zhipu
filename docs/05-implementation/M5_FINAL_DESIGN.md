# AUTOPS M5-AI对接 + 国产化 + 前端适配 设计文档

> 前置：M3闭环+M5基础框架已完成（Agent/ToolGuard/通知/Edge）
> 目标：打通AI Agent→真实LLM调用链、国产化数据库适配层、前端M3/M5新功能页面

---

## 一、差距诊断

### 1.1 AI Agent → 真实LLM

| 项目 | 现状 | 目标 |
|------|------|------|
| ReActAgent._call_llm | 硬编码降级模式 | 调用AIOpsService已有的OpenAI兼容接口 |
| Agent入口API | 无 | POST /api/v1/aiops/agent/run |
| Agent历史记录 | 无 | 存储到ai_analyses表 |
| AiOpsPage | 仅做单次分析(1090行) | 增加Agent交互面板(思考过程+工具调用) |

**关键发现**：AIOpsService._call_llm已实现完整的OpenAI兼容调用(httpx→base_url/chat/completions)。
Agent只需复用此模式，不需要重新实现HTTP调用。

### 1.2 国产化数据库适配

| 项目 | 现状 | 目标 |
|------|------|------|
| 数据库连接 | MySQL硬编码(aiomysql) | dialect映射层 |
| 配置 | database.yaml仅mysql | 增加dialect字段 |
| 兼容范围 | MySQL only | 达梦/OpenGauss/TiDB/OceanBase |

### 1.3 前端M3/M5适配

| 项目 | 现状 | 目标 |
|------|------|------|
| routes.ts | 无Edge/证据链/工单转知识/Agent常量 | 新增7个路由常量 |
| AlertDetailPage | 无证据链Tab | 增加证据链时间线面板 |
| TicketDetailPage | 无转知识按钮 | 增加转知识草稿功能 |
| AiOpsPage | 单次分析(1090行) | 增加Agent交互模式 |
| CollectorPage | 仅内置采集器 | 增加Edge Collector管理Tab |
| IncidentResponsePage | 无策略命中信息 | 增加策略匹配展示 |

---

## 二、设计

### 2.1 AI Agent 对接 LLM

#### 2.1.1 LLMClient抽象

```python
# app/domains/aiops/agent/llm_client.py
class LLMClient:
    """OpenAI兼容LLM客户端，复用AIOpsService的配置."""
    
    def __init__(self):
        self.config = get_config()  # 复用全局配置
        self.base_url = self.config.llm_base_url
        self.model = self.config.llm_model_name
        self.api_key = self.config.llm_api_key
        self.timeout = self.config.llm_timeout
    
    async def chat(self, messages: list[dict]) -> str:
        """调用LLM，返回文本响应."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 2048,
                },
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key != "EMPTY" else {}
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            raise Exception(f"LLM error: {resp.status_code}")
    
    async def is_available(self) -> bool:
        """检查LLM是否可用."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url.replace('/v1','')}/v1/models")
                return resp.status_code == 200
        except Exception:
            return False
```

#### 2.1.2 Agent API端点

```
POST /api/v1/aiops/agent/run
Body: { task: string, alert_id?: string, context?: dict }
Response: { agent_result_id, answer, steps, pending_approval }

GET /api/v1/aiops/agent/results
Query: page, page_size
Response: { items: AgentResult[], total }

POST /api/v1/aiops/agent/{id}/approve
Body: { approved: bool, reason?: string }
Response: { status }
```

#### 2.1.3 ReActAgent改造

- 删除硬编码降级模式
- 注入LLMClient实例
- Agent结果持久化到ai_analyses表(analysis_type="agent")
- 工具调用审计记录到audit_logs

### 2.2 国产化数据库适配

#### 2.2.1 方案

创建`app/infra/db_dialect.py`方言映射模块：

| 配置dialect | 驱动 | 连接串模板 | 特殊处理 |
|------------|------|-----------|---------|
| mysql(默认) | aiomysql | mysql+aiomysql://... | 无 |
| dm(达梦) | dmPython | dm+dmPython://... | 分页改ROWNUM |
| opengauss | asyncpg | postgresql+asyncpg://... | SERIAL→AUTO_INCREMENT |
| tidb | aiomysql | mysql+aiomysql://... | 兼容MySQL协议 |
| oceanbase | aiomysql | mysql+aiomysql://... | 兼容MySQL协议 |

TiDB和OceanBase兼容MySQL协议，不需要额外适配。实际只需：
1. 配置文件增加dialect字段
2. database.py根据dialect构建连接串
3. 分页函数按dialect选择LIMIT/OFFSET或ROWNUM

#### 2.2.2 database.yaml新格式

```yaml
database:
  dialect: mysql          # mysql | dm | opengauss | tidb | oceanbase
  host: 127.0.0.1
  port: 3306
  name: autops
  user: autops
  pass_key: db_pass
  pool_size: 10
  echo: false
```

#### 2.2.3 实现范围

- `app/infra/db_dialect.py`: DialectAdapter类(100行)
- `app/infra/database.py`: 创建引擎时使用adapter
- `app/infra/config.py`: 解析dialect字段
- 配置文件更新

### 2.3 前端适配

#### 2.3.1 routes.ts 新增

```typescript
// 证据链
ALERT_EVIDENCE_CHAIN: (id: string) => `/api/v1/alerts/${id}/evidence-chain`,
// 工单转知识
TICKET_CONVERT_KNOWLEDGE: (id: string) => `/api/v1/tickets/${id}/convert-knowledge`,
// Edge Collector
EDGE_REGISTER: '/api/v1/collectors/edge/register',
EDGE_HEARTBEAT: '/api/v1/collectors/edge/heartbeat',
EDGE_STATUS: (id: string) => `/api/v1/collectors/edge/${id}/status`,
EDGE_TASKS: (id: string) => `/api/v1/collectors/edge/${id}/tasks`,
// Agent
AIOPS_AGENT_RUN: '/api/v1/aiops/agent/run',
AIOPS_AGENT_RESULTS: '/api/v1/aiops/agent/results',
AIOPS_AGENT_APPROVE: (id: string) => `/api/v1/aiops/agent/${id}/approve`,
```

#### 2.3.2 页面改造计划

| 页面 | 改动 | 新增行数估计 |
|------|------|-------------|
| AlertDetailPage.vue | 增加证据链Tab | +120 |
| TicketDetailPage.vue | 增加转知识按钮+对话框 | +80 |
| AiOpsPage.vue | 增加Agent模式面板 | +200 |
| CollectorPage.vue | 增加Edge Tab | +150 |
| IncidentResponsePage.vue | 增加策略命中面板 | +100 |

**设计原则**：在现有页面增加Tab/Section，不新建页面。

#### 2.3.3 AiOpsPage Agent模式设计

```
┌─────────────────────────────────────────┐
│ [分析模式] [Agent模式]    ← Tab切换     │
├─────────────────────────────────────────┤
│ Agent模式:                               │
│ ┌───────────────────────────────────┐   │
│ │ 输入任务描述或选择告警             │   │
│ │ [文本框]                          │   │
│ │ [运行Agent]                       │   │
│ └───────────────────────────────────┘   │
│                                         │
│ Agent思考过程:                           │
│ ┌─ Thought ─────────────────────────┐   │
│ │ 💭 分析告警：磁盘空间不足...       │   │
│ ├─ Action ──────────────────────────┤   │
│ │ 🔧 check_asset_status(asset_id)  │   │
│ ├─ Observation ─────────────────────┤   │
│ │ 📋 资产状态: disk_usage=92%       │   │
│ ├─ Thought ─────────────────────────┤   │
│ │ 💭 需要查询知识库...              │   │
│ ├─ Action ──────────────────────────┤   │
│ │ 🔧 query_knowledge("磁盘清理")   │   │
│ └───────────────────────────────────┘   │
│                                         │
│ 最终结论:                               │
│ ┌─ Final Answer ───────────────────┐   │
│ │ ✅ 根因：日志增长导致磁盘空间不足  │   │
│ │ 建议执行磁盘清理脚本(risk:low)     │   │
│ │ [执行] [转工单] [忽略]            │   │
│ └───────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## 三、实施优先级

| # | 任务 | 优先级 | 工作量 |
|---|------|--------|--------|
| 1 | LLMClient + Agent对接 | P0 | 后端3个文件 |
| 2 | Agent API端点 | P0 | 后端1个文件 |
| 3 | 国产化Dialect层 | P1 | 后端2个文件 |
| 4 | routes.ts更新 | P0 | 前端1个文件 |
| 5 | AiOpsPage Agent模式 | P0 | 前端1个文件 |
| 6 | AlertDetailPage证据链 | P1 | 前端1个文件 |
| 7 | TicketDetailPage转知识 | P1 | 前端1个文件 |
| 8 | CollectorPage Edge Tab | P2 | 前端1个文件 |
| 9 | IncidentResponsePage策略 | P2 | 前端1个文件 |

总计：后端~6文件 ~600行，前端~6文件 ~650行
