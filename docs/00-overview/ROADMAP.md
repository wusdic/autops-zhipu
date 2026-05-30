# AUTOPS 项目路线图

> 文档状态：current  
> 是否为事实源：yes  
> 建议路径：`docs/00-overview/ROADMAP.md`

---

## 概述

AUTOPS 路线图按 6 个里程碑推进，每个里程碑有明确的交付物、验收条件和依赖关系。

**核心原则：**
- 先设计后编码，M0 完成前不写业务代码
- 平台整体优先，不围绕 MVP 写专项代码
- 每个里程碑必须通过验收条件才能进入下一个
- 所有阶段遵循全局约束和目标架构

---

## M0 — 设计完成

**目标：** 完成全部设计文档，建立项目共识基线。

### 交付物

| # | 交付物 | 路径 |
|---|---|---|
| 1 | 全局约束 | `docs/00-overview/GLOBAL_CONSTRAINTS.md` |
| 2 | 产品定位 | `docs/00-overview/PRODUCT_POSITIONING.md` |
| 3 | 路线图 | `docs/00-overview/ROADMAP.md` |
| 4 | 目标架构 | `docs/01-architecture/AUTOPS_TARGET_ARCHITECTURE.md` |
| 5 | 后端架构 | `docs/01-architecture/BACKEND_ARCHITECTURE.md` |
| 6 | 前端架构 | `docs/01-architecture/FRONTEND_ARCHITECTURE.md` |
| 7 | 数据架构 | `docs/01-architecture/DATA_ARCHITECTURE.md` |
| 8 | 安全架构 | `docs/01-architecture/SECURITY_ARCHITECTURE.md` |
| 9 | AI Agent 架构 | `docs/01-architecture/AI_AGENT_ARCHITECTURE.md` |
| 10 | 部署架构 | `docs/01-architecture/DEPLOYMENT_ARCHITECTURE.md` |
| 11 | 10 份领域设计 | `docs/02-domains/*.md` |
| 12 | API 契约 | `docs/03-api/API_CONTRACT.md` |
| 13 | 错误码 | `docs/03-api/ERROR_CODES.md` |
| 14 | WebSocket 事件 | `docs/03-api/WEBSOCKET_EVENTS.md` |
| 15 | 前端工作流 | `docs/04-frontend/*.md` |
| 16 | 测试策略 | `docs/05-implementation/TESTING_STRATEGY.md` |
| 17 | 验收标准 | `docs/05-implementation/ACCEPTANCE_CRITERIA.md` |
| 18 | 部署文档 | `docs/06-operations/*.md` |
| 19 | 开发规范 | `docs/07-development/*.md` |
| 20 | ADR 记录 | `docs/01-architecture/adr/` |

### 验收条件

- [x] 三份核心文档已归位
- [ ] 全部 37 份设计文档已完成
- [ ] 自检清单全部通过
- [ ] 无概念冲突
- [ ] 无模块边界不清
- [ ] 无过度复杂设计
- [ ] 数据模型可演进

### 依赖关系

无前置依赖。本阶段是整个项目的起点。

### 风险点

| 风险 | 影响 | 缓解措施 |
|---|---|---|
| 设计过度导致延期 | 阻塞后续开发 | 控制每份文档的深度，足够落地即可 |
| 领域边界争议 | 返工 | 严格遵循九类统一模型 |
| 技术选型犹豫 | 阻塞 | 遵循简单优先原则，后续可替换 |

---

## M1 — 基础骨架完成

**目标：** 后端和前端可启动，基础设施链路打通。

### 交付物

#### 后端基础

