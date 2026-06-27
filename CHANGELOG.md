# AUTOPS Changelog

所有重要变更将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [0.8.0] - 2026-06-27

### 第四轮整改：执行队列化 + 闭环落库 + 契约对齐 + 安全加固

> 实施记录见 `docs/REMEDIATION_P1_P4_2026-06-27.md`。新增迁移 0010，部署需 `alembic upgrade head`。

#### Added — 执行队列化（P0-03/P1-03/P2-05）
- `execution_queue` 表（迁移 0010）+ `execution_queue.py`（领取/续租/心跳/指数退避重试）
- `ExecutionWorker`（并入 WorkerRunner）：持久化领取并运行，崩溃租约回收重投
- `EventBus.dispatch_to_handlers` 聚合异常抛出 `EventDispatchError` → outbox 真正重试；幂等键成功后登记

#### Changed — 核心闭环真实落库（P0-02/P1-02/P1-07）
- 告警规则命中先落 `Alert`；策略匹配落 `PolicyExecution` 并串 `policy_execution_id` 全链
- `on_execution_created_run` 同步创建+入队（不再 fire-and-forget）
- 发现扫描移出 API 进程（发 `DISCOVERY_SCAN_REQUESTED` 由 Worker 执行）；ping 跨平台
- `asset.create_asset` / `state.record_snapshot` 补发领域事件

#### Fixed — API 契约（P1-08/P1-09/P1-12）
- WebSocket：支持 unsubscribe + lifespan 停止桥接；前端统一 `/ws?token`+executions 频道
- 执行日志统一写 `ExecutionLog`
- `GET /executions` 支持筛选/stats/trend；新增 `POST /executions/{id}/retry`

#### Security（P1-04/P2-04/P2-06/P2-07/P2-08）
- 中间件校验用户禁用状态(30s 缓存) + 支持 `X-API-Key`(scope)
- `CommandPolicy.evaluate_script()` 多行脚本逐行硬校验，SSH/local 共用
- 前端 refresh token 单飞刷新；M12/审计路由体验级管理员拦截
- install.sh 去硬编码弱口令、Redis requirepass

#### Chore（P2-09）
- 修复 `F821`（scheduler `CollectionJob` 前向引用）；清理 78 处未用导入

#### 受理待办（高风险/大改，需可运行环境）
- P1-11 Alembic baseline 显式 DDL；主机升级/回滚真实执行；多租户行级隔离；mypy strict 全量；前端拆包

## [0.7.1] - 2026-06-27

### 外部审查整改（第三轮）：闭环正确性 + 工程门禁 + 跨平台/契约修复

> 逐条评估见 `docs/AUDIT_ADJUDICATION_2026-06-27.md`。本轮聚焦可独立验证、
> 低风险的高确定性修复；执行队列化等架构级项已受理待办。

#### Fixed — 阻断级
- **P0-01 跨平台配置/迁移**：`config.py` YAML 读取显式 `encoding="utf-8"`；`alembic.ini` 注释改 ASCII（修 Windows/中文 locale 下 GBK 解码崩溃）
- **P0-02 告警闭环**：告警规则命中先 `create_alert()` 落库再发布带真实 `alert_id` 的 `ALERT_CREATED`；删除 aiops 中重复的告警→策略、审批→执行 handler（消除双触发）
- **P0-04 审批状态统一**：后端查询全部由 `pending_approval` 改为 canonical `awaiting_approval`（automation_extra/dashboard/platform_extra）
- **P0-05 执行成功路径**：`stderr` 恒为字符串（去 `or None`，修 Pydantic 校验失败）
- **P0-06 测试门禁**：`testpaths` 纳入 `app/domains`；修复领域测试对不存在的 `BLOCKED_COMMANDS` 的导入

