# AUTOPS 设计-编码一致性方法论

> 文档路径：`docs/07-development/DESIGN_CODE_CONSISTENCY.md`
> 状态：current | 事实源：yes
> 原则：**先设计，后编码。设计即契约。代码必须服从设计。**

---

## 1. 核心原则

### 1.1 单向依赖：设计 → 代码

```
设计文档（事实源）
    ↓ 驱动
代码实现
    ↓ 反向同步（仅当实现经验暴露设计缺陷时）
设计文档修订
    ↓ 再驱动
代码调整
```

**禁止**从代码反向推导设计后不再更新文档。任何代码变更必须先更新设计。

### 1.2 三类变更的处理规则

| 变更类型 | 流程 | 示例 |
|---|---|---|
| **新增功能** | 设计文档新增章节 → 编码实现 | 新增通知模块 |
| **修复 bug** | 检查设计文档 → 设计正确则修代码，设计有误则先修设计再修代码 | 字段名不匹配 |
| **重构** | 先更新设计文档的目标状态 → 再逐步调整代码 | API 路径统一 |

### 1.3 文档即 CI 门禁

每次 PR / 提交必须检查：
- 修改了数据库模型？→ 检查 `DATA_ARCHITECTURE.md`
- 修改了 API 路由？→ 检查 `API_CONTRACT.md`
- 修改了前端页面？→ 检查 `PAGE_STRUCTURE.md`
- 修改了领域逻辑？→ 检查 `docs/02-domains/*.md`

---

## 2. 设计文档体系（单一事实源）

### 2.1 四层文档结构

```
Layer 1 - 产品与架构
├── docs/00-overview/PRODUCT_POSITIONING.md    — 产品定位
├── docs/01-architecture/AUTOPS_TARGET_ARCHITECTURE.md — 总体架构
└── docs/01-architecture/BACKEND_ARCHITECTURE.md — 后端架构

Layer 2 - 数据与接口契约
├── docs/01-architecture/DATA_ARCHITECTURE.md  — 数据库全量表结构设计
├── docs/03-api/API_CONTRACT.md                — API 全量端点契约
├── docs/03-api/ERROR_CODES.md                 — 统一错误码
└── docs/03-api/WEBSOCKET_EVENTS.md            — WebSocket 事件契约

Layer 3 - 领域设计
├── docs/02-domains/ASSET_CENTER.md            — 资产中心
├── docs/02-domains/CONFIG_CENTER.md           — 配置与凭证中心
├── docs/02-domains/COLLECTOR_STATE_CENTER.md  — 采集与状态中心
├── docs/02-domains/EVENT_ALERT_CENTER.md      — 事件与告警中心
├── docs/02-domains/POLICY_ENGINE.md           — 策略中心
├── docs/02-domains/AUTOMATION_ENGINE.md       — 自动化执行中心
├── docs/02-domains/LOG_OBSERVABILITY_CENTER.md— 日志与可观测中心
├── docs/02-domains/AIOPS_KNOWLEDGE_CENTER.md  — AIops 与知识中心
├── docs/02-domains/TICKET_CENTER.md           — 工单与协同中心
├── docs/02-domains/GOVERNANCE_CENTER.md       — 平台治理中心
└── docs/02-domains/NOTIFICATION_CENTER.md     — 通知中心

Layer 4 - 前端与运维
├── docs/04-frontend/PAGE_STRUCTURE.md         — 前端页面全量清单
├── docs/04-frontend/UX_WORKFLOWS.md           — 用户工作流
├── docs/06-operations/DEPLOYMENT.md           — 部署方案
└── docs/05-implementation/TESTING_STRATEGY.md — 测试策略
```

### 2.2 事实源优先级

当设计文档与代码不一致时：
1. **设计文档为正确源** — 代码必须调整以匹配设计
2. 如果设计本身不合理 — 先修订设计文档，再调整代码
3. **绝不**在只修改代码后不更新设计

---

## 3. 数据库设计规范

### 3.1 DATA_ARCHITECTURE.md 必须包含

- **每个表的完整列定义**：列名、类型、是否可空、默认值、约束
- **外键关系图**：哪个表引用哪个表
- **索引设计**
- **命名规范**：
  - 表名：小写下划线，复数形式（`assets`, `alert_rules`）
  - 列名：小写下划线
  - 主键：`id`，类型 `VARCHAR(36)`（UUID）
  - 外键：`{引用表单数}_id`（如 `asset_id`, `rule_id`）
  - 时间戳：`created_at`, `updated_at`，类型 `DATETIME`
  - 布尔：`is_{描述}`，类型 `TINYINT(1)`
  - 状态枚举：`{实体}_status` 或 `status`

### 3.2 种子数据脚本的教训

**问题根因**：种子数据脚本基于设计文档编写，但实际建表时列名发生了偏差（如 `ip_address` → `ip`，`health` → `health_status`），导致反复失败。

**解决方案**：
1. 建表脚本必须严格按照 `DATA_ARCHITECTURE.md` 生成
2. 任何列名变更必须先更新文档
3. 种子数据脚本以文档为准，不猜测列名

---

## 4. API 契约规范

### 4.1 API_CONTRACT.md 必须包含

- **每个端点**：方法、路径、请求体、响应体、错误码
- **路径命名规范**：
  - RESTful 风格：`/api/v1/{资源}`、`/api/v1/{资源}/{id}`
  - 子资源：`/api/v1/{资源}/{id}/{子资源}`
  - 动作：`/api/v1/{资源}/{id}/{动作}` （如 `/api/v1/executions/{id}/cancel`）
- **统一响应结构**：
  ```json
  {"code": 0, "message": "success", "data": {...}, "trace_id": "..."}
  ```
- **分页参数**：`page`, `page_size`, 响应含 `total`

