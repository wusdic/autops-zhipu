# AUTOPS 数据架构设计

> 文档状态：current
> 是否为事实源：yes
> 建议路径：`docs/01-architecture/DATA_ARCHITECTURE.md`

---

## 1. 存储分工

| 数据类型 | 存储组件 | 说明 |
|---|---|---|
| 资产、配置、策略、工单、用户、审批 | MySQL/MariaDB | 核心业务数据 |
| 高频指标 | VictoriaMetrics/Prometheus | 时序数据 |
| 最新状态、锁、会话、轻量队列 | Redis | 实时能力 |
| 执行日志索引、审计索引 | 关系库 | 可查询和关联 |
| 大体量日志内容 | 文件/对象存储 | 第一阶段降低复杂度 |
| 附件、报告、归档 | MinIO/S3 | 大文件 |
| 知识向量 | Qdrant/Chroma | RAG 检索 |

---

## 2. 公共字段约定

所有表包含以下公共字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | VARCHAR(36) PK | UUID4，主键 |
| created_at | DATETIME(6) | 创建时间，默认 CURRENT_TIMESTAMP |
| updated_at | DATETIME(6) | 更新时间，ON UPDATE CURRENT_TIMESTAMP |
| created_by | VARCHAR(36) | 创建人 user_id |
| updated_by | VARCHAR(36) | 更新人 user_id |
| is_deleted | TINYINT(1) | 软删除标记，默认 0 |

---

## 3. 核心表设计（共 32 张）

### 3.1 资产中心（5 张）

#### assets — 资产主表

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| name | VARCHAR(255) | NOT NULL | 资产名称 |
| asset_type | VARCHAR(50) | NOT NULL | 资产类型枚举 |
| asset_category | VARCHAR(50) | NOT NULL | 分类：host/network/database/middleware/service/container/cloud/other |
| description | TEXT | | 描述 |
| status | VARCHAR(20) | NOT NULL DEFAULT 'active' | active/inactive/maintenance/decommissioned |
| health_status | VARCHAR(20) | DEFAULT 'unknown' | healthy/warning/critical/unknown |
| reachability | VARCHAR(20) | DEFAULT 'unknown' | reachable/unreachable/unknown |
| management_ip | VARCHAR(45) | | 管理IP |
| os_type | VARCHAR(50) | | 操作系统类型 |
| os_version | VARCHAR(100) | | 操作系统版本 |
| vendor | VARCHAR(100) | | 厂商 |
| model | VARCHAR(100) | | 型号 |
| location | VARCHAR(255) | | 物理位置 |
| business_system | VARCHAR(255) | | 所属业务系统 |
| environment | VARCHAR(50) | | 环境：production/staging/development/testing |
| custom_attributes | TEXT | | 扩展属性 JSON |
| last_collected_at | DATETIME | | 最后采集时间 |

#### asset_ips — 资产IP表

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| asset_id | VARCHAR(36) | FK -> assets.id | 所属资产 |
| ip_address | VARCHAR(45) | NOT NULL | IP地址（IPv4/IPv6） |
| ip_type | VARCHAR(20) | NOT NULL | management/business/cluster/floating |
| is_primary | TINYINT(1) | DEFAULT 0 | 是否主IP |
| port | INT | | 端口号 |
| network_segment | VARCHAR(100) | | 网段 |

#### asset_tags — 资产标签表

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| asset_id | VARCHAR(36) | FK -> assets.id | 资产 |
| tag_key | VARCHAR(100) | NOT NULL | 标签键 |
| tag_value | VARCHAR(255) | | 标签值 |

#### asset_groups — 资产分组表

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| name | VARCHAR(255) | NOT NULL UNIQUE | 分组名称 |
| parent_id | VARCHAR(36) | FK -> asset_groups.id | 父分组 |
| description | TEXT | | 描述 |
| group_type | VARCHAR(50) | NOT NULL | static/dynamic |
| filter_rule | TEXT | | 动态分组过滤规则 JSON |

