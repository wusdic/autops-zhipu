# AUTOPS 平台目标架构与规划方案（最终版）

> 项目名称：autops  
> 文档状态：current  
> 是否为事实源：yes  
> 建议路径：`docs/01-architecture/AUTOPS_TARGET_ARCHITECTURE.md`  
> 文档定位：本文件定义 AUTOPS 的产品目标、总体架构、领域模型、数据架构、前后端架构、安全架构、AIops 架构、部署架构和长期演进方向。  
> 重要说明：本项目从空仓库起步，所有设计以目标架构为准。

---

## 1. 产品定位

AUTOPS 是一个面向私有化部署场景的自治运维操作系统。

它的目标不是简单提供资产管理、监控、告警、工单、脚本和 AI 问答，而是将这些能力统一到一个完整闭环中：

```text
资源发现 → 资产纳管 → 配置治理 → 状态采集 → 事件识别 → 告警收敛
→ 影响分析 → AI 诊断 → 策略决策 → 自动化执行 → 实时日志
→ 结果验证 → 回滚/升级/关闭 → 知识沉淀 → 策略优化
```

平台核心价值：

1. 自动发现和纳管 IT 资源。
2. 实时感知设备、服务、应用、数据库、中间件和平台自身状态。
3. 统一管理采集配置、凭证、阈值、策略、脚本、通知和 AI 模板。
4. 自动识别事件和异常。
5. 自动收敛告警并判断影响范围。
6. 基于多源证据进行 AI 根因分析。
7. 根据策略安全执行自动化动作。
8. 实时回传执行日志并验证结果。
9. 失败时回滚或升级工单。
10. 把处理经验沉淀为知识和可复用策略。

---

## 2. 设计思想

### 2.1 模型驱动

AUTOPS 底层由九类统一模型驱动：

1. 统一资源模型。
2. 统一配置模型。
3. 统一状态模型。
4. 统一事件模型。
5. 统一告警模型。
6. 统一策略模型。
7. 统一执行模型。
8. 统一日志与审计模型。
9. 统一知识模型。

任何功能都必须归入这些模型之一。不能归入统一模型的功能，不进入主干。

### 2.2 平台不是围绕 MVP 开发

平台开发必须按完整宏观规划建设。MVP 只是用来验证架构闭环，不是设计中心。

所有验证场景都必须通过通用能力完成，包括资产、配置、采集、事件、告警、策略、自动化、日志、AI 和知识库，不能为某个场景单独写旁路代码。

### 2.3 长期演进能力

所有核心能力必须支持版本管理、审计、权限、扩展、配置化、私有化部署、离线部署、国产化迁移、可观测和自动化测试。

---

## 3. 总体逻辑架构

```text
[展现层]
  Web Console / 运维指挥台 / 资产与配置台 / 监控与事件台
  故障处置台 / 自动化编排台 / AI 与知识台 / 平台管理台

[接入层]
  API Gateway / JWT / OAuth2 / OIDC / RBAC / ABAC
  WebSocket Gateway / 动态脱敏 / 审计日志 / OpenAPI

[应用服务层]
  Asset / Config / Collector / State / Event / Alert / Log / Policy
  Automation / AIops / Ticket / Knowledge / Governance

[引擎层]
  Scheduler / Worker Pool / Collector Runtime / Policy Runtime
  Automation Runtime / AI Agent Runtime / Notification Runtime / Observability Runtime

[数据层]
  Relational DB / Redis-compatible Cache-Lock-Queue / Time-series Store
  Log Store / Object Storage / Vector Store

[被管环境]
  Agentless Assets / Server Agents / Edge Collectors / Network Devices
  Databases / Middleware / Applications / Kubernetes / Cloud Resources
```

---

## 4. 技术选型原则

### 4.1 总原则

- 简单优先。
- 私有化友好。
- 离线部署友好。
- 国产化迁移友好。
- 可替换。
- 不过早复杂化。
- 不绑定单一厂商。
- 不依赖公有云。
- 能先单机部署，后续扩展集群。

### 4.2 推荐技术栈

