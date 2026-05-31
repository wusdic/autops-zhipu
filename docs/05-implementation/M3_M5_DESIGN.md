# AUTOPS M3 标准场景闭环 + M5 增强阶段 设计文档

> 文档定位：基于差距诊断结果，设计M3/M5的精确实现方案
> 前置条件：M0-M2已完成，事件系统+WebSocket+209 UT已就位
> 设计原则：先设计后编码，设计即契约

---

## 一、差距诊断总结

### M3 当前完成度：≈55%
- ✅ 框架搭好（模型/API/前端页面/种子数据）
- ❌ 内容为占位符（知识库/脚本/Playbook/策略条件）
- ❌ 闭环未串联（Alert→Policy→Execution 自动链路）
- ❌ 去重/关联引擎未实现

### M5 当前完成度：≈20%
- ❌ AI Agent 框架（0%）
- ❌ Tool Calling + Tool Guard（0%）
- ❌ Edge Collector 远程架构（0%）
- ❌ 外部通知渠道（0%）
- ❌ 国产化数据库适配（0%）
- ✅ 审批流程基础（70%）

---

## 二、M3 设计

### M3.1 标准知识库内容填充

**目标**：8个标准场景的知识库文章从占位符变为真实可执行的诊断/修复方案。

**涉及文件**：
- `backend/app/domains/knowledge/service.py` — 新增 `import_standard_scenarios()` 方法
- `scripts/data_seed/standard_knowledge_seed.py` — 新种子脚本

**8个标准场景数据设计**：

#### 场景1：Linux磁盘空间异常
```yaml
title: Linux 磁盘空间异常处置
article_type: standard
asset_types: ["linux_server"]
trigger_events: ["disk_usage_high", "state_change"]
diagnosis_steps:
  - name: 检查磁盘使用率
    command: "df -h"
    expected: "使用率 > 85%"
  - name: 定位大文件
    command: "du -sh /* 2>/dev/null | sort -rh | head -20"
    expected: "识别占用最大的目录"
  - name: 检查日志增长
    command: "find /var/log -name '*.log' -size +100M -exec ls -lh {} \\;"
    expected: "发现异常增长的日志文件"
  - name: 检查已删除但未释放的文件
    command: "lsof +L1 2>/dev/null | head -20"
    expected: "发现已删除但进程仍占用的文件"
action_steps:
  - name: 压缩旧日志
    command: "find /var/log -name '*.log' -mtime +7 -exec gzip {} \\;"
    risk: low
  - name: 清理临时文件
    command: "find /tmp -type f -mtime +3 -delete 2>/dev/null"
    risk: low
  - name: 清理包管理器缓存
    command: "apt-get clean || yum clean all"
    risk: low
  - name: 通知人工处理（如需扩容）
    command: "N/A - 创建工单"
    risk: none
verification_steps:
  - name: 验证磁盘使用率
    command: "df -h"
    expected: "使用率 < 80%"
risk_level: low
requires_approval: false
```

#### 场景2：Windows服务未运行
```yaml
title: Windows 服务未运行处置
asset_types: ["windows_server"]
trigger_events: ["service_down", "state_change"]
diagnosis_steps:
  - name: 检查服务状态
    command: "Get-Service -Name {service_name} | Select-Object Status,Name,DisplayName"
  - name: 检查服务依赖
    command: "Get-Service -Name {service_name} -DependentServices"
  - name: 检查系统事件日志
    command: "Get-EventLog -LogName System -Source 'Service Control Manager' -Newest 10"
action_steps:
  - name: 尝试启动服务
    command: "Start-Service -Name {service_name}"
    risk: medium
  - name: 如启动失败，检查服务配置
    command: "sc.exe qc {service_name}"
    risk: low
verification_steps:
  - name: 确认服务运行
    command: "Get-Service -Name {service_name}"
    expected: "Status=Running"
risk_level: medium
requires_approval: false
```

