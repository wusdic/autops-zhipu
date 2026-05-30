# AUTOPS 详细开发计划与文档治理方案（最终版）

> 项目名称：autops  
> 文档状态：current  
> 是否为事实源：yes  
> 建议路径：`docs/05-implementation/AUTOPS_DEVELOPMENT_AND_GOVERNANCE_PLAN.md`  
> 文档定位：本文件根据 AUTOPS 目标架构制定，指导 Hermes 或开发团队从空仓库开始完成设计、开发、测试、部署、文档治理和长期演进。

---

## 1. 工作总原则

### 1.1 空仓库起步

本项目从零开始构建。不迁移、不适配、不复用任何既有实现。所有代码、目录、接口、表结构、页面、脚本和文档均按照 AUTOPS 目标架构新建。

### 1.2 先设计，后编码

任何编码前必须完成：

1. 总体目录结构设计。
2. 领域模块设计。
3. 数据库模型设计。
4. API 契约设计。
5. 前端页面流设计。
6. 安全边界设计。
7. 自动化执行状态机设计。
8. AI 工具调用边界设计。
9. 测试方案设计。
10. 部署方案设计。

未完成设计不得开始实现。

### 1.3 平台整体优先，MVP 验证靠后

整体开发不围绕某个 MVP 写代码。所有模块按平台宏观架构建设。标准验证场景只用于验收平台能力是否完整，不允许为场景写特殊逻辑。

---

## 2. 仓库初始结构

```text
autops/
  README.md
  CHANGELOG.md
  LICENSE
  .env.example
  .gitignore
  docker-compose.yml
  Makefile

  backend/
    pyproject.toml
    alembic.ini
    app/
      main.py
      api/
      domains/
      common/
      infra/
      workers/
      integrations/
      tests/

  frontend/
    package.json
    vite.config.ts
    src/
      app/
      features/
      shared/

  configs/
    app.yaml
    database.yaml
    redis.yaml
    llm.yaml
    security.yaml
    collectors.yaml
    policies.yaml

  deploy/
    docker/
    offline/
    scripts/
      install.sh
      upgrade.sh
      rollback.sh
      self_check.sh

  docs/
    00-overview/
    01-architecture/
    02-domains/
    03-api/
    04-frontend/
    05-implementation/
    06-operations/
    07-development/
    99-archive/

  scripts/
    dev/
    maintenance/
    data_seed/

  tests/
    e2e/
    simulation/
```

---

## 3. 文档先行阶段

必须先创建：

- `docs/00-overview/PRODUCT_POSITIONING.md`
- `docs/00-overview/ROADMAP.md`
- `docs/01-architecture/AUTOPS_TARGET_ARCHITECTURE.md`
- `docs/01-architecture/BACKEND_ARCHITECTURE.md`
- `docs/01-architecture/FRONTEND_ARCHITECTURE.md`
- `docs/01-architecture/DATA_ARCHITECTURE.md`
- `docs/01-architecture/SECURITY_ARCHITECTURE.md`
- `docs/01-architecture/AI_AGENT_ARCHITECTURE.md`
- `docs/01-architecture/DEPLOYMENT_ARCHITECTURE.md`
- `docs/01-architecture/adr/`
- `docs/02-domains/ASSET_CENTER.md`
- `docs/02-domains/CONFIG_CENTER.md`
- `docs/02-domains/COLLECTOR_STATE_CENTER.md`
- `docs/02-domains/EVENT_ALERT_CENTER.md`
- `docs/02-domains/LOG_OBSERVABILITY_CENTER.md`
- `docs/02-domains/POLICY_ENGINE.md`
- `docs/02-domains/AUTOMATION_ENGINE.md`
- `docs/02-domains/AIOPS_KNOWLEDGE_CENTER.md`
- `docs/02-domains/TICKET_CENTER.md`
- `docs/02-domains/GOVERNANCE_CENTER.md`
- `docs/03-api/API_CONTRACT.md`
- `docs/03-api/ERROR_CODES.md`
- `docs/03-api/WEBSOCKET_EVENTS.md`
- `docs/04-frontend/UX_WORKFLOWS.md`
- `docs/04-frontend/PAGE_STRUCTURE.md`
- `docs/04-frontend/INCIDENT_RESPONSE_UI.md`
- `docs/05-implementation/TESTING_STRATEGY.md`
- `docs/05-implementation/ACCEPTANCE_CRITERIA.md`
- `docs/06-operations/DEPLOYMENT.md`
- `docs/06-operations/OFFLINE_DEPLOYMENT.md`
- `docs/06-operations/UPGRADE_AND_ROLLBACK.md`
- `docs/06-operations/BACKUP_RESTORE.md`
- `docs/06-operations/PLATFORM_SELF_CHECK.md`
- `docs/07-development/CONTRIBUTING.md`
- `docs/07-development/PR_CHECKLIST.md`
- `docs/07-development/CODING_STYLE.md`