前端：Vue 3、TypeScript、Vite、Pinia、Element Plus、ECharts、Playwright。  
后端：Python 3.10+、FastAPI、SQLAlchemy 2.0、Pydantic V2、Alembic、pytest、ruff、black、mypy。  
数据库：默认 MySQL/MariaDB 兼容路线，通过 SQLAlchemy 保留 PostgreSQL、openGauss、人大金仓、达梦迁移空间。  
中间件：Redis 兼容组件、VictoriaMetrics/Prometheus、MinIO、Qdrant/Chroma、vLLM/Ollama、OpenTelemetry。  
日志：第一阶段以关系库索引 + 文件/对象存储保存执行日志，后续可接 Loki/OpenSearch。

### 4.3 数据库兼容策略

1. 所有数据访问通过 repository 层。
2. 避免不可迁移数据库特性。
3. 不把 PostgreSQL JSONB 作为核心依赖。
4. 尽量使用标准字段和关系表。
5. 原生 SQL 必须集中管理。
6. 所有数据库变更必须使用 Alembic。
7. migration 必须有回滚说明。
8. 数据库兼容性纳入测试。

---

## 5. 核心领域设计

## 5.1 资产中心 Asset Center

目标：管理平台中所有可观测、可配置、可告警、可执行、可分析的对象。

资产类型：

- Linux 主机、Windows 主机、网络设备、安全设备、存储设备。
- 数据库、中间件、Web 服务、API 服务、进程、端口。
- 容器、Kubernetes 工作负载、虚拟化资源、云资源、业务系统、外部依赖。

核心能力：

- 资产发现、资产纳管、资产分组、资产标签、资产关系。
- 生命周期、可达状态、健康状态、采集状态。
- 凭证绑定、采集模板绑定、策略绑定。
- 自动化能力声明、影响范围分析、拓扑视图。

核心表：

- `assets`
- `asset_ips`
- `asset_tags`
- `asset_groups`
- `asset_relations`
- `asset_credentials`
- `asset_collection_profiles`
- `asset_policy_bindings`
- `asset_lifecycle_events`
- `discovery_tasks`
- `discovery_results`

## 5.2 配置与凭证中心 Config Center

目标：管理平台期望状态，包括采集、阈值、通知、策略、脚本、AI 模板和凭证。

能力：

- 配置定义、配置分类、配置模板、配置版本、配置发布、配置灰度、配置回滚。
- 配置继承、配置差异、配置影响分析、配置审计、配置漂移检测。
- 凭证加密、凭证绑定、凭证测试、凭证轮换。

配置层级：

```text
全局配置 → 组织/租户配置 → 业务系统配置 → 资产组配置 → 单资产配置
```

核心表：

- `config_definitions`
- `config_versions`
- `config_releases`
- `config_bindings`
- `config_drifts`
- `credentials`
- `credential_bindings`
- `change_records`
- `change_approvals`

## 5.3 采集与状态中心 Collector & State Center

目标：采集中心负责感知现实环境，状态中心负责回答“现在怎么样”。

采集模式：

1. Agentless：适合快速部署。
2. Agent：适合深度采集和本地执行。
3. Edge Collector：适合多网段、多机房和安全域隔离。

支持协议：ICMP、TCP、SNMP、SSH、WMI/WinRM、REST API、Syslog、数据库连接、文件日志、IPMI、Redfish、VMware API、Kubernetes API。

采集器接口：

```python
class BaseCollector:
    def validate_config(self, config): ...
    def test_connection(self, target, credential): ...
    def collect(self, target, config, context): ...
    def parse(self, raw_result): ...
    def normalize(self, parsed_result): ...
```

统一输出：

```json
{
  "collector": "ssh",
  "target_asset_id": "asset-001",
  "status": "success",
  "metrics": [],
  "logs": [],
  "facts": {},
  "errors": [],
  "started_at": "2026-01-01T00:00:00",
  "finished_at": "2026-01-01T00:01:00",
  "trace_id": "trace-001"
}
```

能力：

- 采集器注册、能力声明、健康检查。
- 采集任务调度、分片、标准化、失败分类。
- 最新状态缓存、状态历史、状态变更事件、WebSocket 状态推送、状态恢复验证。

## 5.4 事件与告警中心 Event & Alert Center

事件来源：

- 采集结果、状态变化、日志命中、配置变更、配置漂移。
- 自动化执行、工单变更、AI 分析、平台组件异常、Agent 心跳异常。

事件处理：

```text
raw signal → normalized event → deduplication → correlation
→ classification → routing → alert / policy / ticket / audit
```

告警能力：

- 告警生成、收敛、抑制、静默、升级、确认、转工单、触发策略。
- 告警生命周期、复盘、压缩率统计、影响范围分析。