| # | 交付物 | 说明 |
|---|---|---|
| 1 | FastAPI 项目初始化 | `backend/app/main.py` |
| 2 | SQLAlchemy + Alembic 配置 | 数据库连接、migration 框架 |
| 3 | MySQL/MariaDB 默认连接 | 连接池、重试、健康检查 |
| 4 | Redis 连接 | 缓存、锁、轻量队列 |
| 5 | 配置加载器 | `configs/*.yaml` 统一加载 |
| 6 | 统一响应结构 | `{code, message, data, trace_id}` |
| 7 | 统一错误码 | 错误码体系 + 全局异常处理 |
| 8 | trace_id | 请求链路追踪 |
| 9 | 请求上下文 | 用户、租户、权限上下文 |
| 10 | 审计日志基础 | 审计记录写入能力 |
| 11 | 权限框架 | RBAC 基础、JWT 认证 |
| 12 | 动态脱敏 | 敏感字段自动脱敏 |
| 13 | 凭证加密 | AES-256-GCM 加解密工具 |
| 14 | OpenTelemetry 埋点 | 基础 trace 和 metric |
| 15 | pytest 框架 | 测试配置和 fixtures |
| 16 | 代码质量工具 | ruff、black、mypy、pre-commit |

#### 前端基础

| # | 交付物 | 说明 |
|---|---|---|
| 17 | Vue 3 + TypeScript + Vite | 项目初始化 |
| 18 | 路由配置 | vue-router + 权限守卫 |
| 19 | Pinia 状态管理 | 全局 store |
| 20 | API Client | axios 封装 + 拦截器 |
| 21 | 布局框架 | 主布局 + 侧边栏 + 标签页 |
| 22 | 主题配置 | Element Plus 主题 |
| 23 | WebSocket Client | 实时通信封装 |

### 验收条件

- [ ] 后端 `uvicorn app.main:app` 可启动
- [ ] `/health` 返回 200
- [ ] `/ready` 返回 200（检查 DB + Redis）
- [ ] `alembic upgrade head` 可执行
- [ ] API 返回统一结构 `{code, message, data, trace_id}`
- [ ] 每个请求有 trace_id
- [ ] 错误响应使用统一错误码
- [ ] pytest 可运行且通过
- [ ] 配置从 `configs/*.yaml` 加载
- [ ] 前端 `npm run dev` 可启动
- [ ] 前端可显示登录页

### 依赖关系

**前置：** M0 设计完成

### 风险点

| 风险 | 影响 | 缓解措施 |
|---|---|---|
| MySQL 未安装 | 无法启动后端 | 提供安装脚本和 Docker Compose |
| Python 版本兼容 | 依赖冲突 | 严格 Python 3.10+ |
| 前端依赖下载慢 | 开发阻塞 | 配置 npm 镜像 |

---

## M2 — 平台主干完成

**目标：** 13 个领域模块的核心逻辑可运行。

### 交付物

| # | 领域模块 | 核心能力 |
|---|---|---|
| 1 | 资产中心 | 资产CRUD、IP管理、标签、分组、关系、生命周期、发现任务 |
| 2 | 配置中心 | 配置定义、版本、发布、绑定、差异、漂移检测 |
| 3 | 凭证中心 | 凭证加密存储、绑定、测试、使用审计 |
| 4 | 采集中心 | BaseCollector、Collector Registry、采集任务调度、标准化输出 |
| 5 | 状态中心 | 状态快照、状态变更、最新状态缓存、变更事件 |
| 6 | 事件中心 | 事件标准化、去重、关联、分类、路由 |
| 7 | 告警中心 | 告警规则、生命周期、收敛、抑制、升级、时间线 |
| 8 | 策略中心 | 策略定义、版本、触发条件、动作链、模拟、冲突检测 |
| 9 | 自动化中心 | 脚本库、Playbook、执行状态机、dry-run、审批、回滚 |
| 10 | 日志中心 | 执行日志分片、实时流、日志检索、审计日志 |
| 11 | AIops 基础 | LLM 配置加载、Context Builder、结构化分析输出 |
| 12 | 知识中心基础 | 知识模型、标准知识库导入、向量检索基础 |
| 13 | 工单中心 | 工单模型、状态机、关联、SLA |

