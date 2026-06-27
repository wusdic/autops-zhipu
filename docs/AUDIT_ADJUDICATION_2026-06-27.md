# 外部审查报告逐条评估与处置（2026-06-27）

针对外部审查报告（审查版本 `eb06902`）逐条核对其合理性，并标注处置：
**已修复 / 部分修复 / 已存在 / 拒绝（不成立）/ 受理待办（架构级，需测试环境）**。

> 验证手段：本环境无后端依赖（pydantic 等）与 MySQL/目标设备，仅能做
> `python -m py_compile` 与 `ruff --select F`。集成/真机验证须在 CI 与真实环境完成。

## 阻断级（P0）

| 编号 | 结论 | 处置 |
|---|---|---|
| P0-01 配置/迁移在 Windows/中文环境不可用 | **合理** | **已修复**：`config.py` 所有 YAML 读取显式 `encoding="utf-8"`；`alembic.ini` 注释改 ASCII。 |
| P0-02 告警→策略→自动化未真实落库 + 重复触发 | **合理（核心）** | **部分修复**：① 告警规则命中现先 `AlertService.create_alert()` 落库，再发布带真实 `alert_id` 的 `ALERT_CREATED`；② 删除 aiops 中重复的 `on_alert_created_match_policies`/`on_policy_approved_create_execution`，告警→策略、审批→执行统一由 policy 领域负责，消除双触发。**受理待办**：`PolicyExecution` 落表、`Event→Alert→PolicyExecution→Execution` 全链事务化仍需配合执行队列改造。 |
| P0-03 Outbox 标记 done 但执行在不可重试后台 task | **合理** | **受理待办**：需引入独立 `execution_queue`/job 表（Worker 领取/续租/幂等重试）。改动大、无测试环境暂不盲改，已记入路线。 |
| P0-04 审批状态 `pending_approval` vs `awaiting_approval` 不一致 | **合理** | **已修复**：后端 `automation_extra.py`/`dashboard.py`/`platform_extra.py` 全部查询改为 canonical `awaiting_approval`；前端执行审批已用 `awaiting_approval`（工单域的 `pending_approval` 属另一状态机，保留）；统计响应键 `pending_approval` 作为 API 字段名保留以兼容前端。 |
| P0-05 成功路径 `stderr=None` 触发 Pydantic 校验失败 | **合理** | **已修复**：`local_dev.py`/`ssh.py` 去掉 `or None`，`stderr` 恒为字符串。 |
| P0-06 默认 testpaths 隐藏失败 + 领域测试导入错误 | **合理** | **已修复**：`testpaths` 增加 `app/domains`；删除 `test_automation_service.py` 对不存在的 `BLOCKED_COMMANDS` 的导入。 |

## 高危（P1）

| 编号 | 结论 | 处置 |
|---|---|---|
| P1-01 EventBus 吞掉 outbox 持久化失败 | **合理** | **已修复**：复用业务事务（`session` 非空）时持久化失败 `raise`，触发业务回滚；独立 session 仅记录日志。 |
| P1-02 多个 Service 写表不发事件 | **部分合理** | **部分处置**：告警链路经 handler 发 `ALERT_CREATED`（避免与 create_alert 双发故 service 不再重复发）。asset/state 入口补事件属增强，**受理待办**。 |
| P1-03 创建执行后不自动运行 / 审批通过不续跑 | **合理** | **受理待办**：与 P0-03 执行队列一并改造（审批通过 → 入队 → Worker 运行）。 |
| P1-04 中间件只信 JWT、不校验用户状态、不支持 API Key | **合理** | **受理待办**：需中间件查用户状态 + 短期缓存 + `X-API-Key` scope 映射，属安全加固阶段。 |
| P1-05 凭证接口缺管理员保护且返回密文 | **合理** | **已修复**：`cred_router` 挂 `require_admin`；响应统一经 `_cred_dict()` 剔除 `encrypted_data`/原始密钥材料。 |
| P1-06 备份占位却标记 completed | **合理** | **已修复**：占位/降级标记为 `degraded`（restore 已拒绝非 completed）。备份入队列属待办。 |
| P1-07 发现任务在 API 进程内 + ping 平台不兼容 | **合理** | **受理待办**：进 Worker 队列、ping 跨平台参数，归入队列化改造。 |
| P1-08 WebSocket/日志通道契约不一致 | **合理** | **受理待办**：需统一 WS 协议与 unsubscribe/生命周期清理，单独处理。 |
| P1-09 执行日志写 ExecutionStep、API 读 ExecutionLog | **合理** | **受理待办**：统一日志模型，需配套前端联调。 |
| P1-10 漂移检测逻辑不可能命中 + rollback 产生多 published | **合理** | **已修复**：`detect_drift` 改查该 definition 全部版本的绑定再比对最新发布版本；`rollback_version` 先建 draft 再复用 `publish_version` 归档逻辑，保证唯一 published。 |
| P1-11 Alembic baseline 用 create_all 不可复现 | **合理** | **受理待办**：baseline 改显式 DDL 风险高（需全链回归），单列任务。 |
| P1-12 前端执行列表用了后端不支持的筛选/统计参数 | **合理** | **受理待办**：需后端补筛选/统计/趋势/retry 或前端裁剪，建议 OpenAPI 生成 client。 |
| P1-13 旧 AIOps `_call_llm` 未带 API Key | **合理** | **已修复**：新增 `_llm_headers()`，两处 `/chat/completions` 均带 `Authorization: Bearer`。 |

