# AUTOPS 差距分析报告

> 对照文档：`AUTOPS_详细开发计划与文档治理方案_最终版.md`
> 分析日期：2026-05-31
> 分析范围：仓库结构、文档、后端基础设施、14个领域、前端7大工作台、测试策略、部署方案、里程碑

---

## 总览评分

| 维度 | 完成度 | 评级 |
|------|--------|------|
| 仓库结构 | 95% (2项缺失) | A |
| 文档治理 | 100% (36/36文档) | A |
| ADR决策记录 | 100% (8个ADR) | A |
| 后端基础设施 | 90% | A- |
| 领域模块(核心) | 75% | B |
| 前端7大工作台 | 90% | A- |
| 测试体系 | 25% | D |
| 部署方案 | 95% | A |
| CI/CD | 10% | D |
| 事件系统 | 5% | D |

**综合完成度：约 72%**

---

## 一、仓库结构对照（第2章）

### ✅ 已完成（25/27）

所有顶层目录、后端/前端项目结构、configs、deploy、docs、scripts、tests均已创建。

### ❌ 缺失项

| 项目 | 状态 | 优先级 |
|------|------|--------|
| `LICENSE` | 缺失 | P2 |
| `Makefile` | 缺失 | P2 |

---

## 二、文档治理对照（第3章）

### ✅ 100% 完成

所有36份设计文档全部到位：

- `docs/00-overview/` — 3份（含GLOBAL_CONSTRAINTS额外文档）
- `docs/01-architecture/` — 9份 + 8个ADR
- `docs/02-domains/` — 10份（含NOTIFICATION_CENTER额外文档）
- `docs/03-api/` — 3份
- `docs/04-frontend/` — 5份（含审计报告等额外文档）
- `docs/05-implementation/` — 4份
- `docs/06-operations/` — 5份
- `docs/07-development/` — 4份（含DESIGN_CODE_CONSISTENCY额外文档）

---

## 三、后端基础设施对照（第5.1章）

### ✅ 已完成（14/19项）

| # | 要求 | 状态 |
|---|------|------|
| 1 | FastAPI 项目初始化 | ✅ |
| 2 | SQLAlchemy 配置 | ✅ |
| 3 | Alembic 配置 | ✅ |
| 4 | MySQL 连接 | ✅ |
| 5 | Repository 层抽象 | ✅ |
| 6 | Redis 配置 | ✅ |
| 7 | 统一响应结构 | ✅ (code/message/data) |
| 8 | 统一错误码 | ✅ |
| 9 | trace_id | ✅ (common/trace.py) |
| 10 | 审计日志基础 | ✅ (api/audit.py) |
| 11 | 权限框架 | ✅ (RBAC in governance) |
| 12 | 凭证加密 | ✅ (common/crypto.py) |
| 13 | 配置加载器 | ✅ (infra/config.py) |
| 14 | pytest | ✅ |
| 15 | ruff/black/mypy | ✅ (pyproject.toml已配置) |
| 16 | `/health` | ✅ {"status":"alive"} |
| 17 | `/ready` | ✅ {"status":"ready","checks":{"database":"ok","redis":"ok"}} |

### ❌ 缺失项

| 项目 | 说明 | 优先级 |
|------|------|--------|
| 请求上下文 | 无显式request context middleware | P1 |
| 动态脱敏工具 | masking.py存在但未集成到API响应层 | P1 |
| pre-commit | pyproject.toml有配置但无.pre-commit-config.yaml文件 | P2 |
| OpenTelemetry | trace.py有基础trace_id但无OTel埋点 | P2 |

---

## 四、领域模块成熟度矩阵（第5.2/6章）

### 模块结构评分

| 领域 | models | schemas | repository | service | api | events | handlers | permissions | tests | 评分 |
|------|--------|---------|------------|---------|-----|--------|----------|-------------|-------|------|
| asset | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | B |
| config | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | B |
| collector | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | B |
| state | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | B |
| event | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | B |
| alert | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | B |
| policy | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | B |
| automation | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | B |
| aiops | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | B |
| knowledge | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | B |
| ticket | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | B |
| governance | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | B |
| log | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | C |
| notification | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | D |

### 🔴 系统性缺失（全部领域）

这是最大的差距，**跨越所有14个领域**：

1. **events.py** — 所有领域均无事件定义文件
2. **handlers.py** — 所有领域均无事件处理器文件
3. **permissions.py** — 所有领域均无独立权限定义文件
4. **领域README.md** — 所有14个领域均缺少README