#### asset_group_members — 资产分组成员

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| group_id | VARCHAR(36) | FK -> asset_groups.id | 分组 |
| asset_id | VARCHAR(36) | FK -> assets.id | 资产 |

---

### 3.2 资产关系（1 张）

#### asset_relations — 资产关系表

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| source_asset_id | VARCHAR(36) | FK -> assets.id | 源资产 |
| target_asset_id | VARCHAR(36) | FK -> assets.id | 目标资产 |
| relation_type | VARCHAR(50) | NOT NULL | depends_on/contains/runs_on/connects_to/provides |
| description | VARCHAR(500) | | 关系描述 |

---

### 3.3 配置中心（5 张）

#### config_definitions — 配置定义

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| key | VARCHAR(255) | NOT NULL UNIQUE | 配置键 |
| name | VARCHAR(255) | NOT NULL | 配置名称 |
| category | VARCHAR(50) | NOT NULL | collection/threshold/notification/policy/script/ai_template |
| value_type | VARCHAR(20) | NOT NULL | string/integer/float/boolean/json/yaml |
| default_value | TEXT | | 默认值 |
| description | TEXT | | 说明 |
| is_required | TINYINT(1) | DEFAULT 0 | 是否必填 |
| validation_rule | TEXT | | 验证规则 JSON |
| scope | VARCHAR(20) | DEFAULT 'global' | global/organization/business_system/asset_group/asset |

#### config_versions — 配置版本

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| definition_id | VARCHAR(36) | FK -> config_definitions.id | 配置定义 |
| version | INT | NOT NULL | 版本号，自增 |
| value | TEXT | NOT NULL | 配置值 |
| change_reason | TEXT | | 变更原因 |
| status | VARCHAR(20) | DEFAULT 'draft' | draft/published/archived |

#### config_bindings — 配置绑定

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| version_id | VARCHAR(36) | FK -> config_versions.id | 配置版本 |
| target_type | VARCHAR(50) | NOT NULL | asset/asset_group/business_system/global |
| target_id | VARCHAR(36) | | 绑定目标ID |
| priority | INT | DEFAULT 0 | 优先级，数字越大越优先 |

#### config_drifts — 配置漂移

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| binding_id | VARCHAR(36) | FK -> config_bindings.id | 配置绑定 |
| expected_value | TEXT | | 期望值 |
| actual_value | TEXT | | 实际值 |
| detected_at | DATETIME | NOT NULL | 检测时间 |
| status | VARCHAR(20) | DEFAULT 'open' | open/acknowledged/resolved |

#### change_records — 变更记录

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| change_type | VARCHAR(50) | NOT NULL | config/credential/policy/asset |
| target_id | VARCHAR(36) | | 变更目标ID |
| old_value | TEXT | | 变更前值 |
| new_value | TEXT | | 变更后值 |
| change_reason | TEXT | | 变更原因 |
| approved_by | VARCHAR(36) | | 审批人 |
| change_status | VARCHAR(20) | DEFAULT 'pending' | pending/approved/rejected/rolled_back |

---

### 3.4 凭证中心（2 张）

#### credentials — 凭证表

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| name | VARCHAR(255) | NOT NULL | 凭证名称 |
| credential_type | VARCHAR(50) | NOT NULL | ssh_key/ssh_password/windows/snmp/database/api_token/custom |
| encrypted_data | TEXT | NOT NULL | AES-256-GCM 加密后的凭证数据 |
| encryption_key_id | VARCHAR(36) | NOT NULL | 使用的密钥ID |
| description | TEXT | | 描述 |
| expires_at | DATETIME | | 过期时间 |
| last_tested_at | DATETIME | | 最后测试时间 |
| last_test_result | VARCHAR(20) | | success/failed/unknown |

#### credential_bindings — 凭证绑定

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| credential_id | VARCHAR(36) | FK -> credentials.id | 凭证 |
| target_type | VARCHAR(50) | NOT NULL | asset/asset_group |
| target_id | VARCHAR(36) | | 目标ID |
| usage_count | INT | DEFAULT 0 | 使用次数 |
| last_used_at | DATETIME | | 最后使用时间 |

