# AUTOPS 后端13领域深度代码审计报告

> 审计时间: 2026-05-31
> 审计范围: backend/app/domains/ 全部13个领域
> 审计标准: 与 docs/02-domains/ 设计文档逐项对比

---

## 总览成熟度评分

| # | 领域 | 评分 | 状态 |
|---|------|------|------|
| 1 | **asset** | **7/10** | 🟢 基础完善，缺发现任务和动态分组 |
| 2 | **config** | **5/10** | 🟡 框架有，缺漂移检测/回滚/变更记录 |
| 3 | **collector** | **5/10** | 🟡 模型有，缺执行引擎和健康检查 |
| 4 | **state** | **7/10** | 🟢 变更检测实现良好，缺历史查询 |
| 5 | **event** | **5/10** | 🟡 基础CRUD有，去重/关联/路由未实现 |
| 6 | **alert** | **5/10** | 🟡 基础有，缺抑制/升级/转工单 |
| 7 | **policy** | **5/10** | 🟡 模拟仅骨架，缺匹配引擎和冲突检测 |
| 8 | **automation** | **5/10** | 🟡 模型完善，缺实际执行引擎 |
| 9 | **log** | **3/10** | 🔴 严重不足：缺service文件，缺审计日志 |
| 10 | **aiops** | **7/10** | 🟢 最完整，LLM集成可用，上下文构建需加强 |
| 11 | **knowledge** | **6/10** | 🟡 CRUD完整，缺向量搜索和批量导入 |
| 12 | **ticket** | **5/10** | 🟡 基础有，缺SLA/知识沉淀/状态机校验 |
| 13 | **governance** | **6/10** | 🟡 认证完整，缺审计/平台管理 |

---

## 1. 资产中心 (asset) — 评分: 7/10

### 1.1 模型完整性

**已有模型:** Asset, AssetIP, AssetGroup, AssetGroupMember, AssetRelation, AssetTimeline ✅

**缺失:**
- `DiscoveryTask` 模型 — 设计文档要求 `POST /api/v1/discovery-tasks`
- `AssetTag` 独立表 — tags 用 JSON TEXT 存储，不利于索引和查询
- 资产生命周期枚举不完整: 设计要求 `discovered → registered → active → maintenance → inactive → decommissioned`，代码只有 `active/inactive/maintenance/decommissioned`

### 1.2 API端点完整性

| 设计要求 | 状态 |
|---------|------|
| GET /api/v1/assets | ✅ |
| POST /api/v1/assets | ✅ |
| GET /api/v1/assets/{id} | ✅ |
| PUT /api/v1/assets/{id} | ✅ |
| DELETE /api/v1/assets/{id} | ✅ 软删除 |
| POST /api/v1/assets/import | ✅ |
| GET /api/v1/assets/{id}/relations | ✅ |
| POST /api/v1/assets/{id}/relations | ✅ |
| GET /api/v1/assets/{id}/timeline | ✅ |
| GET /api/v1/asset-groups | ✅ |
| POST /api/v1/asset-groups | ✅ |
| POST /api/v1/discovery-tasks | ❌ **缺失** |
| GET /api/v1/discovery-tasks/{id} | ❌ **缺失** |

### 1.3 业务逻辑完整性
- ✅ 创建/更新/删除(软)/批量导入/关系管理/时间线/分组
- ❌ 资产发现 (IP段扫描/SNMP/Agent注册)
- ❌ 动态分组 (基于标签/属性自动匹配)
- ❌ 状态转换校验 (任意状态可转为任意状态)

### 1.4 代码质量问题
1. **SQL注入风险**: `repository.py:38-43` search 方法 `ilike(f"%{search}%")` 未转义 `%` 和 `_`
2. **update_asset exclude_none bug**: `service.py:78` `exclude_none=True` 导致无法将字段设为 None
3. **原始SQL**: `service.py:139` `remove_group_member` 使用原始SQL字符串
4. **手动dict转换**: `api.py:26-47` `_to_dict()` 手动转换，应使用Pydantic model_validate
5. **get_by_name/get_by_ip**: `repository.py:51,56` 未过滤 `is_deleted` 记录

