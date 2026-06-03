# P0 后端API补齐设计

> 状态：accepted  
> 日期：2026-06-03  
> 目标：补齐前端 routes.ts 定义但后端未实现的 32 个 API 端点

---

## 1. 设计原则

1. **不新增数据库表** — 所有缺失 API 通过聚合已有域的数据实现，不引入新模型
2. **聚合查询模式** — Dashboard、Stats 类 API 从多个已有域的表中聚合数据
3. **视图/无状态模式** — Business Systems、Tenants、Dictionaries 等轻量CRUD用独立路由文件
4. **遵循已有模式** — `APIRouter(prefix=...)` + `Depends(get_db)` + `success()/paginate()` 响应
5. **静态路由在前，参数路由在后** — 避免路径冲突

## 2. 缺失API分组与实现方案

### 2.1 Dashboard 聚合 API（8个端点）

**位置**: `app/api/dashboard.py`（独立路由文件，非域）

**设计**: 从各域表聚合统计数据，只读不写。

```text
GET /api/v1/dashboard/stats            — 总览统计
GET /api/v1/dashboard/asset-discovery   — 资产发现概况
GET /api/v1/dashboard/inspection        — 巡检概况
GET /api/v1/dashboard/anomaly           — 异常概况
GET /api/v1/dashboard/automation        — 自动化概况
GET /api/v1/dashboard/report            — 报告概况
GET /api/v1/dashboard/platform-health   — 平台健康概况
GET /api/v1/dashboard/my-pending        — 我的待办
```

**数据来源**:
| 端点 | 数据源表 |
|---|---|
| stats | 聚合下面所有子统计 |
| asset-discovery | `discovery_tasks`, `discovery_results`, `assets` |
| inspection | `inspection_tasks`, `inspection_results` |
| anomaly | `anomalies` |
| automation | `executions`, `policies` |
| report | `report_tasks` |
| platform-health | `platform_health`、缓存结果 |
| my-pending | `executions`(待审批) + `anomalies`(待处理) + `tickets`(待处理) |

**实现**: DashboardService 类，注入 session，直接写 select/func.count 查询。

### 2.2 Business Systems API

**位置**: `app/api/business_systems.py`

**设计**: 无独立表，复用 `assets` 表中 `asset_type='business_system'` 的资产，加过滤。

```text
GET    /api/v1/business-systems           — 列表
POST   /api/v1/business-systems           — 创建
GET    /api/v1/business-systems/{id}       — 详情
PUT    /api/v1/business-systems/{id}       — 更新
DELETE /api/v1/business-systems/{id}       — 删除
```

**逻辑**: 创建时 `asset_type='business_system'`，在 asset 域的 service 上封装。

### 2.3 Agents API

**位置**: `app/api/agents.py`

**设计**: 无独立表，复用 `collectors` 表（edge collector 即 agent）。

```text
GET    /api/v1/agents           — Agent列表
GET    /api/v1/agents/{id}      — Agent详情
POST   /api/v1/agents/{id}/upgrade — 升级
```

### 2.4 Inspection Sub-type APIs（4个）

**位置**: `app/api/inspection_subtypes.py`

**设计**: 巡检子类型检查 API，复用 `inspection_results` 表，按 `check_type` 字段过滤。

```text
GET /api/v1/inspection/page-checks     — 页面巡检结果
GET /api/v1/inspection/config-checks   — 配置巡检结果
GET /api/v1/inspection/log-checks      — 日志巡检结果
GET /api/v1/inspection/baseline-checks — 基线巡检结果
```

**逻辑**: 每个端点 = `GET /inspection/results?check_type=xxx` 的快捷方式。

### 2.5 Monitoring 补充 API（4个）

**位置**: `app/api/monitoring_extra.py`

```text
GET /api/v1/collection-results              — 采集结果列表(聚合)
GET /api/v1/metrics/trend/{asset_id}        — 指标趋势
GET /api/v1/log-sources                     — 日志源列表
GET /api/v1/collectors/health               — 采集器健康汇总
```

**数据来源**:
- collection-results: 复用 `collection_results` 表
- metrics/trend: 复用 `states` 表最新快照
- log-sources: 从 `configs` 中查询 `type='log_source'` 的配置
- collectors/health: 聚合 `collectors` 表 + `collection_jobs` 表

### 2.6 Automation 补充 API（3个）