## 中危（P2）

| 编号 | 结论 | 处置 |
|---|---|---|
| P2-01 `app.yaml` 未加载、version 硬编码 0.5.0 | **合理** | **已修复**：`AppConfig` 加载 `app.yaml`（version/api_prefix/cors_origins/name）；version 统一 `0.7.0`（config 默认 + `app.yaml` + `pyproject.toml`）。 |
| P2-02 Pydantic v2 仍用 class Config | **合理** | **已修复**：5 个 BaseSettings 改 `model_config = SettingsConfigDict(...)`。 |
| P2-03 统计 total 忽略过滤条件 | **合理** | **已修复**：`AIOpsService.list_analyses`、`ConfigService.list_definitions/list_credentials`、`StateService.get_changes` 的 count 复用同一筛选。 |
| P2-04 命令策略默认 allowlist 过宽 | **部分合理** | **受理待办**：生产默认 deny + 资产/目录白名单 + 统一 SSH/local 策略，安全阶段处理。 |
| P2-05 多类后台任务仍在 API 进程内 | **合理** | **受理待办**：与执行队列统一。 |
| P2-06 前端 refresh token 未接入 | **合理** | **受理待办**：需实现存储/轮换/并发刷新锁，前端联调任务。 |
| P2-07 前端路由只检查 token 不检查权限 | **合理** | **受理待办**：路由 meta 加权限（体验级），后端仍为权威。 |
| P2-08 部署脚本默认弱口令 / Redis 无认证 | **部分合理** | **受理待办**：安装脚本禁默认生产口令、Redis 强制密码。 |
| P2-09 ruff/类型门禁未建立 | **合理** | **部分处置**：本次仅修真实 F 类与本次改动；全量风格收敛分阶段做（不阻塞业务修复）。 |

## 低危/规范（§6）

| 项 | 结论 | 处置 |
|---|---|---|
| 1 可变默认 `{}`（ExecutionPlan/Result） | 合理 | **已修复**：改 `Field(default_factory=dict)`。 |
| 2 TestClient httpx 弃用告警 | 合理 | 受理待办（依赖锁定）。 |
| 3 前端 chunk 过大 | 合理 | 受理待办（拆包）。 |
| 4 多处 raw SQL 边界不清 | 部分合理 | 受理待办（仓储层收敛）。 |
| 5 `PUBLIC_PREFIXES` 用 startswith | 合理 | 受理待办（精确匹配）。 |
| 6 登录密码最小长度 1 | 合理 | 受理待办（统一密码策略）。 |
| 7 handler 吞异常不抛 outbox | 合理 | 见 P1-01（核心写路径已处理）。 |
| 8 跨模块同名状态不同义 | 合理 | 受理待办（状态字典）。 |

## 本次实际改动文件

- `backend/app/infra/config.py`（P0-01/P2-01/P2-02）
- `configs/app.yaml`、`backend/pyproject.toml`（P2-01 版本统一；testpaths）
- `backend/alembic.ini`（P0-01）
- `backend/app/domains/automation/executor/base.py|local_dev.py|ssh.py`（P0-05、可变默认）
- `backend/app/api/automation_extra.py|dashboard.py|platform_extra.py`（P0-04）
- `backend/app/domains/config/api.py`（P1-05）、`config/service.py`（P1-10、P2-03）
- `backend/app/api/backup.py`（P1-06）
- `backend/app/common/events.py`（P1-01）
- `backend/app/domains/aiops/service.py`（P1-13、P2-03）、`aiops/handlers.py`（P0-02 去重）
- `backend/app/domains/alert/handlers.py`（P0-02 告警落库）
- `backend/app/domains/state/service.py`（P2-03）
- `backend/app/domains/automation/tests/test_automation_service.py`（P0-06）

## 说明：受理待办的取舍

报告对“核心闭环真实落库 + 执行队列化”（P0-03/P1-03/P1-07/P1-08/P1-09/P1-11/
P1-12/P2-05）的判断成立，但属跨领域架构改造，需在可运行的 CI + 真机环境下
配套集成测试才能安全落地。本次优先完成**可独立验证、低风险、高确定性**的修复，
其余按报告第 7 节阶段顺序排入后续。