### 1.5 Repository层CRUD问题
- `search` 方法正确
- `get_by_name`/`get_by_ip` 缺少 `is_deleted=False` 过滤条件

---

## 2. 配置与凭证中心 (config) — 评分: 5/10

### 2.1 模型完整性

**已有:** ConfigDefinition, ConfigVersion, ConfigBinding, Credential, CredentialBinding ✅

**缺失:**
- `ConfigDrift` 模型 — 设计要求漂移检测
- `ChangeRecord` 模型 — 设计要求变更记录

### 2.2 API端点完整性

| 设计要求 | 状态 |
|---------|------|
| GET /api/v1/config-definitions | ✅ (路径 /configs/definitions) |
| POST /api/v1/config-definitions | ✅ |
| GET /api/v1/config-definitions/{id}/versions | ✅ |
| POST /api/v1/config-definitions/{id}/versions | ✅ |
| POST /api/v1/config-versions/{id}/publish | ✅ |
| POST /api/v1/config-versions/{id}/rollback | ❌ **缺失** |
| GET /api/v1/config-bindings | ❌ **缺失** |
| POST /api/v1/config-bindings | ❌ **缺失** |
| GET /api/v1/config-drifts | ❌ **缺失** |
| GET /api/v1/credentials | ✅ |
| POST /api/v1/credentials | ✅ |
| POST /api/v1/credentials/{id}/test | ❌ **缺失** |
| POST /api/v1/credential-bindings | ✅ (路径 /credentials/{id}/bind) |
| GET /api/v1/change-records | ❌ **缺失** |

### 2.3 业务逻辑完整性
- ✅ 配置定义CRUD、版本创建、发布、凭证加密存储
- ❌ 版本回滚
- ❌ 配置漂移检测
- ❌ 凭证连接测试
- ❌ 变更记录跟踪
- ❌ 配置层级继承 (global → org → asset)

### 2.4 代码质量问题
1. **`__import__` 反模式**: `service.py:44,61` 使用 `__import__('sqlalchemy').func.count()` / `func.max()`，应在文件顶部 import
2. **计数查询不一致**: `list_definitions` 的 total_count 未应用 config_type 过滤条件（BUG）
3. **计数查询不一致**: `list_credentials` 的 total_count 未应用 cred_type 过滤条件（BUG）
4. **Repository构造函数不一致**: `repository.py` 使用 `BaseRepository(session, Model)` 而 `service.py` 也直接用 `BaseRepository(session, Model)` — 重复创建，未用 repo 子类

### 2.5 Repository层CRUD问题
- 所有 Repo 子类仅调用 `super().__init__()`，无自定义查询方法
- Service 层完全绕过自定义 Repo，直接使用 `BaseRepository(session, Model)`

---

## 3. 采集器 (collector) — 评分: 5/10

### 3.1 模型完整性

**已有:** Collector, CollectionJob, CollectionResult ✅

**缺失:**
- `CollectionLog` 模型 — 设计文档列出 `collection_logs` 表
- 采集器心跳/健康状态字段
- `BaseCollector` ABC 未实现

### 3.2 API端点完整性

| 设计要求 | 状态 |
|---------|------|
| GET /api/v1/collectors | ✅ |
| GET /api/v1/collectors/{id}/health | ❌ **缺失** |
| GET /api/v1/collection-jobs | ✅ |
| POST /api/v1/collection-jobs | ✅ |
| POST /api/v1/collection-jobs/{id}/execute | ❌ **缺失** |
| GET /api/v1/collection-results | ❌ **缺失** |
| GET /api/v1/collection-results/{id} | ❌ **缺失** |