#### 场景3：Web端口不可达
```yaml
title: Web 端口不可达处置
asset_types: ["web_server", "linux_server", "windows_server"]
trigger_events: ["port_unreachable", "state_change"]
diagnosis_steps:
  - name: 本地端口检查
    command: "ss -tlnp | grep :{port} || netstat -tlnp | grep :{port}"
  - name: 检查进程
    command: "ps aux | grep {process_name}"
  - name: 检查防火墙规则
    command: "iptables -L -n | grep {port} || firewall-cmd --list-ports"
action_steps:
  - name: 尝试重启服务
    command: "systemctl restart {service_name}"
    risk: medium
  - name: 检查配置文件语法
    command: "{service_name} -t"
    risk: low
verification_steps:
  - name: 端口可达性测试
    command: "curl -s -o /dev/null -w '%{http_code}' http://localhost:{port}"
    expected: "HTTP 200-399"
risk_level: medium
requires_approval: true
```

#### 场景4：数据库连接数过高
#### 场景5：数据库连接失败
#### 场景6：SSL证书即将过期
#### 场景7：采集器离线
#### 场景8：自动化执行失败

（详细数据在种子脚本中定义，此处省略重复格式）

### M3.2 Alert→Policy→Execution 自动闭环

**核心链路**：
```
状态变化 → 事件生成 → 告警触发
    → 策略匹配(alert_created事件)
    → 自动化执行创建
    → 结果验证 → 知识沉淀
```

**涉及文件**：
- `backend/app/common/event_handlers.py` — 补充 `on_alert_created_match_policy` 处理器
- `backend/app/domains/alert/handlers.py` — 发布 `alert.created` 事件
- `backend/app/domains/policy/service.py` — 新增 `match_and_execute(alert)` 方法
- `backend/app/domains/policy/handlers.py` — 订阅 `alert.created` 事件

**设计**：

```python
# common/event_handlers.py 中新增
async def on_alert_created_match_policy(event: DomainEvent):
    """告警创建后自动匹配策略并执行"""
    policy_svc = PolicyService(db_session)
    match = await policy_svc.match_alert(event.data)
    if match:
        if match.requires_approval:
            # 创建待审批的执行
            exec_id = await policy_svc.create_pending_execution(match)
            await bus.publish(DomainEvent(
                type="policy.approval_required",
                data={"policy_execution_id": match.id, "execution_id": exec_id}
            ))
        else:
            # 直接执行
            exec_id = await policy_svc.execute_immediately(match)
            await bus.publish(DomainEvent(
                type="policy.execution_started",
                data={"execution_id": exec_id}
            ))

# 注册
bus.subscribe("alert.created", on_alert_created_match_policy)
```

**策略匹配算法**：
```python
async def match_alert(self, alert_data: dict) -> PolicyExecution | None:
    """根据告警数据匹配最佳策略"""
    alert_type = alert_data.get("event_type", "")
    asset_ids = alert_data.get("asset_ids", [])
    severity = alert_data.get("severity", "info")

    # 查找所有启用的策略
    policies = await self._get_enabled_policies()

    matches = []
    for policy in policies:
        condition = policy.trigger_condition  # JSON
        if self._evaluate_condition(condition, alert_type, severity):
            matches.append(policy)

    if not matches:
        return None

    # 选择最高优先级（risk_level排序）
    best = sorted(matches, key=lambda p: RISK_ORDER[p.risk_level])[0]
    return await self._create_policy_execution(best, alert_data)
```

### M3.3 事件去重引擎

**设计**：
```python
# domains/event/service.py 中修改 create_event
async def create_event(self, data: EventCreate) -> Event:
    # 1. 生成指纹
    fingerprint = self._generate_fingerprint(data)

    # 2. 查重：相同指纹 + 5分钟内
    existing = await self._find_duplicate(fingerprint, minutes=5)
    if existing:
        existing.is_deduplicated = True
        await self.session.flush()
        return existing

    # 3. 创建新事件
    event = Event(id=str(uuid4()), fingerprint=fingerprint, **data.model_dump())
    self.session.add(event)
    await self.session.flush()
    return event

def _generate_fingerprint(self, data) -> str:
    """基于 event_type + source + asset_id + title 生成MD5"""
    key = f"{data.event_type}|{data.source}|{data.asset_id or ''}|{data.title}"
    return hashlib.md5(key.encode()).hexdigest()
```

### M3.4 策略条件修正 + 命中解释

