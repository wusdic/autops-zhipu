# AUTOPS 后端深度审计报告

> 日期: 2026-06-01
> 目的: 查找所有已实现但未引用、未完成的mock实现、以及前后端不匹配问题

---

## 1. 已实现但 Handler 调用了缺失方法

| # | 位置 | 问题 | 严重度 |
|---|------|------|--------|
| M1 | `automation/handlers.py:79,112` 调用 `svc.append_execution_log()` | `AutomationService` 中**没有** `append_execution_log` 方法，运行时会报错 | 🔴 P0 |
| M2 | `collector/handlers.py:62` 调用 `svc.list_collectors(asset_type=...)` | `CollectorService.list_collectors()` **没有** `asset_type` 参数 | 🟡 P1 |
| M3 | `collector/handlers.py:97` 调用 `svc.list_failed_jobs(reason=...)` | `CollectorService` **没有** `list_failed_jobs` 方法 | 🟡 P1 |
| M4 | `collector/handlers.py:102` 调用 `svc.retry_job(job_id)` | `CollectorService` **没有** `retry_job` 方法 | 🟡 P1 |
| M5 | `collector/handlers.py:128` 调用 `svc.cancel_job(job_id)` | `CollectorService` **没有** `cancel_job` 方法 | 🟡 P1 |

## 2. 完全是 Mock/Stub 的实现

| # | 文件 | 问题 | 严重度 |
|---|------|------|--------|
| S1 | `asset/discovery_service.py` | `create_task()` 返回mock数据 `"id": "mock-task-001"`，`list_tasks()` 返回空 | 🔴 P0 |
| S2 | `asset/discovery_schemas.py` | 前端发送 `name/cidr/protocols/ports`，后端schema只有 `ip_range/scan_type` | 🔴 P0 |
| S3 | `workers/__init__.py` | 空文件，没有调度器/执行引擎 | 🔴 P0 |

## 3. 实现完整但缺少"执行层"（只写DB不执行动作）

| # | 文件 | 问题 | 严重度 |
|---|------|------|--------|
| E1 | `automation/service.py` | `create_execution()` 只创建DB记录，不真正执行脚本/命令 | 🔴 P0 |
| E2 | `collector/service.py` | `record_result()` 只写DB，没有真正的采集器去调用 | 🔴 P0 |
| E3 | `config/service.py` (250行) | `detect_drift()` 是完整实现，但无人调用 | 🟡 P1 |

## 4. 已完整实现但未被启动/引用的模块

| # | 模块 | 行数 | 说明 | 状态 |
|---|------|------|------|------|
| R1 | `aiops/agent/react.py` | 196行 | 完整的 ReAct Agent 推理循环 | ✅ 已实现，依赖LLM |
| R2 | `aiops/agent/llm_client.py` | 246行 | 完整的 LLM 客户端 | ✅ 已实现 |
| R3 | `aiops/agent/context.py` | 51行 | Agent 上下文构建 | ✅ 已实现 |
| R4 | `aiops/agent/api.py` | 145行 | Agent API端点 | ✅ 已注册路由 |
| R5 | `aiops/tools/readonly.py` | 144行 | 5个只读工具(查资产/告警/知识/执行日志/事件) | ✅ 已实现 |
| R6 | `aiops/tools/execution.py` | 66行 | 2个执行工具(执行脚本/创建工单) | ✅ 已实现 |
| R7 | `aiops/tools/guard.py` | 63行 | ToolGuard安全边界 | ✅ 已实现 |
| R8 | `aiops/tools/registry.py` | 72行 | 工具注册中心 | ✅ 已实现 |
| R9 | `integrations/*.py` | ~500行 | Webhook/钉钉/邮件通知渠道 | ✅ 已实现 |
| R10 | `state/handlers.py` | 123行 | 状态变更→采集完成→告警恢复 事件处理 | ✅ 已实现 |
| R11 | `event/handlers.py` | 完整 | 资产变更→事件创建 | ✅ 已实现 |
| R12 | `alert/handlers.py` | 完整 | 事件→规则匹配→告警创建→自动恢复 | ✅ 已实现 |
| R13 | `policy/handlers.py` | 完整 | 告警→策略匹配→执行创建 | ✅ 已实现 |
| R14 | `automation/handlers.py` | 完整 | 策略触发→创建执行+步骤日志 | ✅ 已实现 |
| R15 | `collector/handlers.py` | 124行 | 资产创建→采集作业、凭证变更→重试、资产删除→取消作业 | ✅ 已实现，但有M2-M5缺失方法 |
| R16 | `common/event_handlers.py` | 完整 | **10条联动链路全部已注册**，包括审计/通知 | ✅ 核心骨架完整 |

## 5. 前后端不匹配

| # | 问题 | 严重度 |
|---|------|--------|
| F1 | 资产发现前端发 `name/cidr/protocols/ports/timeout`，后端schema只接受 `ip_range/scan_type` | 🔴 P0 |

## 6. 核心结论

### 已有完整实现的（只需接线即可工作）:
1. **事件总线** - 10条联动链路全部注册 ✅
2. **AIOps Agent** - ReAct推理循环、工具集、安全边界 ✅
3. **通知集成** - Webhook/钉钉/邮件 ✅
4. **领域Handler链** - 状态→事件→告警→策略→自动化 完整 ✅

### 缺失的"执行层"（需要新增实现）:
1. **资产发现引擎** - 真实网络扫描 (替代mock) 
2. **内置采集器** - Ping/TCP/HTTP/Cert/DB 探测
3. **定时调度器** - workers/ 目录为空
4. **自动化执行引擎** - 真正执行脚本命令

### 缺失的方法（需要在现有Service中补充）:
1. `AutomationService.append_execution_log()` - handler已调用但方法不存在
2. `CollectorService.list_collectors(asset_type=)` - 需要加参数
3. `CollectorService.list_failed_jobs()` - 需要新增
4. `CollectorService.retry_job()` - 需要新增
5. `CollectorService.cancel_job()` - 需要新增