### 3.3 业务逻辑完整性
- ✅ 采集器注册、任务创建、结果记录
- ❌ 实际采集执行引擎
- ❌ 采集器健康检查/心跳
- ❌ 手动触发执行
- ❌ 调度管理 (cron/interval)
- ❌ 采集失败分类处理

### 3.4 代码质量问题
1. **分页计数BUG**: `service.py:46` `list_jobs` 的 total_count 未包含 asset_id 过滤条件
2. **无分页**: `list_collectors` 返回全部记录无分页
3. **缺少模型引用**: `repository.py` 使用未导入的模型类名

### 3.5 Repository层CRUD问题
- 所有Repo无自定义方法，完全依赖BaseRepository

---

## 4. 状态中心 (state) — 评分: 7/10

### 4.1 模型完整性

**已有:** StateSnapshot, StateChange ✅

**缺失:**
- Redis缓存层 — 设计要求"最新状态存Redis"
- 状态恢复验证逻辑

### 4.2 API端点完整性

| 设计要求 | 状态 |
|---------|------|
| GET /api/v1/states/{asset_id} | ✅ (路径 /states/latest/{asset_id}) |
| GET /api/v1/states/{asset_id}/history | ❌ **缺失** |
| GET /api/v1/state-changes | ✅ |
| POST /states/snapshots | ✅ (额外端点) |

### 4.3 业务逻辑完整性
- ✅ 快照记录 + 状态变更自动检测
- ✅ 获取最新状态(按类型去重)
- ✅ 变更列表查询
- ❌ 状态历史查询 (时间范围)
- ❌ Redis缓存集成
- ❌ 状态恢复验证 (连续2次正常才恢复)
- ❌ 状态恢复时自动关闭告警

### 4.4 代码质量问题
1. **性能问题**: `get_latest_states` 加载资产所有快照后在Python去重，应用SQL `DISTINCT ON` 或子查询
2. **路径不一致**: 设计用 `/states/{asset_id}`，代码用 `/states/latest/{asset_id}`

### 4.5 Repository层CRUD问题
- 无自定义方法，但通过Service层SQL直接查询

---

## 5. 事件中心 (event) — 评分: 5/10

### 5.1 模型完整性

**已有:** Event ✅ (event_type, source, source_id, asset_id, title, detail, raw_data, severity, fingerprint, is_deduplicated)

**缺失:**
- 无独立去重表
- 事件关联模型缺失

### 5.2 API端点完整性

| 设计要求 | 状态 |
|---------|------|
| GET /api/v1/events | ✅ |
| GET /api/v1/events/{id} | ✅ |

> 注: 事件创建为内部接口，非REST API

### 5.3 业务逻辑完整性
- ✅ 事件创建 + fingerprint 生成
- ✅ 事件列表查询 + 过滤
- ❌ **去重未实现**: 生成fingerprint但不检查是否已存在相同fingerprint的事件
- ❌ **事件关联**: 基于asset+时间窗口的关联未实现
- ❌ **事件分类**: 未实现自动分类
- ❌ **事件路由**: 未实现到alert/policy/ticket的路由

### 5.4 代码质量问题
1. **去重名存实亡**: `service.py:23-25` 生成fingerprint后 `kwargs.setdefault('fingerprint', fingerprint)` 但从不检查重复
2. **is_deduplicated 字段从未被设为True**

### 5.5 Repository层CRUD问题
- 最简实现，无自定义方法

---

## 6. 告警中心 (alert) — 评分: 5/10

### 6.1 模型完整性

**已有:** AlertRule, Alert ✅

**缺失:**
- 告警状态机不完整: 设计要求 `firing → acknowledged → investigating → resolved → closed + suppressed/escalated`，模型只支持 `firing/acknowledged/resolved/suppressed`
- 缺 `investigating`, `closed`, `escalated` 状态

### 6.2 API端点完整性