---

## 4. ADR 机制

所有重大技术决策必须写 ADR，包括：关系数据库选择、缓存和队列选择、时序库选择、日志存储方式、向量库选择、AI Agent 框架、自动化执行安全边界、国产化兼容策略、离线部署策略、权限模型。

ADR 模板：

```text
# ADR-0001-标题

## 状态
proposed / accepted / superseded

## 背景

## 决策

## 备选方案

## 影响

## 后续动作
```

---

## 5. 后端开发计划

### 5.1 后端基础设施阶段

任务：

1. 初始化 FastAPI 项目。
2. 配置 SQLAlchemy。
3. 配置 Alembic。
4. 配置 MySQL/MariaDB 默认连接。
5. 抽象 repository 层。
6. 配置 Redis。
7. 建立统一响应结构。
8. 建立统一错误码。
9. 建立 trace_id。
10. 建立请求上下文。
11. 建立审计日志基础能力。
12. 建立权限框架。
13. 建立动态脱敏工具。
14. 建立凭证加密工具。
15. 建立配置加载器。
16. 建立 OpenTelemetry 基础埋点。
17. 建立 pytest。
18. 建立 ruff、black、mypy。
19. 建立 pre-commit。

验收：

- 后端可启动。
- `/health` 可用。
- `/ready` 可用。
- 数据库 migration 可执行。
- Redis 可连接。
- API 返回统一结构。
- 每个请求有 trace_id。
- 错误码统一。
- 单元测试可运行。
- 配置从 `configs/*.yaml` 加载。

### 5.2 领域目录阶段

创建：

```text
backend/app/domains/
  asset/
  config/
  collector/
  state/
  event/
  alert/
  log/
  policy/
  automation/
  aiops/
  knowledge/
  ticket/
  governance/
```

每个领域统一结构：

```text
models.py
schemas.py
repository.py
service.py
events.py
handlers.py
permissions.py
tests/
```

验收：

- 每个领域有 README。
- 每个领域有职责说明。
- 每个领域有初始模型设计。
- 每个领域不直接访问其他领域数据库表，只通过 service 或 event 交互。
- 领域边界写入 `docs/02-domains/`。

---

## 6. 领域开发计划

### 6.1 资产中心

任务：

- 资产模型、资产 IP、标签、分组、关系模型。
- 资产生命周期、可达状态、健康状态。
- 资产发现任务、资产导入、资产详情。
- 资产关系图接口。
- 资产与凭证、采集模板、策略绑定。
- 资产时间线。

验收：

- 可以创建 Linux、Windows、数据库、Web 服务等资产。
- 可以绑定凭证和采集模板。
- 可以查看资产当前状态和时间线。
- 资产关系可被故障影响分析调用。

### 6.2 配置与凭证中心

任务：

- 配置定义、配置版本、配置发布、配置绑定。
- 配置差异、配置回滚、配置影响范围、配置漂移。
- 凭证加密、凭证测试、凭证绑定、凭证使用审计。
- 维护窗口、变更记录。

验收：

- 采集模板可版本化。
- 策略配置可版本化。
- 凭证加密存储，不可明文导出。
- 配置发布有审计，可回滚。
- 执行记录能记录所用配置版本。

### 6.3 采集与状态中心

任务：

- BaseCollector、Collector Registry、Collector Capability、Collector Health。
- Collection Job、Collection Result、Collection Log。
- SSH Collector、WMI/WinRM Collector、HTTP/TCP Collector、Database Check Collector、Certificate Collector。
- State Snapshot、State Change、最新状态缓存、状态变更事件。

验收：

- 采集器统一输入输出。
- 采集失败有错误分类。
- 最新状态可查询。
- 状态变化能生成事件。
- 采集器自身健康可见。

### 6.4 事件与告警中心

任务：

- Event 模型、Event Normalizer、Event Deduplication、Event Correlation。
- Alert Rule、Alert Lifecycle、Alert Timeline、Alert Suppression、Alert Escalation。
- Alert Context Builder。
- Alert 与资产、日志、执行、工单关联。

验收：

- 状态异常生成事件。
- 事件规则生成告警。
- 告警有生命周期和证据链。
- 告警能触发策略、关闭、升级、转工单。

### 6.5 策略中心

任务：