### 功能深度差距（按领域）

#### 6.1 资产中心
| 功能 | 状态 |
|------|------|
| 资产/IP/标签/分组/关系模型 | ✅ 完整 |
| 生命周期/可达/健康状态 | ✅ |
| 资产发现任务 | ✅ (discovery_api.py) |
| 资产导入 | ✅ |
| 关系图接口 | ❌ 拓扑图前端有(254行)但后端无topology API |
| 资产时间线 | ⚠️ 有timeline字段但无独立时间线API |
| 资产与凭证/采集模板/策略绑定 | ⚠️ 部分实现 |

#### 6.2 配置与凭证中心
| 功能 | 状态 |
|------|------|
| 配置定义/版本 | ✅ |
| 配置发布 | ✅ |
| 配置差异/回滚 | ❌ 无diff/rollback逻辑 |
| 配置漂移检测 | ❌ |
| 凭证加密/测试/审计 | ✅ 加密有，测试部分 |
| 维护窗口 | ⚠️ 模型有字段但无独立API |

#### 6.3 采集与状态中心
| 功能 | 状态 |
|------|------|
| BaseCollector抽象 | ❌ 无统一基类/注册机制 |
| Collector Registry | ❌ |
| Collector Health | ❌ |
| Collection Job/Result | ✅ |
| SSH/WMI/HTTP/TCP/DB/Cert采集器 | ⚠️ 模型有type枚举但无实际执行逻辑 |
| State Snapshot/Change | ✅ |

#### 6.4 事件与告警中心
| 功能 | 状态 |
|------|------|
| Event模型/去重 | ✅ |
| Event关联 | ❌ 无correlation引擎 |
| Alert规则/生命周期 | ⚠️ 基础有，缺少完整状态机 |
| Alert抑制 | ✅ 有模型字段 |
| Alert升级 | ✅ 有API |
| Alert时间线 | ❌ 无独立timeline |
| Alert上下文构建器 | ⚠️ 有context字段但非自动构建 |

#### 6.5 策略中心
| 功能 | 状态 |
|------|------|
| 策略模型/版本 | ✅ |
| 触发条件/动作链 | ✅ |
| 策略模拟 | ✅ (dry_run API) |
| 冲突检测 | ❌ |
| 审批规则 | ✅ |
| 最大影响面控制 | ❌ |

#### 6.6 自动化执行中心
| 功能 | 状态 |
|------|------|
| 脚本库/Playbook | ✅ |
| 执行任务/步骤 | ✅ |
| dry-run | ✅ |
| 风险评估 | ❌ |
| 审批/并发锁 | ✅ 审批有，并发锁无 |
| 实时日志/WebSocket | ❌ 后端无WS端点 |
| 执行超时/重试/验证 | ⚠️ 部分字段 |
| 回滚动作 | ❌ |
| 高危命令黑名单 | ⚠️ 模型有blocked_commands字段 |
| 自动执行白名单 | ❌ |

#### 6.7 日志与可观测中心
| 功能 | 状态 |
|------|------|
| 日志模型/API | ✅ 基础CRUD |
| stdout/stderr流 | ⚠️ 有字段 |
| WebSocket实时日志 | ❌ |
| 审计日志 | ⚠️ 在api/audit.py而非log领域 |
| 日志脱敏 | ❌ 未集成 |
| OpenTelemetry | ❌ |
| 平台指标暴露 | ⚠️ /health /ready |

#### 6.8 AIops与知识中心
| 功能 | 状态 |
|------|------|
| LLM配置/Context Builder | ✅ |
| Root Cause Analyzer | ✅ |
| 知识库CRUD/导入 | ✅ |
| 向量检索 | ❌ 无embedding/向量库集成 |
| Tool Guard | ❌ |
| Human-in-the-loop | ❌ |
| AI Feedback | ⚠️ 有模型字段 |
| 模型不可用降级 | ❌ |

#### 6.9 工单中心
| 功能 | 状态 |
|------|------|
| 工单模型/CRUD | ✅ |
| 状态机 | ❌ 无显式状态机 |
| 告警转工单 | ❌ 无自动转换 |
| 工单时间线 | ❌ |
| 工单关联上下文 | ⚠️ 有字段 |
| 工单转知识草稿 | ⚠️ 有字段但无逻辑 |

