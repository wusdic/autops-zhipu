# AUTOPS - 自治运维操作系统

> 面向私有化部署场景的自治运维操作系统

## 项目定位

AUTOPS 不是普通监控平台、工单系统、脚本平台或简单 AI 助手。它将资产、配置、状态、事件、告警、日志、策略、自动化执行、AI 分析、工单协同、知识沉淀和平台自身治理整合成一个可持续演进的闭环系统。

## 核心闭环

```
资源发现 → 资产纳管 → 配置治理 → 状态采集 → 事件识别 → 告警收敛
→ 影响分析 → AI 诊断 → 策略决策 → 自动化执行 → 实时日志
→ 结果验证 → 回滚/升级/关闭 → 知识沉淀 → 策略优化
```

## 当前状态

**M0-M5 全部完成，执行层已实现。** 平台具备完整自治运维能力：

| 能力 | 状态 | 说明 |
|------|------|------|
| 资产发现 | ✅ 已实现 | TCP/ICMP/CIDR网段扫描，自动识别资产类型 |
| 自动纳管 | ✅ 已实现 | 发现任务支持 auto_onboard：扫描完成自动纳管全部存活IP（默认开启，幂等）；也支持手动4步纳管向导 |
| 状态采集 | ✅ 已实现 | Ping/TCP端口/HTTP/SSL证书/数据库 5个内置采集器，纳管后立即采集+每5分钟定期采集 |
| 事件驱动 | ✅ 已实现 | 状态变更→事件→告警规则匹配→告警创建 |
| 告警管理 | ✅ 已实现 | 告警规则、生命周期、自动恢复 |
| 策略引擎 | ✅ 已实现 | 策略匹配、触发条件、动作链、审批机制 |
| 自动化执行 | ✅ 已实现 | 脚本库、执行状态机、dry-run、实时日志 |
| AI 分析 | ✅ 已实现 | LLM集成、结构化分析输出 |
| 知识中心 | ✅ 已实现 | 知识模型、标准知识库导入 |
| 工单中心 | ✅ 已实现 | 工单状态机、告警/执行关联 |
| 认证鉴权 | ✅ 已实现 | JWT 全局认证（中间件白名单）+ RBAC 角色（super_admin/admin/operator/viewer/ai_operator）+ require_admin 管理端点保护 |
| 前端界面 | ✅ 已实现 | 7大工作台、36+页面、完整路由 |
| 离线部署 | ✅ 已实现 | 安装/升级/回滚/自检脚本 |

### 已验证的端到端事件链路

```
Ping采集 → 状态变更(offline→online) → STATE_CHANGED事件 
→ 告警规则匹配 → 告警创建(warning) → 策略匹配 
→ 自动化执行(脚本) → 执行完成 → 告警自动resolved
```

## 技术架构

### 后端

- **框架：** FastAPI + SQLAlchemy 2.0 + Pydantic V2
- **数据库：** MySQL/MariaDB（兼容 PostgreSQL / openGauss / 达梦 / 人大金仓）
- **缓存/队列：** Redis
- **异步：** asyncio + async/await 全异步架构
- **数据库迁移：** Alembic

### 前端

- **框架：** Vue 3 + TypeScript + Vite
- **UI库：** Element Plus
- **状态管理：** Pinia
- **路由：** Vue Router 4
- **图表：** ECharts
- **实时通信：** WebSocket

### 领域模块（13个）