## 5.5 日志与可观测中心 Log & Observability Center

目标：成为故障分析、执行审计、AI 诊断和自动化闭环的证据中心。

日志类型：

- 设备日志、应用日志、系统日志、采集日志、执行日志、审计日志、平台运行日志、AI 工具调用日志、Trace。

执行日志模型：

```text
execution_id
  ├── trigger_source
  ├── policy_id
  ├── playbook_id
  ├── script_version
  ├── target_assets
  ├── parameters
  ├── approval_id
  ├── steps
  ├── stdout stream
  ├── stderr stream
  ├── exit_code
  ├── duration
  ├── final_status
  └── audit_record
```

能力：

- 日志采集、解析、脱敏、检索、实时流。
- 日志与事件、告警、执行、工单关联。
- AI 日志解释、OpenTelemetry Trace、平台自身指标监控。

## 5.6 策略中心 Policy Engine

策略结构：

- 触发源、触发条件、适用范围、时间窗口、前置条件、排除条件。
- 风险等级、审批要求、动作链、验证条件、失败处理、回滚动作。
- 通知规则、优先级、冲突处理、命中解释、版本、发布状态、最大影响面限制。

能力：

- 策略模板、创建、版本、发布、灰度、模拟、冲突检测、命中解释。
- 策略执行历史、成功率统计、误触发分析。

## 5.7 自动化执行中心 Automation Engine

执行对象：

- Shell、PowerShell、Python 脚本、SQL 检查、REST API 调用、服务重启、配置回滚、文件清理、日志压缩、备份、健康检查、巡检、Playbook。

执行状态机：

```text
created → validated → risk_assessed → dry_run_completed → waiting_approval
→ approved/rejected → queued → running → verifying
→ success/failed/partial_success → rollback_running/rollback_success/rollback_failed → closed
```

企业级约束：

- 幂等性、dry-run、审批、并发锁、分批执行、灰度执行、实时日志。
- 高危命令黑名单、自动执行白名单、最大影响面限制。
- 执行前快照、执行后验证、失败回滚、生产环境二次确认、审计。

## 5.8 AIops 与知识中心

AI 是受控诊断与决策辅助层，而不是自由执行器。

AI 输入上下文：

- 资产信息、资产关系、当前状态、指标趋势、相关事件、相关告警、相关日志。
- 最近配置变更、最近执行记录、相关工单、相似案例、可用策略、可执行动作、风险边界、用户权限。

AI 输出格式：

```json
{
  "summary": "故障摘要",
  "impact": "影响范围",
  "probable_causes": [
    {"cause": "可能原因", "confidence": 0.82, "evidence": ["证据1", "证据2"]}
  ],
  "recommended_actions": [
    {"action": "建议动作", "risk": "low", "requires_approval": false}
  ],
  "verification_plan": ["验证步骤"],
  "uncertainties": ["不确定信息"]
}
```

Agentic Workflow 阶段：

1. 结构化分析和推荐动作。
2. 只读工具调用，如查询资产、指标、日志、告警和工单。
3. 生成执行计划，由策略中心校验。
4. 低风险动作在策略允许范围内自动执行。
5. 高风险动作必须人工确认。

知识必须结构化：适用场景、触发条件、诊断步骤、处置步骤、验证步骤、风险等级、是否可自动执行、关联资产类型、关联告警类型、关联策略和 Playbook。

## 5.9 工单与协同中心 Ticket Center

能力：

- 告警转工单、策略触发工单、自动化失败转工单、人工创建工单。
- SLA、自动派单、审批、评论、附件、时间线。
- 关联告警、事件、执行、日志、AI 分析。
- 复盘总结、工单转知识。

## 5.10 平台治理中心 Governance Center

能力：

- 用户、角色、RBAC、ABAC、API Key、租户预留、菜单、字典。
- 审计日志、动态脱敏、凭证安全、备份恢复。
- 平台健康、组件状态、一键自检、离线部署、升级回滚、安全基线、系统参数。

---

## 6. 前端架构

一级工作台：

1. 运维指挥台。
2. 资产与配置台。
3. 监控与事件台。
4. 故障处置台。
5. 自动化编排台。
6. AI 与知识台。
7. 平台管理台。

前端目录：