#### 6.10 治理中心
| 功能 | 状态 |
|------|------|
| 用户/角色模型 | ✅ |
| 权限模型 | ⚠️ Role有permissions字段但无独立Permission模型 |
| API Key | ✅ |
| 动态脱敏 | ✅ masking.py |
| 审计日志 | ✅ |
| 系统参数 | ❌ 无SystemConfig模型 |
| 平台健康 | ✅ /health /ready |

---

## 五、前端7大工作台对照（第7章）

### 页面清单与成熟度

| 工作台 | 页面 | 行数 | 成熟度 |
|--------|------|------|--------|
| **运维指挥台** | CommandCenterPage | 843 | ✅ 完整 |
| | IncidentResponsePage | 1181 | ✅ 完整 |
| **资产与配置台** | AssetListPage | 854 | ✅ |
| | AssetDetailPage | 779 | ✅ |
| | AssetTopologyPage | 254 | ⚠️ 骨架 |
| | AssetDiscoveryPage | 536 | ✅ |
| | AssetGroupPage | 414 | ✅ |
| | CredentialPage | 454 | ✅ |
| | ConfigPage | 637 | ✅ |
| | CollectorPage | 770 | ✅ |
| **监控与事件台** | MonitoringOverviewPage | 579 | ✅ |
| | EventListPage | 1036 | ✅ |
| | AlertListPage | 670 | ✅ |
| | AlertDetailPage | 1121 | ✅ |
| | AlertRulePage | 314 | ⚠️ 基本 |
| | TicketPage | 1223 | ✅ |
| | TicketDetailPage | 646 | ✅ |
| **自动化编排台** | ScriptListPage | 1197 | ✅ |
| | PlaybookListPage | 322 | ⚠️ |
| | PolicyListPage | 352 | ⚠️ |
| | PolicySimulatePage | 164 | ❌ 骨架 |
| | ExecutionListPage | 905 | ✅ |
| | ExecutionDetailPage | 542 | ✅ |
| **AI与知识台** | AiOpsPage | 1090 | ✅ |
| | KnowledgePage | 447 | ✅ |
| | KnowledgeDetailPage | 568 | ✅ |
| | KnowledgeEditPage | 263 | ⚠️ |
| | KnowledgeImportPage | 731 | ✅ |
| **平台管理台** | LoginPage | 94 | ✅ |
| | UserManagementPage | 303 | ⚠️ |
| | RoleManagementPage | 310 | ⚠️ |
| | ApiKeyPage | 286 | ⚠️ |
| | SystemConfigPage | 632 | ✅ |
| | PlatformStatusPage | 392 | ✅ |
| | BackupPage | 552 | ✅ |
| | AuditLogPage | 310 | ⚠️ |

**共38个Vue页面，路由38条。**

### 缺失功能

| 功能 | 状态 |
|------|------|
| WebSocket实时推送 | ❌ 前端有composable但后端无WS端点 |
| 批量操作框架 | ⚠️ 部分页面有 |
| ECharts深度集成 | ✅ 仪表盘已集成 |

---

## 六、标准知识库（第8章）

### ✅ 已完成

所有8个标准方案均已写入种子数据：
1. Linux磁盘空间异常 ✅
2. Windows服务未运行 ✅
3. Web端口不可达 ✅
4. 数据库连接数过高 ✅
5. 数据库连接失败 ✅
6. SSL证书即将过期 ✅
7. 采集器离线 ✅
8. 自动化执行失败 ✅

### ⚠️ 差距

- 标准方案作为种子数据存在，但未验证是否可被策略中心/自动化中心完整调用链贯穿
- 缺少端到端验证脚本

---

## 七、测试策略对照（第9章）

### 🔴 重大差距

| 测试类型 | 计划要求 | 实际状态 |
|----------|----------|----------|
| 单元测试 | 核心业务80%+ | 13个测试文件存在，覆盖率未知 |
| 集成测试 | 全链路闭环 | 0个 |
| E2E测试 | 登录→创建→采集→告警→AI→执行→验证→知识 | 0个，无Playwright配置 |
| 安全测试 | Secret扫描/凭证/脱敏/越权 | 0个 |
| 容错测试 | DB/Redis/模型/Worker异常 | 0个 |

---

## 八、CI/CD与部署（第10-11章）

| 项目 | 状态 |
|------|------|
| GitHub Actions CI | ❌ 无 .github/workflows |
| pre-commit hooks | ❌ 无 .pre-commit-config.yaml |
| docs-check CI | ❌ |
| install.sh | ✅ 216行 |
| upgrade.sh | ✅ 113行 |
| rollback.sh | ✅ 93行 |
| self_check.sh | ✅ 106行 |
| docker-compose.yml | ✅ |
| 离线部署文档 | ✅ |