每个领域模块包含：models.py, schemas.py, repository.py, service.py, events.py, handlers.py, permissions.py, tests/

### 采集器实现

| 采集器 | 协议 | 说明 |
|---|---|---|
| SSH Collector | SSH | Linux 主机采集 |
| WMI/WinRM Collector | WMI/WinRM | Windows 主机采集 |
| HTTP/TCP Collector | HTTP/TCP | Web 服务和端口检测 |
| Database Check Collector | DB 协议 | 数据库连接和状态检查 |
| Certificate Collector | TLS/SSL | 证书有效期检查 |

### 验收条件

- [ ] 每个领域有领域文档和初始模型
- [ ] 每个领域不直接访问其他领域数据库表
- [ ] 领域间通过 service 或 event 交互
- [ ] 资产可创建、查询、更新、删除
- [ ] 凭证可加密存储、绑定、测试
- [ ] 采集任务可调度并返回标准化结果
- [ ] 状态变化可生成事件
- [ ] 事件可触发告警
- [ ] 告警有生命周期
- [ ] 策略可定义和模拟
- [ ] 自动化执行有完整状态机
- [ ] 执行有实时日志
- [ ] AI 可返回结构化分析结果
- [ ] 核心业务逻辑单元测试覆盖率 80%+

### 依赖关系

**前置：** M1 基础骨架完成

---

## M3 — 标准场景闭环完成

**目标：** 8 个标准验证场景通过平台通用能力完成闭环验证。

### 交付物

| # | 交付物 | 说明 |
|---|---|---|
| 1 | 标准知识库 | 8 个标准处置方案的知识库条目 |
| 2 | 标准事件规则 | 对应 8 个场景的事件识别规则 |
| 3 | 标准策略 | 对应 8 个场景的处置策略 |
| 4 | 标准自动化动作 | 对应 8 个场景的 Playbook 和脚本 |
| 5 | 故障处置台 | 时间线、证据链、AI 分析、策略命中、执行控制 |
| 6 | 执行日志流 | WebSocket 实时日志推送 |
| 7 | 验证结果 | 执行后自动验证 |
| 8 | 工单升级 | 自动化失败自动转工单 |
| 9 | 知识沉淀 | 处置经验生成知识草稿 |
| 10 | E2E 测试 | 8 个场景的端到端测试 |

### 标准验证场景

| # | 场景 | 触发 | 诊断 | 处置 | 验证 |
|---|---|---|---|---|---|
| 1 | Linux 磁盘空间异常 | disk_usage > 90% | SSH 采集磁盘、大文件、日志增长 | 清理临时文件、压缩日志、删除旧文件 | 磁盘使用率 < 阈值 |
| 2 | Windows 服务异常 | service_status != running | WMI 查询服务状态 | 重启服务 | 服务状态为 running |
| 3 | Web 端口不可达 | tcp_check failed | HTTP 状态码、响应时间 | 重启服务、通知 | 端口可达 |
| 4 | 数据库连接数过高 | connections > threshold | 查询活跃连接、慢查询 | 终止空闲连接 | 连接数恢复正常 |
| 5 | 数据库连接失败 | connection_test failed | 检查服务状态、监听端口 | 重启数据库服务 | 连接测试通过 |
| 6 | SSL 证书即将过期 | days_remaining < 30 | 检查证书详情 | 通知 + 续期提醒 | 新证书有效期 > 30 天 |
| 7 | 采集器离线 | heartbeat_timeout | 检查采集器状态 | 通知 + 重试 | 采集器恢复在线 |
| 8 | 自动化执行失败 | execution_failed | 检查执行日志、错误分类 | 转工单 + 回滚 | 工单已创建 |

### 验收条件

- [ ] 8 个场景全部通过端到端测试
- [ ] 每个场景通过通用能力完成，无专项代码
- [ ] 故障处置台可展示完整证据链
- [ ] AI 分析结果结构化
- [ ] 策略命中有解释
- [ ] 执行日志实时可查看
- [ ] 执行后自动验证
- [ ] 失败可转工单
- [ ] 成功可生成知识草稿
- [ ] 前端七大工作台基础可用