- 策略模型、版本、触发条件、适用范围、风险等级、审批规则。
- 动作链、验证条件、失败处理、回滚动作。
- 策略模拟、冲突检测、命中解释、最大影响面控制。

验收：

- 可以配置多个标准场景策略。
- 策略能模拟。
- 策略命中有解释。
- 高风险策略需要审批。
- 策略不直接执行动作，只调用自动化执行中心。

### 6.6 自动化执行中心

任务：

- 脚本库、Playbook、执行任务、执行步骤。
- dry-run、风险评估、审批、并发锁。
- 实时日志、执行超时、重试、验证、回滚、执行审计。
- 高危命令黑名单、自动执行白名单。

验收：

- 每次执行有 execution_id、步骤和实时日志。
- 支持 dry-run、验证、失败转工单、回滚。
- 高危命令能被阻断。
- AI 无法绕过执行中心。

### 6.7 日志与可观测中心

任务：

- 执行日志分片、stdout/stderr 流、WebSocket 实时日志。
- 采集日志、审计日志、日志脱敏、日志检索。
- 日志与告警、执行、工单关联。
- OpenTelemetry Trace、平台指标暴露、一键自检。

验收：

- 执行日志可实时查看。
- 日志可按 execution_id 查询。
- 告警详情能展示相关日志。
- AI 能读取相关日志上下文。
- 平台自身状态可见。

### 6.8 AIops 与知识中心

任务：

- LLM 配置加载、AI Context Builder、Root Cause Analyzer、Remediation Planner、Log Interpreter。
- Knowledge Retriever、Knowledge Writer、AI Feedback、Tool Guard。
- 只读工具调用、Human-in-the-loop。
- 标准知识库导入、标准处置方案导入、向量检索。

验收：

- 模型名称和地址来自配置。
- AI 分析输入包含完整上下文。
- AI 输出结构化 JSON。
- AI 推荐动作必须进入策略校验。
- AI 工具调用有审计。
- 标准知识库可导入，多个标准场景可命中。
- 模型不可用时平台降级。

### 6.9 工单与协同中心

任务：

- 工单模型、工单状态机、告警转工单、自动化失败转工单。
- 工单时间线、评论、附件、SLA。
- 工单关联告警、事件、执行、日志、AI 分析。
- 工单转知识草稿。

验收：

- 告警可转工单。
- 自动化失败可转工单。
- 工单能看到完整上下文。
- 工单关闭可生成知识草稿。

### 6.10 平台治理中心

任务：

- 用户、角色、权限、API Key、审计日志、动态脱敏。
- 系统参数、平台健康、备份恢复、升级回滚、离线部署、安全基线。

验收：

- 用户权限可控。
- 高危动作按权限拦截。
- API Key 有范围和有效期。
- 审计日志可查询。
- 平台支持备份恢复、离线安装和升级回滚。

---

## 7. 前端开发计划

### 7.1 基础阶段

任务：

- 初始化 Vue 3 + TypeScript + Vite。
- 配置路由、Pinia、API Client、权限守卫、布局、主题。
- 配置 WebSocket Client、错误处理、E2E 测试框架。

### 7.2 工作台

- 运维指挥台：总体健康、严重告警、自动化执行、采集成功率、平台健康、待审批动作。
- 资产与配置台：资产列表、详情、关系、凭证绑定、采集模板绑定、策略绑定、配置发布。
- 监控与事件台：实时状态、指标趋势、事件流、告警列表、日志检索。
- 故障处置台：时间线、证据链、AI 分析、策略、审批、执行控制、实时日志。
- 自动化编排台：脚本库、Playbook、策略编排、策略模拟、dry-run、执行历史。
- AI 与知识台：知识库、标准处置方案、AI 分析记录、AI 反馈、知识草稿审核。
- 平台管理台：用户、角色、权限、API Key、系统配置、平台健康、审计日志、备份恢复。

---

## 8. 标准知识库与验证场景

标准知识库格式示例：

```yaml
id: kb-linux-disk-high
title: Linux 磁盘空间异常处置
asset_types:
  - linux_server
trigger_events:
  - disk_usage_high
diagnosis:
  - check_disk_usage
  - check_large_files
  - check_log_growth
actions:
  - dry_run_cleanup
  - compress_logs
  - cleanup_temp_files
verification:
  - check_disk_usage_below_threshold
risk_level: low
requires_approval: false
```

第一批标准方案：

1. Linux 磁盘空间异常。
2. Windows 服务未运行。
3. Web 端口不可达。
4. 数据库连接数过高。
5. 数据库连接失败。
6. SSL 证书即将过期。
7. 采集器离线。
8. 自动化执行失败。