---

## 九、里程碑对照（第11章）

| 里程碑 | 要求 | 实际 | 状态 |
|--------|------|------|------|
| M0 设计完成 | 全局约束、架构、领域、API、数据模型、前端、测试、部署 | 52份文档+8个ADR | ✅ 100% |
| M1 基础骨架 | 后端启动、前端启动、DB/Redis、统一响应、错误码、trace_id、审计、权限 | 全部就绪 | ✅ 100% |
| M2 平台主干 | 14个领域CRUD+API+前端 | 领域CRUD完整，缺事件系统 | ⚠️ 85% |
| M3 标准场景闭环 | 知识库+策略+自动化+工单+知识沉淀全链路 | 种子数据有，链路未验证 | ⚠️ 60% |
| M4 私有化可用 | install/upgrade/rollback/self_check/离线/备份 | 脚本完整 | ✅ 95% |
| M5 增强阶段 | Agent/Edge Collector/AI Tool/Human-in-loop/集成/国产化 | 未开始 | ❌ 5% |

---

## 十、优先级排序修复清单

### P0 — 必须修复（影响架构完整性）

| # | 项目 | 影响范围 | 工作量 |
|---|------|----------|--------|
| P0-1 | **事件系统**：为所有领域创建events.py + 全局EventBus | 全局 | 3-5天 |
| P0-2 | **领域间交互**：通过事件替代直接调用（设计文档要求） | 全局 | 2-3天 |
| P0-3 | **WebSocket后端**：实时日志推送、告警推送 | 自动化/监控 | 2-3天 |
| P0-4 | **单元测试补全**：核心service层80%覆盖 | 质量 | 3-5天 |

### P1 — 应该修复（影响核心功能）

| # | 项目 | 影响范围 | 工作量 |
|---|------|----------|--------|
| P1-1 | 领域README.md（14个领域） | 规范 | 0.5天 |
| P1-2 | 事件关联引擎(Event Correlation) | 事件中心 | 1-2天 |
| P1-3 | 工单状态机+告警转工单 | 工单中心 | 1-2天 |
| P1-4 | 配置diff/rollback/漂移检测 | 配置中心 | 2天 |
| P1-5 | 自动化回滚/并发锁 | 自动化中心 | 1-2天 |
| P1-6 | 资产拓扑图后端API | 资产中心 | 1天 |
| P1-7 | 向量检索基础(知识中心) | AIops | 2-3天 |
| P1-8 | 集成测试(全链路) | 质量 | 3-5天 |

### P2 — 可以延后（完善性增强）

| # | 项目 | 影响范围 | 工作量 |
|---|------|----------|--------|
| P2-1 | LICENSE + Makefile | 规范 | 0.1天 |
| P2-2 | pre-commit-config.yaml | 规范 | 0.5天 |
| P2-3 | GitHub Actions CI | CI/CD | 1天 |
| P2-4 | OpenTelemetry埋点 | 可观测 | 2-3天 |
| P2-5 | 安全测试+容错测试 | 质量 | 3-5天 |
| P2-6 | Playwright E2E测试 | 质量 | 3-5天 |
| P2-7 | E2E验证脚本(8个标准场景) | 验证 | 2天 |
| P2-8 | M5增强功能(Agent/Edge等) | 增强 | 10+天 |
| P2-9 | Collector实际执行逻辑 | 采集 | 3-5天 |
| P2-10 | 每个领域permissions.py | 安全 | 2天 |

---

## 十一、总结

**已完成的核心价值：**
- 36张数据库表 + 145个API端点 + 38个Vue页面的全栈平台骨架
- 52份设计文档 + 8个ADR，形成完整的单一事实源
- 种子数据覆盖18类，8个标准知识库方案
- 部署脚本完整（install/upgrade/rollback/self_check）
- 前端构建成功，后端32/32 API全部通过

**最大差距（按影响排序）：**
1. **事件系统完全缺失** — 这是架构层面的系统性缺口，所有领域间的联动（状态→事件→告警→策略→自动化→日志→工单→知识）依赖它
2. **测试体系严重不足** — 只有13个基础测试文件，无集成/E2E/安全/容错测试
3. **WebSocket未实现** — 实时日志/告警推送无后端支撑
4. **部分高级功能缺失** — 配置diff/漂移、工单状态机、向量检索、Tool Guard等