#### Fixed — 高危
- **P1-01**：EventBus 复用业务事务时 outbox 持久化失败改为抛出（触发回滚），不再静默吞掉
- **P1-05**：凭证接口挂 `require_admin`，响应剔除 `encrypted_data` 等密文字段
- **P1-06**：备份占位文件标记为 `degraded`（不再冒充 completed）
- **P1-10**：配置漂移检测改查全部版本绑定再比对最新发布版本；rollback 复用 publish 归档逻辑保证唯一 published
- **P1-13**：旧 AIOps `_call_llm` 两处补 `Authorization: Bearer` 头

#### Fixed — 中危
- **P2-01**：加载 `app.yaml`（version/api_prefix/cors_origins/name）；version 统一为 `0.7.x`
- **P2-02**：5 个 BaseSettings 由 `class Config` 迁移到 `SettingsConfigDict`
- **P2-03**：分页 total 复用同一筛选条件（aiops/config/state 列表）
- 可变默认 `{}` → `Field(default_factory=dict)`（ExecutionPlan/ExecutionResult）

## [0.7.0] - 2026-06-26

### 深度采集/巡检/报告闭环、生产执行器、平台功能补齐、前后端契约对齐

> 本版本新增 5 个数据库迁移（0005–0009），部署需执行 `alembic upgrade head`。

#### Added — 设备深度采集 · 巡检执行 · 自动报告
- **深度采集器**（`app/workers/device_inspect.py`）：SSH(Linux)/WinRM(Windows)/SNMP(网络设备) 采集 OS/CPU/内存/磁盘/负载/inode/进程/监听端口/NTP/SSH-root/SELinux 等真实指标；依赖懒加载，缺失优雅降级
- **凭据解析**（`app/common/credentials.py`）：按资产绑定凭据解密并归一化（用户名/密码/私钥/community）
- **巡检执行引擎**（`app/domains/inspection/executor.py`）：按模板 `check_items` + 启用的巡检规则评估阈值，写 `InspectionResult`/`InspectionReport`
- **定时巡检**（`app/workers/inspection_scheduler.py`）：worker 内置 cron 触发巡检计划
- **报告生成器**（`app/domains/report/generator.py`）：汇总资产/告警/巡检渲染 HTML 报告并归档
- 新增依赖：`asyncssh`、`pysnmp`、`pywinrm`

#### Added — 生产自动化执行器
- 新增 `SSHExecutor`（`executor/ssh.py`），凭据中心解析登录，支持多行脚本，拦截高危/fork 炸弹
- 执行器可配置选择 `AUTOPS_EXECUTOR=auto|local_dev|ssh`（auto：生产→ssh）

#### Added — 平台与 AI 功能补齐（此前前端有页面、后端缺失/造假）
- AI 助手：`/ai/chat`、`/ai/execute`
- 模型服务：`/aiops/agents` CRUD + `/aiops/agents/{id}/test` + `/aiops/model-config`（api_key 加密；LLMClient 运行时读取，回退 env/yaml）
- 平台：字典 CRUD、`/platform/license`、`/platform/upgrade-history`；任务队列修正（`event_outbox.status`）
- 备份：由内存 mock 改为 `backups` 表持久化 + mysqldump 真实产物 + 下载
- 导出中心：`/exports` 真实生成 CSV（白名单表）+ `/exports/{id}/download`
- 工单附件：真实上传(multipart)/列表/下载/删除（`ticket_attachments` 表落盘）
- 巡检规则：`/inspection/rules` CRUD + toggle，执行器据此评估
- 触发历史：`/trigger-history`（巡检规则/处置模板触发记录）

#### Added — 补齐前端在用但后端缺失的端点
- 凭证 PUT/DELETE、资产绑定凭证 POST、知识 DELETE、告警规则 DELETE、Edge 采集器 GET 列表/详情/DELETE、工单附件 DELETE