---

### 3.5 采集中心（4 张）

#### collector_instances — 采集器实例

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| name | VARCHAR(255) | NOT NULL | 采集器名称 |
| collector_type | VARCHAR(50) | NOT NULL | ssh/winrm/http_tcp/database/snmp/certificate |
| version | VARCHAR(50) | | 版本 |
| capabilities | TEXT | | 能力声明 JSON |
| status | VARCHAR(20) | DEFAULT 'active' | active/inactive/error |
| last_heartbeat | DATETIME | | 最后心跳时间 |
| config | TEXT | | 采集器配置 JSON |

#### collection_jobs — 采集任务

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| name | VARCHAR(255) | | 任务名称 |
| collector_id | VARCHAR(36) | FK -> collector_instances.id | 采集器 |
| asset_id | VARCHAR(36) | FK -> assets.id | 目标资产 |
| credential_id | VARCHAR(36) | FK -> credentials.id | 使用凭证 |
| config_version_id | VARCHAR(36) | FK -> config_versions.id | 采集配置版本 |
| schedule_type | VARCHAR(20) | NOT NULL | manual/cron/interval/event |
| schedule_expression | VARCHAR(255) | | cron表达式或间隔秒数 |
| status | VARCHAR(20) | DEFAULT 'active' | active/paused/disabled |
| timeout_seconds | INT | DEFAULT 300 | 超时时间 |
| retry_count | INT | DEFAULT 0 | 重试次数 |
| max_retries | INT | DEFAULT 3 | 最大重试 |

#### collection_results — 采集结果

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| job_id | VARCHAR(36) | FK -> collection_jobs.id | 采集任务 |
| asset_id | VARCHAR(36) | NOT NULL | 资产ID |
| status | VARCHAR(20) | NOT NULL | success/failed/partial/timeout |
| metrics | TEXT | | 指标数据 JSON |
| facts | TEXT | | 配置事实 JSON |
| errors | TEXT | | 错误信息 JSON |
| started_at | DATETIME | | 开始时间 |
| finished_at | DATETIME | | 结束时间 |
| duration_ms | INT | | 耗时毫秒 |
| trace_id | VARCHAR(36) | | 链路追踪ID |

#### collection_logs — 采集日志

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| result_id | VARCHAR(36) | FK -> collection_results.id | 采集结果 |
| log_level | VARCHAR(10) | NOT NULL | DEBUG/INFO/WARNING/ERROR |
| message | TEXT | NOT NULL | 日志内容 |
| logged_at | DATETIME | NOT NULL | 日志时间 |

---

### 3.6 状态中心（2 张）

#### state_snapshots — 状态快照

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| asset_id | VARCHAR(36) | FK -> assets.id | 资产 |
| state_type | VARCHAR(50) | NOT NULL | reachability/service/disk/cpu/memory/network/port/process/certificate |
| state_value | TEXT | NOT NULL | 状态值 JSON |
| state_status | VARCHAR(20) | NOT NULL | normal/warning/critical/unknown |
| collected_at | DATETIME | NOT NULL | 采集时间 |
| source | VARCHAR(50) | | 数据来源（collection/manual/import） |

#### state_changes — 状态变更

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| asset_id | VARCHAR(36) | FK -> assets.id | 资产 |
| state_type | VARCHAR(50) | NOT NULL | 状态类型 |
| old_status | VARCHAR(20) | | 变更前状态 |
| new_status | VARCHAR(20) | NOT NULL | 变更后状态 |
| old_value | TEXT | | 变更前值 |
| new_value | TEXT | | 变更后值 |
| changed_at | DATETIME | NOT NULL | 变更时间 |
| event_id | VARCHAR(36) | | 关联事件ID |

---

### 3.7 事件中心（1 张）