**修正种子数据**：每个策略的 `trigger_condition` 对应实际场景：
```python
POLICY_CONDITIONS = {
    "Auto Disk Cleanup": {
        "event_type": "disk_usage_high",
        "severity": ["warning", "critical"],
        "asset_types": ["linux_server"]
    },
    "Auto Service Restart": {
        "event_type": "service_down",
        "severity": ["critical"],
        "asset_types": ["windows_server"]
    },
    # ...
}
```

**命中解释**：`simulate` API 返回增加 `explanation` 字段：
```json
{
    "trigger_matched": true,
    "explanation": "告警类型 'disk_usage_high' 匹配策略触发条件，资产类型 'linux_server' 在策略适用范围内，严重级别 'warning' >= 最低阈值",
    "matched_condition": {"field": "event_type", "expected": "disk_usage_high", "actual": "disk_usage_high"},
    "risk_level": "low",
    "action_chain": [...],
    "affected_assets": [...]
}
```

### M3.5 工单→知识沉淀 API

**新增端点**：
```
POST /api/v1/tickets/{ticket_id}/convert-knowledge
Response: { code: 0, data: { article_id: "...", title: "...", status: "draft" } }
```

**实现**：
```python
# domains/ticket/api.py 新增
@router.post("/{ticket_id}/convert-knowledge")
async def convert_to_knowledge(ticket_id: str, db: AsyncSession = Depends(get_db)):
    ticket_svc = TicketService(db)
    draft = await ticket_svc.convert_to_knowledge_draft(ticket_id)

    # 创建知识文章
    knowledge_svc = KnowledgeService(db)
    article = await knowledge_svc.create(KnowledgeCreate(
        title=draft["title"],
        article_type="runbook",
        content=draft["content"],
        source="ticket",
        source_id=ticket_id,
        status="draft",
        tags=draft.get("tags", [])
    ))
    return success({"article_id": article.id, "title": article.title, "status": "draft"})
```

### M3.6 故障处置证据链 API

**新增端点**：
```
GET /api/v1/alerts/{alert_id}/evidence-chain
Response: {
    alert: {...},
    timeline: [
        { time: "T+0s", type: "event", data: {...} },
        { time: "T+2s", type: "alert", data: {...} },
        { time: "T+5s", type: "ai_analysis", data: {...} },
        { time: "T+10s", type: "policy_matched", data: {...} },
        { time: "T+15s", type: "execution", data: {...} },
    ],
    related_events: [...],
    related_executions: [...],
    related_ticket: {...}
}
```

---

## 三、M5 设计

### M5.1 AI Agent 框架

**架构设计**：
```
┌─────────────────────────────────────────┐
│           AI Agent Framework            │
├─────────────────────────────────────────┤
│  AgentBase (抽象基类)                    │
│  ├─ ReActAgent (推理-行动循环)           │
│  └─ PlanExecuteAgent (规划-执行)         │
├─────────────────────────────────────────┤
│  ToolRegistry (工具注册中心)             │
│  ├─ 读取工具 (read_only)                │
│  │   ├─ check_asset_status             │
│  │   ├─ query_logs                     │
│  │   ├─ query_alerts                   │
│  │   ├─ query_knowledge                │
│  │   └─ query_metrics                  │
│  └─ 执行工具 (requires_approval)        │
│      ├─ execute_script                  │
│      ├─ restart_service                 │
│      └─ create_ticket                   │
├─────────────────────────────────────────┤
│  ToolGuard (安全边界)                    │
│  ├─ 只读工具：直接放行                   │
│  ├─ 低风险：自动执行                     │
│  ├─ 中风险：需确认 → Human-in-the-loop   │
│  └─ 高风险：必须审批 + 禁止自动          │
├─────────────────────────────────────────┤
│  ContextBuilder (上下文构建)             │
│  └─ 按需加载：资产→告警→日志→知识→拓扑   │
└─────────────────────────────────────────┘
```