| 设计要求 | 状态 |
|---------|------|
| GET /api/v1/alerts | ✅ |
| GET /api/v1/alerts/{id} | ✅ |
| POST /api/v1/alerts/{id}/acknowledge | ✅ |
| POST /api/v1/alerts/{id}/resolve | ✅ |
| POST /api/v1/alerts/{id}/suppress | ❌ **缺失** |
| POST /api/v1/alerts/{id}/escalate | ❌ **缺失** |
| POST /api/v1/alerts/{id}/create-ticket | ❌ **缺失** |
| GET /api/v1/alert-rules | ✅ |
| POST /api/v1/alert-rules | ✅ |
| PUT /api/v1/alert-rules/{id} | ❌ **缺失** |
| GET /api/v1/alerts/stats | ✅ (路径 /alerts/stats/overview) |

### 6.3 业务逻辑完整性
- ✅ 规则CRUD、告警CRUD、确认、解决
- ❌ 告警规则引擎 (从事件自动生成告警)
- ❌ 告警收敛 (去重/压缩/抑制/静默/延迟)
- ❌ 告警升级 (按时间自动升级)
- ❌ 告警上下文关联 (资产/指标/日志)
- ❌ 告警转工单

### 6.4 代码质量问题
1. **路由冲突BUG**: `api.py:45` `GET /{alert_id}` 定义在 `api.py:72` `GET /stats/overview` 之前，FastAPI会先匹配 `/{alert_id}` 导致 `/stats/overview` 永远不可达 (alert_id="stats" 会404)
2. **重复的get_alert检查**: `service.py:68` acknowledge/resolve 各自独立get_by_id + 检查，应复用 `get_alert()`

### 6.5 Repository层CRUD问题
- 无自定义方法

---

## 7. 策略中心 (policy) — 评分: 5/10

### 7.1 模型完整性

**已有:** Policy, PolicyExecution ✅

**缺失:**
- `PolicyVersion` 模型 — 设计要求独立的版本表
- 策略状态不完整: 设计要求 `draft → testing → active → inactive → archived`，代码只有 `draft/active/disabled`

### 7.2 API端点完整性

| 设计要求 | 状态 |
|---------|------|
| GET /api/v1/policies | ✅ |
| POST /api/v1/policies | ✅ |
| GET /api/v1/policies/{id} | ✅ |
| PUT /api/v1/policies/{id} | ✅ |
| DELETE /api/v1/policies/{id} | ✅ (实际是禁用) |
| GET /api/v1/policies/{id}/versions | ❌ **缺失** |
| POST /api/v1/policies/{id}/publish | ❌ **缺失** |
| POST /api/v1/policies/{id}/simulate | ✅ |
| GET /api/v1/policies/{id}/history | ❌ **缺失** |
| POST /api/v1/policies/conflict-check | ❌ **缺失** |

### 7.3 业务逻辑完整性
- ✅ 策略CRUD + 简单模拟
- ❌ 策略发布工作流 (draft → testing → active)
- ❌ 策略匹配引擎 (核心功能)
- ❌ 冲突检测
- ❌ 风险评估
- ❌ 命中解释
- ❌ 策略版本管理

### 7.4 代码质量问题
1. **模拟过于简化**: `service.py:63-80` simulate 仅检查 event_type 字符串匹配，不评估 asset_scope/exclusion
2. **删除≠禁用**: `delete_policy` 实际设 `status="disabled"` 但API返回"策略已禁用"，语义混乱
3. **版本号无条件递增**: `update_policy` 每次更新都 version+1，即使只改描述

### 7.5 Repository层CRUD问题
- 无自定义方法

---

## 8. 自动化执行中心 (automation) — 评分: 5/10

### 8.1 模型完整性

**已有:** Script, Playbook, Execution, ExecutionStep ✅ (模型设计较完善)

### 8.2 API端点完整性