#### events — 事件表

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| event_type | VARCHAR(100) | NOT NULL | 事件类型 |
| source | VARCHAR(50) | NOT NULL | 来源：collector/state/log/config/automation/aiops/platform |
| severity | VARCHAR(20) | NOT NULL | critical/warning/info/unknown |
| title | VARCHAR(500) | NOT NULL | 事件标题 |
| description | TEXT | | 事件描述 |
| asset_ids | TEXT | | 关联资产ID列表 JSON |
| raw_data | TEXT | | 原始数据 JSON |
| normalized_data | TEXT | | 标准化数据 JSON |
| dedup_key | VARCHAR(255) | | 去重键 |
| correlation_id | VARCHAR(36) | | 关联ID，用于事件关联 |
| occurred_at | DATETIME | NOT NULL | 发生时间 |
| processed_at | DATETIME | | 处理时间 |
| status | VARCHAR(20) | DEFAULT 'new' | new/processed/suppressed/closed |

---

### 3.8 告警中心（2 张）

#### alerts — 告警表

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| alert_rule_id | VARCHAR(36) | | 规则ID |
| title | VARCHAR(500) | NOT NULL | 告警标题 |
| description | TEXT | | 告警描述 |
| severity | VARCHAR(20) | NOT NULL | critical/high/medium/low/info |
| status | VARCHAR(20) | NOT NULL DEFAULT 'firing' | firing/acknowledged/resolved/suppressed/closed |
| asset_ids | TEXT | | 关联资产 JSON |
| event_ids | TEXT | | 关联事件 JSON |
| source_event_id | VARCHAR(36) | | 触发事件 |
| context | TEXT | | 告警上下文 JSON（指标、日志、配置等） |
| fingerprint | VARCHAR(255) | | 告警指纹（去重/收敛） |
| assigned_to | VARCHAR(36) | | 指派人 |
| acknowledged_by | VARCHAR(36) | | 确认人 |
| resolved_by | VARCHAR(36) | | 解决人 |
| fired_at | DATETIME | NOT NULL | 触发时间 |
| acknowledged_at | DATETIME | | 确认时间 |
| resolved_at | DATETIME | | 解决时间 |

#### alert_rules — 告警规则

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| name | VARCHAR(255) | NOT NULL | 规则名称 |
| description | TEXT | | 说明 |
| event_types | TEXT | | 匹配事件类型 JSON |
| conditions | TEXT | NOT NULL | 触发条件 JSON |
| severity_mapping | TEXT | | 严重度映射 JSON |
| asset_filter | TEXT | | 资产过滤 JSON |
| suppression_rules | TEXT | | 抑制规则 JSON |
| escalation_rules | TEXT | | 升级规则 JSON |
| notification_config | TEXT | | 通知配置 JSON |
| status | VARCHAR(20) | DEFAULT 'active' | active/inactive |
| cooldown_minutes | INT | DEFAULT 5 | 冷却时间 |

---

### 3.9 策略中心（2 张）

#### policies — 策略表

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| name | VARCHAR(255) | NOT NULL | 策略名称 |
| description | TEXT | | 说明 |
| trigger_type | VARCHAR(50) | NOT NULL | event/alert/schedule/manual |
| trigger_conditions | TEXT | NOT NULL | 触发条件 JSON |
| asset_scope | TEXT | | 适用资产范围 JSON |
| risk_level | VARCHAR(20) | NOT NULL | critical/high/medium/low |
| requires_approval | TINYINT(1) | DEFAULT 1 | 是否需要审批 |
| action_chain | TEXT | NOT NULL | 动作链 JSON |
| verification_conditions | TEXT | | 验证条件 JSON |
| failure_handling | TEXT | | 失败处理 JSON |
| rollback_actions | TEXT | | 回滚动作 JSON |
| exclusion_conditions | TEXT | | 排除条件 JSON |
| max_impact_scope | INT | | 最大影响资产数 |
| status | VARCHAR(20) | DEFAULT 'draft' | draft/active/inactive/archived |
| version | INT | DEFAULT 1 | 版本号 |