#### Fixed — 阻断级与前后端契约
- `success()` 恢复 `message` 参数（修复全仓 44 处删除/登出类端点 500）
- `EventService.create_event` 发布 `event.created`/`event.deduplicated`，打通 event→alert→policy→automation
- `RoleResponse.parse_permissions` 容错 `*:*` 裸字符串（修 `/auth/me` 500）
- `HTTPBearer(auto=False)` → `auto_error=False`（修后端导入即报错）
- alert/policy/automation handler 的 JSON 字段解析与方法签名修正
- 前端：App.vue 未登录不渲染 MainLayout（消除 401 风暴）、侧边栏默认展开、401→session-expired、路由守卫放行公开页、ConfigOverview/OpsReport 假动作接真
- 配置：`DB_PASS`/`REDIS_PASS`/`JWT_ALGORITHM` 增加 `AliasChoices`

#### Added — 迁移
- `0005_check_type`、`0006_platform_tables`、`0007_inspection_rules`、`0008_exports_attach`、`0009_trigger_history`

#### Changed — 统计（详见 README）
- 数据库表 36 → **47**；API 端点 145+ → **300+**

## [0.6.0] - 2026-06-25

### 全面安全加固、Bug 修复、自动纳管、文档同步

#### Added — 自动发现并纳管
- **auto_onboard 自动纳管**：发现任务新增 `auto_onboard` 字段（默认开启），创建任务即自动启动扫描，扫描完成自动纳管全部存活 IP（幂等），纳管后立即采集+定期采集，全程无人值守
- 新增 alembic 迁移 `0004_discovery_auto_onboard`
- 前端创建对话框新增"自动纳管"开关

#### Added — RBAC 鉴权层
- 新增 `require_admin` 授权依赖（复用现有 Role 表，零迁移）
- `UserResponse` 新增 `roles` 字段，`/auth/me` 返回角色信息
- 高危端点（用户/角色/资产/脚本/Playbook 增删、执行审批/回滚、审计日志、备份恢复、租户管理）挂载 require_admin

#### Fixed — 阻断性 Bug
- `CRUDService.list_paginated` 引用不存在的 `model_class` 致必崩 → 改用 `self.repo.model`
- WebSocket 匿名连接 + 广播逻辑反转（未订阅反收全部平台数据）→ 强制鉴权 + 仅订阅频道接收
- 健康检查 `anext(get_db())` 连接泄漏；`get_redis()` 漏 await
- CertCollector 误用私有 API 功能失效；Ping 写死 `-c/-W` 在 Windows 失效

#### Fixed — 安全加固
- 凭证加密改用独立 `CREDENTIAL_ENCRYPT_KEY` + 每条随机盐（Fernet/PBKDF2），与 JWT 密钥分离
- 命令策略相对路径绕过、AI Agent 工具 JSON 注入与执行旁路
- 前端 XSS：净化器改用 DOMPurify；知识库/搜索 v-html 全部净化
- Redis/后端端口绑定 `127.0.0.1`；configs 移除硬编码密钥；初始口令改为随机生成

#### Fixed — 事件一致性与并发
- outbox 写入支持复用业务事务（原子提交）
- `run_execution` 同步阻塞事件总线 → 改后台 task
- 幂等去重 `clear()` 全量清空 → OrderedDict LRU；发布版本竞态加行锁

#### Fixed — 前端系统性问题
- 清除 `'primary'` 占位符污染（666 处，90+ 文件），根因是表单初始值/查询参数被注入垃圾值导致加载数据错误
- API 客户端 baseURL 硬编码、拦截器错误结构丢失
- 运算符优先级 bug、路由 404、ElMessageBox cancel 判断、对话框状态不重置等

#### Changed — 代码质量
- 全局 `datetime.utcnow()` → `datetime.now(timezone.utc)`（31 处）
- 收敛吞异常为日志；通用异常处理器补 traceback
- Dockerfile 非 root 用户、CI 加扫描（建议）