这些方案必须进入知识库、策略中心和自动化中心，不允许写成专项接口。

---

## 9. 测试策略

### 9.1 单元测试

覆盖：

- 资产 service、配置版本、凭证加密、数据脱敏。
- 采集器 normalize、状态变更、事件生成、告警规则。
- 策略命中、dry-run、执行状态机、AI 输出解析、权限校验。

目标：核心业务逻辑覆盖率 80%+。

### 9.2 集成测试

覆盖：

```text
资产 → 配置 → 采集 → 状态 → 事件 → 告警 → 策略
→ 自动化 → 日志 → 验证 → 工单 → 知识
```

### 9.3 E2E 测试

覆盖：登录、创建资产、绑定凭证、触发采集、查看告警、查看 AI 分析、执行 dry-run、执行自动化、查看实时日志、查看验证结果、生成知识草稿。

### 9.4 安全测试

覆盖：Secret 扫描、凭证不明文、动态脱敏、权限越权、高危命令阻断、API Key 越权、审计完整性。

### 9.5 容错测试

模拟：数据库异常、Redis 异常、模型服务异常、采集器离线、Worker 失败、WebSocket 断开、自动化脚本失败。

---

## 10. 文档治理方案

### 10.1 Docs as Code

文档和代码同仓库管理，所有设计和实现必须同步更新。

### 10.2 文档目录

```text
docs/
  00-overview/
  01-architecture/
  02-domains/
  03-api/
  04-frontend/
  05-implementation/
  06-operations/
  07-development/
  99-archive/
```

### 10.3 单一事实源

| 内容 | 文件 |
|---|---|
| 产品定位 | `docs/00-overview/PRODUCT_POSITIONING.md` |
| 总体架构 | `docs/01-architecture/AUTOPS_TARGET_ARCHITECTURE.md` |
| 数据架构 | `docs/01-architecture/DATA_ARCHITECTURE.md` |
| 安全架构 | `docs/01-architecture/SECURITY_ARCHITECTURE.md` |
| API 契约 | `docs/03-api/API_CONTRACT.md` |
| 领域设计 | `docs/02-domains/*.md` |
| 前端流程 | `docs/04-frontend/UX_WORKFLOWS.md` |
| 开发计划 | `docs/05-implementation/AUTOPS_DEVELOPMENT_AND_GOVERNANCE_PLAN.md` |
| 部署 | `docs/06-operations/DEPLOYMENT.md` |
| 测试 | `docs/07-development/TESTING_GUIDE.md` |

### 10.4 PR 检查

每个 PR 必须确认：

```text
[ ] 是否修改领域模型？
[ ] 是否修改 API？
[ ] 是否修改数据库？
[ ] 是否修改配置？
[ ] 是否修改事件？
[ ] 是否修改策略？
[ ] 是否修改自动化动作？
[ ] 是否修改 AI 工具调用？
[ ] 是否修改前端页面？
[ ] 是否修改部署？
[ ] 是否修改安全边界？
[ ] 是否同步更新文档？
[ ] 是否新增或修改测试？
```

### 10.5 docs-check CI

CI 应检查：

- 修改 backend/app/domains 时，对应 docs/02-domains 是否更新。
- 修改 backend/app/api 时，docs/03-api 或 OpenAPI 是否更新。
- 修改 frontend/src/features 时，docs/04-frontend 是否更新。
- 修改 deploy/configs 时，docs/06-operations 是否更新。
- 修改安全相关代码时，SECURITY_ARCHITECTURE 是否更新。
- 修改数据库模型时，DATA_ARCHITECTURE 和 migration 是否更新。

---

## 11. 里程碑

### M0：设计完成

交付：全局约束、目标架构、详细开发计划、领域设计、API 草案、数据模型、前端流程、测试方案、部署方案。

### M1：基础骨架完成

交付：后端启动、前端启动、数据库 migration、Redis、配置加载、统一响应、错误码、trace_id、审计、权限、测试框架。

### M2：平台主干完成

交付：资产中心、配置中心、采集与状态中心、事件与告警中心、策略中心、自动化执行中心、日志中心、AIops 基础、知识中心基础。

### M3：标准场景闭环完成

交付：标准知识库导入、多场景事件规则、多场景策略、多场景自动化动作、故障处置台、执行日志、验证结果、工单升级、知识沉淀。

### M4：私有化可用

交付：install.sh、upgrade.sh、rollback.sh、self_check.sh、离线包、备份恢复、平台自监控。

### M5：增强阶段

交付：Agent、Edge Collector、AI Tool Calling、Human-in-the-loop、外部系统集成、国产化数据库适配验证。