| 设计要求 | 状态 |
|---------|------|
| GET /api/v1/scripts | ✅ |
| POST /api/v1/scripts | ✅ |
| GET /api/v1/scripts/{id} | ❌ **缺失** |
| PUT /api/v1/scripts/{id} | ❌ **缺失** |
| GET /api/v1/playbooks | ✅ |
| POST /api/v1/playbooks | ✅ |
| GET /api/v1/playbooks/{id} | ❌ **缺失** |
| PUT /api/v1/playbooks/{id} | ❌ **缺失** |
| POST /api/v1/executions | ✅ |
| GET /api/v1/executions | ✅ |
| GET /api/v1/executions/{id} | ✅ |
| POST /api/v1/executions/{id}/dry-run | ❌ **缺失** |
| POST /api/v1/executions/{id}/approve | ✅ |
| POST /api/v1/executions/{id}/reject | ❌ **缺失** |
| POST /api/v1/executions/{id}/cancel | ❌ **缺失** |
| POST /api/v1/executions/{id}/rollback | ❌ **缺失** |
| GET /api/v1/executions/{id}/logs | ❌ **缺失** |
| WS /ws/executions/{id}/logs | ❌ **缺失** |

### 8.3 业务逻辑完整性
- ✅ 脚本/Playbook CRUD、执行创建、审批
- ✅ 高危命令检测 (基础)
- ❌ 实际执行引擎 (SSH/WinRM等)
- ❌ Playbook 步骤执行
- ❌ Reject/Cancel/Rollback
- ❌ WebSocket 实时日志
- ❌ Redis 分布式锁
- ❌ 影响面控制/灰度执行
- ❌ 审批超时自动取消

### 8.4 代码质量问题
1. **黑名单不完整**: `service.py:17` BLOCKED_COMMANDS 只有5项，设计文档列出至少10项 (缺 DROP DATABASE, DELETE FROM 无WHERE, UPDATE 无WHERE, shutdown, reboot, halt, format c:)
2. **分页计数BUG**: `list_scripts` 的 total_count 未应用 script_type 过滤 (L53-55)
3. **分页计数BUG**: `list_executions` 的 total_count 未应用 status 过滤 (L147-149)

### 8.5 Repository层CRUD问题
- 无自定义方法

---

## 9. 日志与可观测中心 (log) — 评分: 3/10 🔴

### 9.1 模型完整性

**已有:** ExecutionLog ✅ (仅一个模型)

**缺失:**
- `AuditLog` 模型 — 设计核心要求
- `PlatformLog` 模型
- `AIToolCallLog` 模型

### 9.2 API端点完整性

| 设计要求 | 状态 |
|---------|------|
| GET /api/v1/execution-logs | ✅ (路径 /logs/execution/{id}) |
| GET /api/v1/execution-logs/stream | ❌ **缺失** (WebSocket) |
| GET /api/v1/audit-logs | ❌ **缺失** |
| GET /api/v1/audit-logs/export | ❌ **缺失** |
| GET /api/v1/platform/status | ❌ **缺失** |
| GET /metrics | ❌ **缺失** |

### 9.3 业务逻辑完整性
- ✅ 执行日志追加和查询
- ❌ **service.py 文件不存在** — 服务逻辑直接写在 api.py 中
- ❌ 审计日志系统
- ❌ 平台状态检查
- ❌ Prometheus 指标
- ❌ 日志搜索 (关键字/级别)
- ❌ 日志脱敏
- ❌ OpenTelemetry 集成

### 9.4 代码质量问题
1. **严重: service.py 缺失** — 违反分层架构，服务逻辑混在 api.py 中
2. **Schema不匹配模型**: `schemas.py` ExecutionLogResponse 有 `step_name/level/message/output`，而模型有 `step_id/stream_type/content/offset` — 字段完全不对应
3. **架构违反**: api.py 直接包含 LogService 类定义

### 9.5 Repository层CRUD问题
- 无自定义方法

---

## 10. AIops 智能运维 (aiops) — 评分: 7/10

### 10.1 模型完整性

**已有:** AIAnalysis ✅

### 10.2 API端点完整性

