# 第四轮整改实施记录（P一 ~ P四，2026-06-27）

按用户要求，依次完成外部审查报告 §7「建议整改顺序」的一~四阶段。无法在本环境运行
（无后端依赖/MySQL/目标设备），均以 `py_compile` + `ruff --select F` 静态校验；
集成与真机验证须在 CI + 真实环境完成。

## 一、核心闭环真实落库 + 执行队列化 ✅

| 项 | 处置 |
|---|---|
| P0-03/P1-03/P2-05 执行队列化 | 新增 `execution_queue` 表(迁移 0010) + `app/common/execution_queue.py`（enqueue/lease/heartbeat/complete/fail，租约回收+指数退避重试）+ `ExecutionWorker`（并入 WorkerRunner）。`on_execution_created_run` 改为**同步创建+入队**，失败抛错触发 outbox 重试；API create/approve、审批中心 approve、retry 均入队。`EventBus.dispatch_to_handlers` 聚合异常抛出，幂等键改为成功后登记 → outbox 真正可重试。 |
| P0-02 全链落库 | `PolicyService.match_and_record` 统一匹配并逐条落 `PolicyExecution`；`policy_execution_id` 串入 POLICY_TRIGGERED→EXECUTION_CREATED→Execution 回填。 |
| P1-07 发现移出 API | `start_task` 改发 `DISCOVERY_SCAN_REQUESTED` 事件（与状态同事务，不再 create_task/commit），Worker 进程执行扫描；ping 跨平台参数。 |
| P1-02 领域事件 | `asset.create_asset` 发 ASSET_CREATED；`state.record_snapshot` 发 SNAPSHOT/STATE_CHANGED/CRITICAL/RECOVERED。 |

## 二、API 契约对齐 ✅

| 项 | 处置 |
|---|---|
| P1-08 WebSocket | 后端支持 unsubscribe + realtime 桥接 lifespan 停止；前端统一走 `/ws?token` + executions 频道 + REST 拉历史日志（不再连不存在的 `/execution/{id}/logs`）。 |
| P1-09 日志模型 | 执行输出与步骤日志统一写 `ExecutionLog`（日志中心/前端读取的表）。 |
| P1-12 执行列表 | `GET /executions` 支持筛选(trigger_source/risk_level/search/时间) + stats + trend；新增 `POST /executions/{id}/retry`；前端 retry/canCancel/canRetry 对齐 canonical 状态。 |
| OpenAPI 生成 client（建议） | **未做**：建议后续以 OpenAPI 生成前端 client 根治契约漂移（需前端构建链改造）。 |

## 三、安全加固 ✅

| 项 | 处置 |
|---|---|
| P1-04 鉴权 | `app/common/auth_state.py`：用户禁用即时失效校验(30s 缓存) + `X-API-Key` 解析(sha256/过期/scope)；中间件接入两路认证。 |
| P2-04 命令策略 | `CommandPolicy.evaluate_script()` 多行脚本逐行硬校验；SSH/local 共用；生产未知命令默认 deny（既有）。 |
| P2-06 refresh token | 登录存 refresh_token；client 401 单飞刷新+重放，失败再登出。 |
| P2-07 路由权限 | 持久化角色名；guard 对 M12 平台管理 + /audit 体验级管理员拦截（后端 require_admin 仍权威）。 |
| P2-08 部署口令 | install.sh 取消硬编码 `autops_2026`（DB_PASS 或随机）；Redis requirepass 提示/设置。 |

## 四、生产化与规范（部分 ✅ / 部分受理待办）

| 项 | 处置 |
|---|---|
| P2-09 ruff 收敛 | 修复真实 `F821`（scheduler.py 未定义 `CollectionJob` → TYPE_CHECKING 前向引用）；`F401` 全量清理（78 处、54 文件，均为未用导入，无 `__init__` 再导出）。`F841`(40 处未用局部变量) 暂留（低风险，避免误删带副作用赋值）。**mypy strict 全量** + **前端拆包** 仍受理待办。 |
| P1-11 Alembic baseline 显式 DDL | **受理待办（高风险，刻意不盲改）**：`0001_initial_schema.py` 用 `create_all()`。手工改写 30+ 表为显式 `op.create_table()` 且无 DB 无法验证回放，错误会导致全新部署建表失败。须在可运行 DB 的环境用 autogenerate 基线化并回归后再替换。 |
| 主机升级/回滚演示模式 | **受理待办**：`UpgradeMaintenancePage` 仍演示（升级历史可读，真实分发/回滚未做），属运维基建，需分发通道/灰度/回滚方案设计。 |
| 多租户伪隔离 | **受理待办**：有 `tenants` 表与管理页，但核心业务表无 `tenant_id`，无行级隔离。纳入目标需全表加租户维度 + 查询过滤 + 迁移，影响面大，单列里程碑。 |

## 验证

- 后端：`python -m compileall app/` 通过；`ruff --select F`（F401/F811/F821 全清，余 40 F841 为既有未用局部变量）。
- 迁移链 head：`0010_execution_queue`（0009→0010）。部署需 `alembic upgrade head`。
- 前端：本环境无 `node_modules`，未跑 vue-tsc/build；改动均沿用既有模式，需 CI 类型检查与构建确认。
- **强烈建议**：在能运行 CI + MySQL + 目标设备的环境补端到端集成测试（事件入库→告警落库→策略 PolicyExecution→执行入队→Worker 运行→日志/WS→重试）。