#### Docs — 文档与代码一致性同步
- README：默认口令改为随机/环境变量、补充 RBAC 与 auto_onboard、Redis 版本 7.0+
- 部署运维：端口统一 8001、废弃 compose 提示、curl 健康检查说明、备份/自检/升级脚本路径与命令修正
- API 契约：补 require_admin 权限列、/auth/me roles、discovery 端点与 auto_onboard 字段、分页 total_pages
- WebSocket：路径 `/api/v1/ws`、强制鉴权、订阅语义、事件 type 与心跳对齐代码
- 安全架构：凭证加密方案改为 Fernet/PBKDF2 实际实现、补充中间件白名单与 require_admin
- 错误码：00010 HTTP 改 422、00103 补 require_admin 说明
- `.env.example`：补 `MYSQL_ROOT_PASSWORD`/`ADMIN_INITIAL_PASSWORD`/`FRONTEND_PORT`/`CREDENTIAL_ENCRYPT_KEY`，删死变量 `JWT_EXPIRE_MINUTES`

## [0.5.0] - 2026-06-01

### 执行层实现 + 集成修复

#### Added — 执行层
- **发现引擎**：TCP/ICMP/CIDR网段扫描，自动推断资产类型（Linux/Windows/数据库/Web），异步扫描，纳管接口
- **内置采集器**：Ping、TCP端口、HTTP、SSL证书、数据库检查 5个采集器
- **采集调度器**：定时采集周期（默认900秒）、资产创建事件触发采集、Ping状态变更检测
- **策略→自动化执行链路**：EXECUTION_CREATED事件消费者，自动创建执行记录并运行脚本
- **告警自动恢复**：执行完成后自动将告警状态更新为resolved

#### Fixed
- collection-jobs API参数位置错位导致items返回空列表
- 双重策略匹配（移除重复的on_alert_created_match_policy订阅）
- 策略匹配JSON字段（trigger_condition/action_chain）未解析为dict
- ExecutionStep.append_execution_log使用不存在的DB字段
- ExecutionCreate.asset_ids不允许空列表

#### 前端修复
- 发现结果IP列空白（API字段`ip` vs 前端`ip_address`）
- 纳管向导HTML结构损坏（恢复完整wizard四步流程）
- 凭证步骤强制必填改为可选
- discovered状态未映射（前端只识别'new'/'managed'）
- NotificationBell/ConfigInheritance硬编码API路径改用routes.ts常量

#### 清理
- 删除39个测试残留采集器，只保留5个标准内置采集器

### 验证
- ✅ 完整事件链路验证通过：Ping采集→状态变更→事件→告警→策略→自动化执行→恢复
- ✅ 浏览器E2E：登录→发现资产→纳管→采集→告警→策略→自动化 全流程可用

---

## [0.4.0] - 2026-06-01

### M5增强 + 前端全面增强

#### Added
- AI Agent LLM集成（智谱GLM）
- 数据库方言抽象层（MySQL/PostgreSQL/openGauss/达梦/人大金仓）
- 前端M3/M5页面实现
- 前端功能全面增强：CollectorPage(103→770行)、CommandCenterPage(155→807行)等
- 批量操作框架
- 集成测试完善
- 通知渠道API

---

## [0.3.0] - 2026-05-31

### M3标准场景闭环

#### Added
- 8个标准场景的事件规则、策略、自动化动作
- 故障处置台、执行日志流、验证结果
- 工单升级和知识沉淀
- E2E测试

---

## [0.2.0] - 2026-05-30

### M2平台主干完成

#### Added
- 13个领域模块核心实现（models/schemas/repository/service/events/handlers）
- 统一事件总线
- 前端7大工作台基础页面
- 145+ API端点

---

## [0.1.0] - 2026-05-29

### M1基础骨架完成

#### Added
- FastAPI项目初始化
- SQLAlchemy + Alembic配置
- MySQL/Redis连接
- 统一响应结构 `{code, message, data, trace_id}`
- 统一错误码
- JWT认证和RBAC权限框架
- Vue 3 + TypeScript + Vite前端项目
- Element Plus UI + 主题
- 路由守卫和布局框架

---

## [0.0.1] - 2026-05-28

### M0设计完成

#### Added
- 项目初始化：目录结构、核心设计文档
- 37份设计文档
- 8份ADR技术决策记录
- 全局约束和目标架构定义
- 开发计划和测试策略