| 设计要求 | 状态 |
|---------|------|
| POST /api/v1/aiops/analyze | ✅ (路径 /aiops/analyses) |
| GET /api/v1/aiops/analysis/{id} | ✅ |
| GET /api/v1/aiops/analysis | ✅ |
| POST /api/v1/aiops/analysis/{id}/feedback | ✅ |
| GET /aiops/health | ✅ (额外端点，有益) |
| POST /aiops/diagnose | ✅ (额外端点，有益) |

### 10.3 业务逻辑完整性
- ✅ LLM集成 (OpenAI兼容接口)
- ✅ 分析记录管理
- ✅ 反馈机制
- ✅ 优雅降级 (模型不可用时)
- ✅ 健康检查
- ✅ 快捷诊断
- ❌ **上下文构建严重不足**: `_build_context` 仅传递 alert_id/asset_ids，未获取实际数据 (设计要求10+数据源)
- ❌ Prompt模板管理
- ❌ Token预算管理
- ❌ 模型降级链 (主→备→降级)

### 10.4 代码质量问题
1. **上下文构建空壳**: `service.py:66-72` `_build_context` 仅返回 `{analysis_type, alert_id, asset_ids}`，未实际查询数据库获取资产信息、状态、指标等
2. **JSON解析脆弱**: `service.py:106-111` 用 `content.find("{")` / `rfind("}")` 提取JSON，LLM返回多JSON时会截断
3. **配置访问模式脆弱**: `service.py:39` `getattr(config, 'model_name', getattr(config, 'llm_model', 'default'))` 链式fallback不清晰
4. **diagnose过长**: `service.py:171-269` 近100行方法，应拆分

### 10.5 Repository层CRUD问题
- 无自定义方法

---

## 11. 知识中心 (knowledge) — 评分: 6/10

### 11.1 模型完整性

**已有:** KnowledgeArticle ✅

**缺失:**
- `KnowledgeFeedback` 模型 — 设计要求
- 向量嵌入存储 (Qdrant/Chroma集成)

### 11.2 API端点完整性

| 设计要求 | 状态 |
|---------|------|
| GET /api/v1/knowledge | ✅ |
| POST /api/v1/knowledge | ✅ |
| GET /api/v1/knowledge/{id} | ✅ |
| PUT /api/v1/knowledge/{id} | ✅ |
| POST /api/v1/knowledge/{id}/publish | ✅ |
| POST /api/v1/knowledge/search | ❌ **缺失** (向量搜索) |
| POST /api/v1/knowledge/import | ❌ **缺失** |

### 11.3 业务逻辑完整性
- ✅ 文章CRUD + 发布
- ❌ **向量搜索 (RAG)** — 设计核心功能
- ❌ 批量导入
- ❌ 知识反馈
- ❌ 自动关联策略/Playbook
- ❌ 知识沉淀循环 (工单→知识草稿)

### 11.4 代码质量问题
- 整体代码质量较好
- 无明显bug

### 11.5 Repository层CRUD问题
- 无自定义方法

---

## 12. 工单中心 (ticket) — 评分: 5/10

### 12.1 模型完整性

**已有:** Ticket, TicketComment ✅

### 12.2 API端点完整性

| 设计要求 | 状态 |
|---------|------|
| GET /api/v1/tickets | ✅ |
| POST /api/v1/tickets | ✅ |
| GET /api/v1/tickets/{id} | ✅ |
| PUT /api/v1/tickets/{id} | ✅ |
| POST /api/v1/tickets/{id}/assign | ❌ **缺失** (可PUT但无语义端点) |
| POST /api/v1/tickets/{id}/comments | ✅ |
| GET /api/v1/tickets/{id}/comments | ✅ |
| POST /api/v1/tickets/{id}/resolve | ❌ **缺失** |
| POST /api/v1/tickets/{id}/close | ❌ **缺失** |
| POST /api/v1/tickets/{id}/create-knowledge | ❌ **缺失** |
| GET /api/v1/tickets/{id}/timeline | ❌ **缺失** |