### 4.2 前后端 API 一致性

**问题根因**：前端硬编码 API 路径，后端路由变更后前端不知道。

**解决方案**：
- 前端 `shared/api/routes.ts` 是 API 路径的唯一前端事实源
- 后端 `API_CONTRACT.md` 是 API 路径的唯一后端事实源
- 两者必须一一对应，变更时同步更新

---

## 5. 前端设计规范

### 5.1 PAGE_STRUCTURE.md 必须包含

- **每个页面**：路由路径、组件路径、依赖的 API 端点、功能清单
- **布局规范**：哪些路由使用 MainLayout，哪些独立
- **共享组件**：组件名、路径、props、使用页面

### 5.2 前端禁止事项

- **禁止硬编码 API 路径** — 全部从 `routes.ts` 导入
- **禁止硬编码环境值** — 从 `config.ts` 读取
- **禁止直接使用 `fetch/axios`** — 统一使用 `shared/api/client.ts`
- **共享组件导入路径** — `@/shared/components/XXX.vue`

---

## 6. 变更执行流程（SOP）

### 6.1 新增功能 SOP

```
1. 在设计文档中新增章节
   - 领域设计 → docs/02-domains/
   - 数据库表 → DATA_ARCHITECTURE.md
   - API 端点 → API_CONTRACT.md
   - 前端页面 → PAGE_STRUCTURE.md
2. 代码实现
   - 后端 Model → Schema → Repository → Service → Router
   - 前端 types → api 调用 → 页面组件
3. 验证
   - 代码与设计文档一致
   - 种子数据覆盖新表
   - 前端页面可访问
```

### 6.2 修复 Bug SOP

```
1. 定位 bug
2. 查阅设计文档，确认设计的正确状态
3. 如果设计正确、代码有误 → 只修代码
4. 如果设计有误 → 先修设计文档，再修代码
5. 验证修复后代码与设计一致
```

### 6.3 文档反向同步 SOP（当实现已存在但文档缺失或过时时）

```
1. 从实际代码/数据库提取当前状态
2. 写入设计文档，标注"反向同步"
3. 审查：当前状态是否合理？
   - 合理 → 文档保留，作为新的事实源
   - 不合理 → 先修订设计，再调整代码
4. 后续所有变更遵循 6.1 或 6.2 流程
```

---

## 7. 本次项目的经验教训

### 7.1 种子数据14次列名不匹配

| 次序 | 表 | 假设列名 | 实际列名 | 根因 |
|---|---|---|---|---|
| 1 | assets | ip_address | ip, port, hostname | 设计文档未详细定义列 |
| 2 | assets | health | health_status | 列名不一致 |
| 3 | asset_group_members | created_at | (无此列) | 设计假设了不存在的列 |
| 4 | credentials | username, encrypted_secret | cred_type, encrypted_data | 凭证模型设计偏差大 |
| 5 | alert_rules | condition, enabled, updated_at | conditions, event_types, suppress_duration | 规则模型设计偏差 |
| 6 | notifications | is_read | read_at, link, ref_id | 通知模型设计缺失 |
| 7 | ticket_comments | author_id | user_id | 外键列名不一致 |
| 8 | audit_logs | details | trace_id, username, user_agent, detail | 审计模型设计缺失 |
| 9 | state_snapshots | metrics | state_type, status, value, collected_at | 状态模型设计偏差 |
| 10 | state_changes | field | state_type, old_status, new_status, snapshot_id | 状态变更设计偏差 |
| 11 | collection_jobs | status, job_type, started_at | name, schedule, timeout, last_run_at | 采集任务设计偏差 |
| 12 | collectors | status, host, port, last_heartbeat | config_schema, is_builtin | 采集器设计偏差 |
| 13 | scripts | script_type(varchar16) | script_type(varchar16)但值过长 | 类型长度设计未标注 |
| 14 | tickets | assigned_to, creator_id | assigned_to, created_by | 字段命名不一致 |

**根因分析**：所有不匹配的根因都是**设计文档没有在编码前详细定义每个表的列名、类型、约束**。

**根治方案**：`DATA_ARCHITECTURE.md` 必须包含每个表的完整 DDL 级别定义。

### 7.2 前端硬编码 API 路径

**问题**：多个页面直接硬编码 `/api/v1/xxx`，后端路径变更后前端失效。

**根治方案**：`routes.ts` 统一管理 + `API_CONTRACT.md` 作为后端事实源。

### 7.3 导入方式不一致

**问题**：`import { api }` vs `import api`（client.ts 是 default export）。

**根治方案**：在 `PAGE_STRUCTURE.md` 或 `CODING_STYLE.md` 中明确规定导入方式。

---

## 8. 文档维护检查清单

每次提交前必须确认：

```markdown
## 设计-编码一致性检查

### 数据库变更
- [ ] DATA_ARCHITECTURE.md 已更新（表名、列名、类型、约束）
- [ ] 领域文档(docs/02-domains/)已更新（如果影响了领域模型）
- [ ] 种子数据脚本已更新（如果新增了表或列）
- [ ] Alembic migration 已生成（如果是表结构变更）

### API 变更
- [ ] API_CONTRACT.md 已更新（路径、请求体、响应体）
- [ ] 前端 routes.ts 已同步
- [ ] ERROR_CODES.md 已更新（如果新增了错误码）

### 前端变更
- [ ] PAGE_STRUCTURE.md 已更新（页面清单、路由、组件）
- [ ] 没有硬编码 API 路径
- [ ] 没有硬编码环境值
- [ ] 共享组件通过 @/shared/components/ 导入

### 安全变更
- [ ] SECURITY_ARCHITECTURE.md 已更新（如果影响了安全边界）
- [ ] 权限检查已更新（如果新增了端点）
```