```text
frontend/src/
  app/
    router/
    store/
    permission/
    layout/

  features/
    command-center/
    asset-config/
    monitoring-event/
    incident-response/
    automation-orchestration/
    aiops-knowledge/
    ticket/
    platform-admin/

  shared/
    api/
    components/
    hooks/
    utils/
    types/
    constants/
```

故障处置台结构：

```text
左侧：故障时间线
中间：证据与分析
右侧：推荐动作与执行控制
底部：实时日志流
```

必须展示：告警摘要、影响范围、指标趋势、日志片段、配置变更、AI 分析、策略命中解释、dry-run 结果、审批、执行按钮、实时日志、验证结果、转工单、知识草稿。

---

## 7. 数据架构

存储分工：

| 数据类型 | 推荐存储 | 说明 |
|---|---|---|
| 资产、配置、策略、工单、用户、审批 | MySQL/MariaDB 兼容数据库 | 核心业务数据 |
| 高频指标 | VictoriaMetrics/Prometheus | 时序数据 |
| 执行日志索引、审计索引 | 关系库 | 可查询和关联 |
| 大体量日志内容 | 文件/对象存储，后续可接 Loki/OpenSearch | 降低第一阶段复杂度 |
| 最新状态、锁、会话、轻量队列 | Redis 兼容组件 | 实时能力 |
| 附件、报告、归档 | MinIO/S3 兼容存储 | 大文件 |
| 知识向量 | Qdrant/Chroma/可替换向量库 | RAG 检索 |

数据流：

```text
采集器 / Agent / 边缘采集器
  ↓
标准化采集结果
  ├── 指标 → 时序库
  ├── 最新状态 → Redis + 状态表
  ├── 日志 → 日志索引 + 日志存储
  ├── 资产事实 → 资产中心
  ├── 配置事实 → 配置漂移
  └── 异常信号 → 事件中心
```

---

## 8. 大模型与 AI 配置

大模型必须配置化，不写死在代码中。

示例：

```yaml
llm:
  provider: vllm
  base_url: http://127.0.0.1:8000/v1
  model: qwen3.5-0.8b
  timeout_seconds: 60
  max_tokens: 2048
  temperature: 0.2

aiops:
  enable_tool_calling: true
  require_policy_guard: true
  require_human_approval_for_high_risk: true
  default_analysis_template: incident_root_cause
```

模型不可用时，告警、采集、策略和自动化不能中断；AI 分析显示不可用，并产生 AI 服务异常事件。

---

## 9. 私有化与离线部署

部署模式：

- 单机部署。
- Docker Compose 部署。
- 多节点部署。
- 物理机部署。
- 离线部署。
- 边缘采集器部署。
- 后续高可用部署。

离线包应包含：

- 后端镜像、前端构建产物、Python wheelhouse。
- 数据库 migration、默认配置模板、本地模型配置示例。
- install.sh、upgrade.sh、rollback.sh、self_check.sh。
- 文档。

升级必须支持：升级前备份、migration 自动执行、配置差异保留、升级后自检、升级失败回滚、数据不丢失。

---

## 10. 标准验证场景

验证场景不是专项代码，而是通过通用能力配置出来。

第一阶段内置标准知识库和处置方案：

1. Linux 磁盘空间异常。
2. Windows 服务异常。
3. Web 端口不可达。
4. 数据库连接数过高。
5. 数据库连接失败。
6. 证书即将过期。
7. 采集器离线。
8. 自动化执行失败。

每个方案都应包含：适用资产类型、触发事件、判断条件、诊断步骤、处置动作、风险等级、是否需要审批、dry-run 逻辑、验证方式、失败处理、知识说明。

---

## 11. 演进路线

### 阶段一：平台底座设计与建设

重点建设：领域架构、数据模型、API 契约、文档体系、配置中心、资产中心、采集与状态中心、事件与告警中心、策略中心、自动化执行中心、日志中心、基础 AIops、平台自监控。

### 阶段二：标准场景闭环验证

通过标准知识库和通用能力验证多场景闭环。重点不是写专项代码，而是证明平台能力可配置、可复用、可扩展。

### 阶段三：Agent 与边缘采集器

补充 Agent、Edge Collector、断点续传、深度采集、本地执行、多网段部署。

### 阶段四：AI Agentic Workflow

补充只读工具调用、执行计划生成、策略校验、Human-in-the-loop、低风险自动化、高风险审批。

### 阶段五：企业级增强

补充高可用、多租户、国产化数据库适配、信创环境适配、外部系统集成、插件化采集器、报表和审计增强。