### 12.3 业务逻辑完整性
- ✅ 工单CRUD + 评论
- ❌ 状态机校验 (任意状态可转为任意状态)
- ❌ SLA自动计算 (根据优先级设置截止时间)
- ❌ 指派工作流
- ❌ 解决/关闭独立端点
- ❌ 知识草稿生成
- ❌ 工单时间线
- ❌ 关联告警/执行/AI分析

### 12.4 代码质量问题
1. **硬编码user_id**: `api.py:50` `add_comment` 写死 `user_id="system"`，未从认证上下文获取
2. **无状态转换校验**: `service.py:62` 直接允许 `status` 字段任意变更，如从 open 直接到 closed

### 12.5 Repository层CRUD问题
- 无自定义方法

---

## 13. 治理中心 (governance) — 评分: 6/10

### 13.1 模型完整性

**已有:** User, Role, UserRole, ApiKey ✅

**缺失:**
- `AuditLog` 模型 — 全平台审计核心
- `SystemConfig` 模型 — 系统配置管理

### 13.2 API端点完整性

| 设计要求 | 状态 |
|---------|------|
| POST /api/v1/auth/login | ✅ |
| POST /api/v1/auth/logout | ✅ (空实现) |
| POST /api/v1/auth/refresh | ✅ |
| GET /api/v1/auth/me | ✅ |
| PUT /api/v1/auth/password | ✅ |
| GET /api/v1/users | ✅ |
| POST /api/v1/users | ✅ |
| PUT /api/v1/users/{id} | ✅ |
| DELETE /api/v1/users/{id} | ✅ |
| GET /api/v1/roles | ✅ |
| POST /api/v1/roles | ✅ |
| PUT /api/v1/roles/{id} | ❌ **缺失** |
| GET /api/v1/api-keys | ✅ |
| POST /api/v1/api-keys | ✅ |
| DELETE /api/v1/api-keys/{id} | ✅ |
| GET /api/v1/audit-logs | ❌ **缺失** |
| GET /api/v1/audit-logs/export | ❌ **缺失** |
| GET /api/v1/platform/status | ❌ **缺失** |
| GET /api/v1/platform/config | ❌ **缺失** |
| PUT /api/v1/platform/config | ❌ **缺失** |
| POST /api/v1/platform/backup | ❌ **缺失** |
| POST /api/v1/platform/self-check | ❌ **缺失** |

### 13.3 业务逻辑完整性
- ✅ 认证 (login/refresh/me/password)
- ✅ 用户管理 (CRUD + 软删除 + 角色分配)
- ✅ API Key管理 (创建/撤销 + SHA256哈希)
- ❌ 角色更新
- ❌ 审计日志系统 (全平台核心功能)
- ❌ 系统配置管理
- ❌ 平台健康监控
- ❌ 备份管理
- ❌ 自检

### 13.4 代码质量问题
1. **认证token通过查询参数传递**: `api.py:64,147,158,168` change_password/list_api_keys/create_api_key/revoke_api_key 都通过 `token` 参数而非 Authorization header，不安全 (token出现在URL和日志中)
2. **错误码占位符**: `exceptions.py:27-29` `UNAUTHORIZED="***"`, `TOKEN_EXPIRED="***"`, `TOKEN_INVALID="***"` 使用占位符
3. **Role API绕过Service**: `api.py:114-142` 角色列表/创建直接操作数据库，未通过RoleService
4. **logout空实现**: `api.py:41-42` 仅返回成功消息，无实际token失效逻辑
5. **soft_delete用utcnow**: `repository.py:109` 使用 `datetime.utcnow()` (Python 3.12已弃用)，应使用 `datetime.now(timezone.utc)`

### 13.5 Repository层CRUD问题
- BaseRepository.get_multi 默认 order_by `self.model.created_at.desc()` — UserRole 和 ApiKey 等关联表没有 `created_at` 字段会报错