#### policy_versions — 策略版本

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| policy_id | VARCHAR(36) | FK -> policies.id | 策略 |
| version | INT | NOT NULL | 版本号 |
| content | TEXT | NOT NULL | 策略完整内容 JSON |
| change_reason | TEXT | | 变更原因 |
| published_at | DATETIME | | 发布时间 |
| published_by | VARCHAR(36) | | 发布人 |
| status | VARCHAR(20) | DEFAULT 'draft' | draft/published/archived |

---

### 3.10 自动化中心（4 张）

#### scripts — 脚本库

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| name | VARCHAR(255) | NOT NULL | 脚本名称 |
| script_type | VARCHAR(50) | NOT NULL | shell/powershell/python/sql/rest_api |
| content | TEXT | NOT NULL | 脚本内容 |
| description | TEXT | | 说明 |
| parameters | TEXT | | 参数定义 JSON |
| timeout_seconds | INT | DEFAULT 300 | 超时 |
| risk_level | VARCHAR(20) | DEFAULT 'low' | critical/high/medium/low |
| is_dangerous | TINYINT(1) | DEFAULT 0 | 是否高危 |
| version | INT | DEFAULT 1 | 版本 |

#### playbooks — Playbook

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| name | VARCHAR(255) | NOT NULL | 名称 |
| description | TEXT | | 说明 |
| steps | TEXT | NOT NULL | 步骤定义 JSON（脚本引用、参数、顺序、条件） |
| parameters | TEXT | | 参数定义 JSON |
| risk_level | VARCHAR(20) | DEFAULT 'low' | 风险等级 |
| requires_approval | TINYINT(1) | DEFAULT 1 | 需要审批 |
| version | INT | DEFAULT 1 | 版本 |

#### automation_executions — 自动化执行

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| trigger_source | VARCHAR(50) | NOT NULL | policy/manual/aiops/alert/schedule |
| trigger_id | VARCHAR(36) | | 触发源ID |
| playbook_id | VARCHAR(36) | FK -> playbooks.id | Playbook |
| script_id | VARCHAR(36) | FK -> scripts.id | 单脚本执行时使用 |
| target_asset_ids | TEXT | NOT NULL | 目标资产 JSON |
| parameters | TEXT | | 执行参数 JSON |
| status | VARCHAR(20) | NOT NULL DEFAULT 'created' | 状态机值 |
| risk_assessment | TEXT | | 风险评估 JSON |
| approval_id | VARCHAR(36) | | 审批ID |
| dry_run_result | TEXT | | dry-run 结果 JSON |
| started_at | DATETIME | | 开始时间 |
| finished_at | DATETIME | | 结束时间 |
| final_status | VARCHAR(20) | | success/failed/partial_success |
| trace_id | VARCHAR(36) | | 链路追踪ID |

#### automation_execution_steps — 执行步骤

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| execution_id | VARCHAR(36) | FK -> automation_executions.id | 所属执行 |
| step_index | INT | NOT NULL | 步骤序号 |
| script_id | VARCHAR(36) | | 脚本ID |
| target_asset_id | VARCHAR(36) | | 目标资产 |
| status | VARCHAR(20) | NOT NULL DEFAULT 'pending' | pending/running/success/failed/skipped |
| parameters | TEXT | | 实际参数 JSON |
| exit_code | INT | | 退出码 |
| started_at | DATETIME | | 开始时间 |
| finished_at | DATETIME | | 结束时间 |
| duration_ms | INT | | 耗时 |

---

### 3.11 日志中心（1 张）

#### execution_logs — 执行日志分片

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| execution_id | VARCHAR(36) | NOT NULL | 执行ID |
| step_id | VARCHAR(36) | | 步骤ID |
| asset_id | VARCHAR(36) | | 资产ID |
| stream_type | VARCHAR(10) | NOT NULL | stdout/stderr/system |
| log_content | TEXT | NOT NULL | 日志内容 |
| log_offset | BIGINT | NOT NULL | 偏移量（用于流式读取） |
| logged_at | DATETIME | NOT NULL | 日志时间 |
| storage_ref | VARCHAR(500) | | 外部存储引用（大日志） |

---