**文件结构**：
```
backend/app/domains/aiops/
├── agent/
│   ├── __init__.py
│   ├── base.py          # AgentBase 抽象类
│   ├── react.py         # ReAct 推理循环
│   ├── context.py       # ContextBuilder
│   └── executor.py      # Agent 执行管理器
├── tools/
│   ├── __init__.py
│   ├── registry.py      # ToolRegistry 工具注册中心
│   ├── guard.py         # ToolGuard 安全边界
│   ├── readonly.py      # 只读工具集
│   └── execution.py     # 执行工具集
├── models.py            # (已有)
├── schemas.py           # 扩展
├── service.py           # 扩展
└── api.py               # 扩展
```

**ReAct Agent 核心循环**：
```python
class ReActAgent:
    """推理-行动循环 Agent"""
    MAX_ITERATIONS = 10

    async def run(self, task: str, context: dict) -> AgentResult:
        messages = [SystemPrompt, UserPrompt(task, context)]

        for i in range(self.MAX_ITERATIONS):
            response = await self.llm.chat(messages)

            # 解析 Thought / Action / Final Answer
            parsed = self._parse_response(response)

            if parsed.type == "final_answer":
                return AgentResult(answer=parsed.content, steps=i+1)

            if parsed.type == "action":
                # ToolGuard 检查
                guard_result = self.tool_guard.evaluate(parsed.tool, parsed.args)
                if guard_result.needs_approval:
                    return AgentResult(
                        answer="需要人工审批",
                        pending_approval=guard_result,
                        steps=i+1
                    )

                # 执行工具
                tool_result = await self.registry.execute(parsed.tool, parsed.args)
                messages.append(ToolResultMessage(tool_result))

        return AgentResult(answer="达到最大迭代次数", steps=self.MAX_ITERATIONS)
```

**API 端点设计**：
```
POST /api/v1/aiops/agent/start
  Body: { task: "分析告警 xxx", alert_id: "...", max_iterations: 10 }
  Response: { session_id: "...", status: "running" }

GET /api/v1/aiops/agent/{session_id}
  Response: { status, steps: [...], current_action, final_answer }

POST /api/v1/aiops/agent/{session_id}/approve
  Body: { approved: true, comment: "同意" }
  Response: { status: "resumed" }

GET /api/v1/aiops/tools
  Response: { tools: [{ name, description, parameters, risk_level }] }
```

### M5.2 外部通知渠道

**文件结构**：
```
backend/app/integrations/
├── __init__.py
├── base.py           # NotificationChannel 抽象基类
├── webhook.py        # Webhook 通知
├── dingtalk.py       # 钉钉通知
├── email.py          # 邮件通知 (SMTP)
└── registry.py       # 通知渠道注册中心
```

**设计**：
```python
class NotificationChannel(ABC):
    @abstractmethod
    async def send(self, notification: NotificationPayload) -> bool:
        ...

class WebhookChannel(NotificationChannel):
    """通用 Webhook 通知"""
    def __init__(self, url: str, secret: str | None = None):
        self.url = url
        self.secret = secret

    async def send(self, payload) -> bool:
        headers = {"Content-Type": "application/json"}
        if self.secret:
            sign = hmac_sha256(self.secret, json.dumps(payload.data))
            headers["X-Signature"] = sign
        async with httpx.AsyncClient() as client:
            r = await client.post(self.url, json=payload.data, headers=headers)
            return r.status_code == 200

class DingTalkChannel(NotificationChannel):
    """钉钉机器人 Webhook"""
    ...

class EmailChannel(NotificationChannel):
    """SMTP 邮件"""
    ...
```

**配置**（在 `configs/policies.yaml` 中新增）：
```yaml
notification_channels:
  webhook:
    enabled: false
    url: ""
    secret: ""
  dingtalk:
    enabled: false
    webhook_url: ""
    secret: ""
    at_mobiles: []
  email:
    enabled: false
    smtp_host: ""
    smtp_port: 587
    smtp_user: ""
    smtp_password: ""
    from_addr: ""
    to_addrs: []
```

**事件联动**：
```python
# 在 event_handlers.py 中
async def on_alert_created_notify_external(event):
    """告警创建后发送外部通知"""
    severity = event.data.get("severity", "info")
    if severity in ["critical", "warning"]:
        channel_registry = get_notification_registry()
        await channel_registry.broadcast(NotificationPayload(
            title=event.data.get("title"),
            severity=severity,
            alert_id=event.data.get("alert_id"),
            asset_name=event.data.get("asset_name", ""),
        ))
```