### 依赖关系

**前置：** M2 平台主干完成

---

## M4 — 私有化可用

**目标：** 平台支持离线安装、升级回滚和自监控。

### 交付物

| # | 交付物 | 说明 |
|---|---|---|
| 1 | `deploy/scripts/install.sh` | 一键安装脚本 |
| 2 | `deploy/scripts/upgrade.sh` | 升级脚本 |
| 3 | `deploy/scripts/rollback.sh` | 回滚脚本 |
| 4 | `deploy/scripts/self_check.sh` | 自检脚本 |
| 5 | `deploy/docker/docker-compose.yml` | 完整 Docker Compose |
| 6 | `deploy/offline/` | 离线安装包构建 |
| 7 | 备份恢复功能 | 数据库备份、配置备份、恢复 |
| 8 | 平台自监控 | 组件健康、指标暴露、自检 API |
| 9 | 安全基线检查 | 安全配置检查脚本 |

### 验收条件

- [ ] `install.sh` 可在全新 CentOS/Ubuntu 上安装
- [ ] `upgrade.sh` 可从上一版本升级，数据不丢失
- [ ] `rollback.sh` 可回滚到上一版本
- [ ] `self_check.sh` 可检查所有组件健康状态
- [ ] Docker Compose 可一键启动全部服务
- [ ] 离线包可在无网络环境安装
- [ ] 备份和恢复正常工作
- [ ] 平台自身状态可在仪表盘查看
- [ ] 升级前自动备份
- [ ] 升级后自动自检

### 依赖关系

**前置：** M3 标准场景闭环完成

---

## M5 — 增强阶段

**目标：** 补充 Agent、边缘采集、AI 深度和企业级能力。

### 交付物

| # | 交付物 | 说明 |
|---|---|---|
| 1 | Agent | 服务器端本地代理 |
| 2 | Edge Collector | 多网段、多机房边缘采集器 |
| 3 | AI Tool Calling | 只读工具调用（查询资产、指标、日志） |
| 4 | Human-in-the-loop | 高风险动作人工确认流程 |
| 5 | 低风险自动执行 | 策略允许范围内的自动处置 |
| 6 | 外部系统集成 | Webhook、邮件、短信、钉钉、企业微信 |
| 7 | 国产化数据库适配 | PostgreSQL、openGauss、达梦、人大金仓验证 |
| 8 | 信创环境适配 | ARM 架构、麒麟 OS、统信 UOS 验证 |
| 9 | 高可用方案 | 多节点部署、数据库主从 |
| 10 | 插件化采集器 | 第三方采集器注册机制 |
| 11 | 报表和审计增强 | 运维报表、合规审计 |

### 验收条件

- [ ] Agent 可安装并在目标主机运行
- [ ] Edge Collector 可跨网段采集
- [ ] AI 可调用只读工具获取实时信息
- [ ] 高风险动作必须人工确认
- [ ] 通知可通过多种渠道发送
- [ ] 国产化数据库通过兼容性测试
- [ ] ARM 架构部署验证通过

### 依赖关系

**前置：** M4 私有化可用

---

## 时间线概览

```text
M0 设计完成 ──────────────────────────
                                       M1 基础骨架 ──────────
                                                                M2 平台主干 ────────────────
                                                                                             M3 场景闭环 ──────────
                                                                                                                     M4 私有化 ──────────
                                                                                                                                           M5 增强 ────────
```

**说明：** 时间线根据实际执行情况调整。核心约束是每个里程碑必须通过验收条件才能推进。

---

## 版本号规则

- M0：`0.0.0-design`
- M1：`0.1.0-skeleton`
- M2：`0.2.0-core`
- M3：`0.3.0-validation`
- M4：`1.0.0-release`
- M5：`1.x.0-enhancement`