### 3.12 审计（1 张）

#### audit_logs — 审计日志

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| trace_id | VARCHAR(36) | NOT NULL | 链路追踪ID |
| user_id | VARCHAR(36) | | 操作人 |
| action | VARCHAR(100) | NOT NULL | 操作类型 |
| resource_type | VARCHAR(50) | NOT NULL | 资源类型 |
| resource_id | VARCHAR(36) | | 资源ID |
| detail | TEXT | | 操作详情 JSON |
| ip_address | VARCHAR(45) | | 来源IP |
| user_agent | VARCHAR(500) | | UA |
| status | VARCHAR(20) | NOT NULL | success/failed/denied |
| occurred_at | DATETIME | NOT NULL | 发生时间 |

---

### 3.13 工单中心（2 张）

#### tickets — 工单表

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| title | VARCHAR(500) | NOT NULL | 工单标题 |
| description | TEXT | | 描述 |
| ticket_type | VARCHAR(50) | NOT NULL | incident/change/task/knowledge_draft |
| priority | VARCHAR(20) | NOT NULL | critical/high/medium/low |
| status | VARCHAR(20) | NOT NULL DEFAULT 'open' | open/assigned/in_progress/pending_approval/resolved/closed |
| source | VARCHAR(50) | NOT NULL | manual/alert/automation/aiops |
| source_id | VARCHAR(36) | | 来源ID |
| assigned_to | VARCHAR(36) | | 指派人 |
| assigned_group | VARCHAR(100) | | 指派组 |
| reporter_id | VARCHAR(36) | | 报告人 |
| sla_deadline | DATETIME | | SLA截止时间 |
| alert_ids | TEXT | | 关联告警 JSON |
| execution_ids | TEXT | | 关联执行 JSON |
| ai_analysis_id | VARCHAR(36) | | 关联AI分析 |
| knowledge_draft_id | VARCHAR(36) | | 生成的知识草稿 |
| resolved_at | DATETIME | | 解决时间 |
| closed_at | DATETIME | | 关闭时间 |

#### ticket_comments — 工单评论

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| ticket_id | VARCHAR(36) | FK -> tickets.id | 工单 |
| user_id | VARCHAR(36) | NOT NULL | 评论人 |
| content | TEXT | NOT NULL | 评论内容 |
| comment_type | VARCHAR(20) | DEFAULT 'comment' | comment/status_change/approval/rejection/summary |
| attachments | TEXT | | 附件 JSON |

---

### 3.14 AIops（1 张）

#### ai_analysis_records — AI 分析记录

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| trigger_source | VARCHAR(50) | NOT NULL | alert/manual/ticket |
| trigger_id | VARCHAR(36) | | 触发源ID |
| context | TEXT | | 输入上下文 JSON |
| analysis_result | TEXT | | AI 分析结果 JSON |
| model_name | VARCHAR(100) | | 使用的模型 |
| prompt_template | VARCHAR(100) | | 使用的 Prompt 模板 |
| tool_calls | TEXT | | 工具调用记录 JSON |
| token_usage | TEXT | | Token 用量 JSON |
| duration_ms | INT | | 耗时 |
| status | VARCHAR(20) | NOT NULL | success/failed/timeout/unavailable |
| user_feedback | VARCHAR(20) | | helpful/unhelpful/partial |
| started_at | DATETIME | | 开始时间 |
| finished_at | DATETIME | | 结束时间 |

---

### 3.15 知识中心（2 张）