**位置**: `app/api/automation_extra.py`

```text
GET  /api/v1/automation/stats         — 自动化统计
GET  /api/v1/approvals                — 审批列表
POST /api/v1/approvals/{id}/approve   — 审批通过
POST /api/v1/approvals/{id}/reject    — 审批拒绝
GET  /api/v1/dry-run                  — Dry-run 列表
POST /api/v1/dry-run                  — 发起 Dry-run
GET  /api/v1/dry-run/{id}             — Dry-run 详情
```

**数据来源**:
- automation/stats: 聚合 `executions` 表统计
- approvals: 复用 `executions` 表 `status='pending_approval'` 的记录
- dry-run: 复用 `executions` 表 `status='dry_running'` 或 `mode='dry_run'`

### 2.7 Platform 管理补充 API（7个）

**位置**: `app/api/platform_extra.py`

```text
GET    /api/v1/dictionaries               — 字典列表
GET    /api/v1/dictionaries/{type}         — 按类型查询字典
GET    /api/v1/integrations                — 集成列表
GET    /api/v1/integrations/{name}         — 集成详情
POST   /api/v1/integrations/{name}/test    — 测试集成连接
GET    /api/v1/task-queue                  — 任务队列状态
POST   /api/v1/platform/self-check         — 平台自检
GET    /api/v1/tenants                     — 租户列表
POST   /api/v1/tenants                     — 创建租户
GET    /api/v1/tenants/{id}                — 租户详情
PUT    /api/v1/tenants/{id}                — 更新租户
DELETE /api/v1/tenants/{id}                — 删除租户
```

**数据来源**:
- dictionaries: 新建 `dictionaries` 表（轻量KV表，type+key+value+label+sort_order）
- integrations: 从 `configs` 或 `notification_channels` 聚合
- task-queue: 聚合 `outbox` 表 + `inspection_tasks` + `report_tasks` + `executions`
- self-check: 检查 DB/Redis/LLM/Worker 连通性
- tenants: 新建 `tenants` 表（name, code, admin_user_id, quota, status）

### 2.8 Global Search API

**位置**: `app/api/search.py`

```text
GET /api/v1/search?q=xxx&type=asset|ticket|alert|knowledge|...  — 全局搜索
```

**逻辑**: 联合查询 assets/tickets/alerts/knowledge/executions，按 type 参数决定搜哪个表。

## 3. 需要新建的表

仅 2 张轻量表：

### 3.1 dictionaries 表

```sql
CREATE TABLE dictionaries (
  id VARCHAR(36) PRIMARY KEY,
  type VARCHAR(64) NOT NULL,       -- 字典类型(e.g. asset_type, severity)
  value VARCHAR(128) NOT NULL,     -- 字典值
  label VARCHAR(256) NOT NULL,     -- 显示标签
  sort_order INT DEFAULT 0,
  is_active TINYINT DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_type_value (type, value)
);
```

### 3.2 tenants 表

```sql
CREATE TABLE tenants (
  id VARCHAR(36) PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  code VARCHAR(64) NOT NULL UNIQUE,
  admin_user_id VARCHAR(36),
  resource_quota JSON,
  feature_scope JSON,
  status VARCHAR(16) DEFAULT 'active',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 4. 文件变更清单

| 新建文件 | 说明 |
|---|---|
| `app/api/dashboard.py` | Dashboard 聚合 API |
| `app/api/business_systems.py` | 业务系统 API |
| `app/api/agents.py` | Agent 管理 API |
| `app/api/inspection_subtypes.py` | 巡检子类型 API |
| `app/api/monitoring_extra.py` | 监控补充 API |
| `app/api/automation_extra.py` | 自动化补充 API |
| `app/api/platform_extra.py` | 平台管理补充 API |
| `app/api/search.py` | 全局搜索 API |

| 修改文件 | 说明 |
|---|---|
| `app/api/router.py` | 注册新路由 |
| `alembic/versions/xxx_add_dictionaries_tenants.py` | 新建表迁移 |

## 5. 验收标准

- 所有 32 个前端 routes.ts 中定义的端点均有后端实现
- `curl /api/v1/dashboard/stats` 返回 JSON 统计数据
- `vue-tsc --noEmit` 前端编译无错误
- 后端启动无报错
- 不破坏已有 156 个端点的功能