---

## 全局共性问题汇总

### 跨领域问题

| # | 问题 | 涉及领域 |
|---|------|---------|
| G1 | **所有Repository子类为空壳** — 仅调用super().__init__()，无自定义查询，Service层直接用BaseRepository | 全部13个 |
| G2 | **分页计数查询不与过滤条件同步** — list_xxx方法的total_count独立查询，未应用过滤条件 | config, collector, automation |
| G3 | **事件驱动未实现** — 设计文档大量领域事件 (Created/Updated/Deleted等)，代码中完全没有事件发布/订阅机制 | 全部 |
| G4 | **跨领域调用未实现** — 设计文档描述的领域间交互 (如 alert→ticket, policy→automation) 均为空 | 全部 |
| G5 | **认证/鉴权中间件缺失** — 除了governance的login/me外，其他所有API端点均无权限校验 | 全部 |
| G6 | **BaseRepository参数顺序双模式** — 支持 `(session, Model)` 和 `(Model, session)` 两种顺序，易混淆 | 全部 |
| G7 | **model_to_dict vs Pydantic Response** — 部分领域手动dict转换 (asset)，部分用model_to_dict，部分用Pydantic model_validate，不统一 | 全部 |

### 严重BUG清单

| # | 文件 | 行号 | 严重度 | 描述 |
|---|------|------|--------|------|
| B1 | alert/api.py | 45 vs 72 | **高** | `/{alert_id}` 路由在 `/stats/overview` 之前，stats端点永远不可达 |
| B2 | collector/service.py | 46 | **中** | list_jobs分页计数不包含asset_id过滤 |
| B3 | config/service.py | 43-46 | **中** | list_definitions分页计数不包含config_type过滤 |
| B4 | config/service.py | 115-118 | **中** | list_credentials分页计数不包含cred_type过滤 |
| B5 | automation/service.py | 53-56 | **中** | list_scripts分页计数不包含script_type过滤 |
| B6 | automation/service.py | 147-149 | **中** | list_executions分页计数不包含status过滤 |
| B7 | event/service.py | 23-28 | **中** | 去重fingerprint生成但不检查重复，is_deduplicated永远False |
| B8 | asset/repository.py | 38-43 | **中** | search方法的ilike未转义用户输入中的%和_ |
| B9 | ticket/api.py | 50 | **低** | add_comment硬编码user_id="system" |
| B10 | governance/api.py | 64,147,158 | **高** | token通过URL参数传递，暴露在日志和浏览器历史中 |
| B11 | log/service.py | 不存在 | **高** | 文件缺失，服务逻辑混入api.py |
| B12 | log/schemas.py | 全文件 | **中** | Schema字段与Model字段完全不对应 |

---

## 改进优先级建议

### P0 - 必须立即修复 (阻塞功能)
1. 修复 alert `stats/overview` 路由冲突 (B1)
2. 创建 log/service.py，分离服务与API (B11)
3. 修复所有分页计数与过滤条件不同步的BUG (B2-B6)
4. 修复 governance token传递方式 (B10)

### P1 - 核心功能缺失
5. 实现事件去重/关联/路由引擎 (event)
6. 实现告警规则引擎：事件→告警自动生成 (alert)
7. 实现策略匹配引擎：告警→策略匹配 (policy)
8. 实现AIops上下文构建：真正查询多源数据 (aiops)
9. 实现审计日志系统 (governance/log)

### P2 - 完善功能
10. 采集器执行引擎 + 健康检查 (collector)
11. 自动化执行引擎 (automation)
12. 知识库向量搜索 RAG (knowledge)
13. 工单SLA + 知识沉淀 (ticket)
14. 配置漂移检测 + 回滚 (config)

### P3 - 代码质量
15. 统一响应序列化方式
16. Repository子类添加自定义查询方法
17. 全局事件发布/订阅机制
18. API认证中间件