#### knowledge_articles — 知识文章

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| title | VARCHAR(500) | NOT NULL | 标题 |
| article_type | VARCHAR(50) | NOT NULL | standard_solution/case_study/best_practice/draft |
| status | VARCHAR(20) | NOT NULL DEFAULT 'draft' | draft/published/archived |
| content | TEXT | NOT NULL | 文章内容 |
| applicable_asset_types | TEXT | | 适用资产类型 JSON |
| trigger_events | TEXT | | 触发事件 JSON |
| diagnosis_steps | TEXT | | 诊断步骤 JSON |
| action_steps | TEXT | | 处置步骤 JSON |
| verification_steps | TEXT | | 验证步骤 JSON |
| risk_level | VARCHAR(20) | | 风险等级 |
| requires_approval | TINYINT(1) | | 是否需要审批 |
| related_policy_id | VARCHAR(36) | | 关联策略 |
| related_playbook_id | VARCHAR(36) | | 关联 Playbook |
| source | VARCHAR(50) | | 来源：standard/import/ticket_draft/ai_draft |
| vector_id | VARCHAR(100) | | 向量索引ID |
| view_count | INT | DEFAULT 0 | 浏览次数 |
| helpful_count | INT | DEFAULT 0 | 有用次数 |
| published_at | DATETIME | | 发布时间 |
| published_by | VARCHAR(36) | | 发布人 |

#### knowledge_feedback — 知识反馈

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| article_id | VARCHAR(36) | FK -> knowledge_articles.id | 文章 |
| user_id | VARCHAR(36) | NOT NULL | 用户 |
| feedback_type | VARCHAR(20) | NOT NULL | helpful/unhelpful/partial |
| comment | TEXT | | 评论 |
| ticket_id | VARCHAR(36) | | 关联工单 |

---

### 3.16 治理中心（4 张）

#### users — 用户表

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| username | VARCHAR(100) | NOT NULL UNIQUE | 用户名 |
| email | VARCHAR(255) | UNIQUE | 邮箱 |
| display_name | VARCHAR(255) | | 显示名 |
| hashed_password | VARCHAR(255) | NOT NULL | 密码哈希 |
| status | VARCHAR(20) | DEFAULT 'active' | active/disabled/locked |
| last_login_at | DATETIME | | 最后登录 |
| password_changed_at | DATETIME | | 密码修改时间 |

#### roles — 角色表

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| name | VARCHAR(100) | NOT NULL UNIQUE | 角色名 |
| description | TEXT | | 说明 |
| permissions | TEXT | NOT NULL | 权限列表 JSON |

#### user_roles — 用户角色关联

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| user_id | VARCHAR(36) | FK -> users.id | 用户 |
| role_id | VARCHAR(36) | FK -> roles.id | 角色 |

#### api_keys — API Key

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| name | VARCHAR(255) | NOT NULL | 名称 |
| key_hash | VARCHAR(255) | NOT NULL | Key 哈希 |
| key_prefix | VARCHAR(20) | NOT NULL | Key 前缀（用于识别） |
| user_id | VARCHAR(36) | FK -> users.id | 所属用户 |
| scopes | TEXT | | 权限范围 JSON |
| expires_at | DATETIME | | 过期时间 |
| last_used_at | DATETIME | | 最后使用 |
| status | VARCHAR(20) | DEFAULT 'active' | active/revoked/expired |

---

## 4. 索引设计原则

1. 每张表主键使用 UUID VARCHAR(36)
2. 所有外键字段建立索引
3. 频繁查询条件建立复合索引
4. 软删除查询包含 is_deleted 条件
5. 时间范围查询字段建立索引
6. 状态字段建立索引
7. 去重/指纹字段建立唯一索引

## 5. Migration 规范

1. 所有变更使用 Alembic migration
2. 每个迁移有 upgrade 和 downgrade
3. 迁移脚本不可修改
4. 生产环境迁移前必须备份
5. 大表变更需要分步执行

## 6. 数据流

```text
采集器 / Agent
  ↓
标准化采集结果 (collection_results)
  ├── 指标 → VictoriaMetrics
  ├── 最新状态 → Redis 缓存 + state_snapshots
  ├── 状态变更 → state_changes → events
  ├── 配置事实 → config_drifts
  └── 日志 → collection_logs

events
  ↓ 去重、关联、分类
  ↓
alerts
  ↓ 策略匹配
  ↓
policies → automation_executions
  ↓
automation_execution_steps + execution_logs
  ↓
验证 → 成功关闭 / 失败回滚 / 转工单
  ↓
知识沉淀 → knowledge_articles
```