| 模块 | 路径 | 说明 |
|------|------|------|
| 资产中心 | `backend/app/domains/asset/` | 资产CRUD、IP管理、标签、分组、关系、生命周期 |
| 配置中心 | `backend/app/domains/config/` | 配置定义、版本、发布、绑定、差异、漂移检测 |
| 采集中心 | `backend/app/domains/collector/` | Collector注册、采集任务调度、标准化输出 |
| 状态中心 | `backend/app/domains/state/` | 状态快照、变更事件、最新状态缓存 |
| 事件中心 | `backend/app/domains/event/` | 事件标准化、去重、关联、路由 |
| 告警中心 | `backend/app/domains/alert/` | 告警规则、生命周期、收敛、升级 |
| 策略中心 | `backend/app/domains/policy/` | 策略定义、触发条件、动作链、模拟 |
| 自动化中心 | `backend/app/domains/automation/` | 脚本库、Playbook、执行状态机、审批 |
| 日志中心 | `backend/app/domains/log/` | 执行日志、审计日志、日志检索 |
| AIops | `backend/app/domains/aiops/` | LLM集成、Context Builder、根因分析 |
| 知识中心 | `backend/app/domains/knowledge/` | 知识模型、向量检索、标准知识库 |
| 工单中心 | `backend/app/domains/ticket/` | 工单模型、状态机、SLA |
| 治理中心 | `backend/app/domains/governance/` | 用户、角色、权限、API Key、审计 |

### 执行层组件

| 组件 | 路径 | 说明 |
|------|------|------|
| 发现引擎 | `backend/app/domains/discovery/` | TCP/ICMP扫描、CIDR解析、资产类型推断 |
| 内置采集器 | `backend/app/workers/builtin_collectors.py` | Ping、TCP端口、HTTP、SSL证书、数据库检查 |
| 采集调度器 | `backend/app/workers/scheduler.py` | 定时采集、事件触发采集、状态变更检测 |
| 事件处理器 | `backend/app/common/event_handlers.py` | 事件→告警→策略→自动化 完整链路 |

## 前端页面（7大工作台）

| 工作台 | 页面数 | 关键页面 |
|--------|--------|----------|
| 指挥中心 | 3 | 运维指挥台、故障处置、AI诊断 |
| 资产配置 | 6 | 资产列表、资产发现、分组、凭证、配置、采集器 |
| 监控事件 | 5 | 监控总览、事件列表、告警中心、告警规则、工单 |
| 自动化 | 4 | 脚本库、Playbook、策略管理、执行历史 |
| 知识 | 3 | 知识库、知识导入、AI分析记录 |
| 平台管理 | 5 | 用户、角色、权限、系统配置、审计日志 |

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+ / MariaDB 10.6+
- Redis 7.0+

### 后端启动

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 配置数据库
cp ../.env.example .env
# 编辑 .env 设置数据库连接

# 数据库迁移
alembic upgrade head

# 启动后端
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

### 默认登录

- 用户名：`admin`
- 密码：初始口令由种子脚本生成。
  - 若设置了环境变量 `ADMIN_INITIAL_PASSWORD`，则用该值作为初始口令；
  - 否则随机生成 16 位口令并打印到种子日志（仅显示一次）。
- 首次登录后请立即在「个人中心」修改密码。

> ⚠️ 生产环境请务必设置 `ADMIN_INITIAL_PASSWORD` 或从日志中获取随机口令，不要使用任何文档示例值。

## 文档入口

| 文档 | 路径 |
|---|---|
| 全局约束 | [docs/00-overview/GLOBAL_CONSTRAINTS.md](docs/00-overview/GLOBAL_CONSTRAINTS.md) |
| 产品定位 | [docs/00-overview/PRODUCT_POSITIONING.md](docs/00-overview/PRODUCT_POSITIONING.md) |
| 路线图 | [docs/00-overview/ROADMAP.md](docs/00-overview/ROADMAP.md) |
| 目标架构 | [docs/01-architecture/AUTOPS_TARGET_ARCHITECTURE.md](docs/01-architecture/AUTOPS_TARGET_ARCHITECTURE.md) |
| 开发计划 | [docs/05-implementation/AUTOPS_DEVELOPMENT_AND_GOVERNANCE_PLAN.md](docs/05-implementation/AUTOPS_DEVELOPMENT_AND_GOVERNANCE_PLAN.md) |

## 项目统计

- **后端 API 端点：** 145+
- **数据库表：** 36
- **领域模块：** 13
- **前端页面：** 36+
- **前端路由：** 38

## 许可证

待定