### M5.3 Edge Collector 远程架构

**架构**：
```
┌──────────────┐     WebSocket/HTTP     ┌──────────────┐
│  AUTOPS 主站  │◄──────────────────────►│ Edge Collector│
│  (后端8001)   │    心跳 + 任务 + 结果    │  (远程采集器)  │
└──────────────┘                        └──────────────┘
```

**文件结构**：
```
backend/app/domains/collector/
├── edge/               # 新增
│   ├── __init__.py
│   ├── manager.py      # EdgeCollectorManager
│   ├── protocol.py     # 通信协议定义
│   └── tasks.py        # 任务分发引擎
```

**协议设计**：
```json
// 心跳
{ "type": "heartbeat", "collector_id": "xxx", "status": "healthy", "metrics": {...} }

// 任务下发
{ "type": "task", "task_id": "xxx", "collector_type": "ssh", "config": {...} }

// 结果上报
{ "type": "result", "task_id": "xxx", "status": "success", "data": {...} }
```

**API**：
```
POST /api/v1/collectors/edge/register      # 采集器注册
POST /api/v1/collectors/edge/heartbeat      # 心跳上报
GET  /api/v1/collectors/edge/{id}/tasks      # 获取待执行任务
POST /api/v1/collectors/edge/{id}/results    # 上报结果
```

### M5.4 国产化数据库适配

**设计**：在 `infra/database.py` 中增加方言映射层：
```python
DIALECT_MAP = {
    "mysql": "mysql+aiomysql",
    "mariadb": "mysql+aiomysql",
    # 国产化
    "dm": "dm+dmPython",           # 达梦
    "opengauss": "opengauss+asyncpg",  # OpenGauss
    "oceanbase": "mysql+aiomysql",  # OceanBase (MySQL兼容)
    "tidb": "mysql+aiomysql",      # TiDB (MySQL兼容)
}
```

当前阶段仅做配置抽象层，不做实际驱动集成（需要对应数据库环境验证）。

---

## 四、实施优先级与计划

### Phase 1：M3 内容填充（预计编码量：~2000行）
1. 标准知识库种子脚本（8个场景真实内容）
2. 策略 trigger_condition 修正
3. 脚本库 + Playbook 内容填充
4. Alert→Policy→Execution 自动闭环处理器
5. 事件去重引擎
6. 工单→知识 API 端点
7. 故障处置证据链 API

### Phase 2：M5 Agent + 集成（预计编码量：~3000行）
1. AI Agent 框架（ToolRegistry + ReAct + ToolGuard）
2. 外部通知渠道（Webhook + 钉钉 + 邮件）
3. Edge Collector 协议和任务分发
4. 审批队列前端页面

### Phase 3：验证
1. 8个标准场景端到端验证
2. Agent 工具调用安全测试
3. 通知渠道连通测试
4. 更新差距报告

---

## 五、关键设计决策（ADR）

### ADR-001：Agent 推理模式选择
- **决策**：采用 ReAct（Reasoning + Acting）模式
- **原因**：AIOps场景需要逐步诊断+验证，ReAct 的 Thought→Action→Observation 循环天然匹配
- **备选**：Plan-Execute（适合复杂编排，但调试困难）
- **影响**：Agent 每步都可观测，Human-in-the-loop 天然支持

### ADR-002：ToolGuard 安全分级
- **只读工具**：直接放行（查询资产/日志/告警/知识）
- **低风险执行**：自动执行（日志清理/缓存清理）
- **中风险执行**：需确认（服务重启/配置变更）
- **高风险执行**：必须人工审批（数据库操作/系统重启/批量变更）
- **禁止**：高危命令（rm -rf /, mkfs, dd, format）

### ADR-003：Edge Collector 通信协议
- **决策**：HTTP REST + WebSocket 混合
- **原因**：REST 用于注册/心跳/结果上报（简单可靠），WebSocket 用于实时任务推送（低延迟）
- **备选**：纯 gRPC（性能更好但部署复杂）
- **影响**：边缘采集器无需特殊依赖，标准HTTP客户端即可
