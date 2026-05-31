# 自动化执行中心（automation）

## 职责
管理运维自动化脚本、Playbook 剧本和执行任务的完整生命周期。支持脚本版本管理、Playbook 多步骤编排、执行审批流程、试运行和执行结果追踪。

## 核心模型
| 模型 | 说明 |
|------|------|
| Script | 脚本，记录脚本名称、类型、内容和参数定义 |
| Playbook | 剧本，编排多个脚本步骤的执行流程和依赖关系 |
| Execution | 执行任务，记录 Playbook 的一次执行实例及其状态和风险级别 |
| ExecutionStep | 执行步骤，记录 Playbook 中每个步骤的执行状态、输出和耗时 |

## API端点
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/scripts | 脚本列表（支持按类型筛选） |
| POST | /api/v1/scripts | 创建脚本 |
| PUT | /api/v1/scripts/{script_id} | 更新脚本 |
| DELETE | /api/v1/scripts/{script_id} | 删除脚本 |
| GET | /api/v1/playbooks | Playbook 列表 |
| POST | /api/v1/playbooks | 创建 Playbook |
| GET | /api/v1/playbooks/{playbook_id} | 获取 Playbook 详情 |
| PUT | /api/v1/playbooks/{playbook_id} | 更新 Playbook |
| DELETE | /api/v1/playbooks/{playbook_id} | 删除 Playbook |
| GET | /api/v1/executions | 执行任务列表（支持按状态筛选） |
| POST | /api/v1/executions | 创建执行任务 |
| GET | /api/v1/executions/{exec_id} | 获取执行任务详情 |
| POST | /api/v1/executions/{exec_id}/approve | 审批通过执行任务 |
| POST | /api/v1/executions/{exec_id}/cancel | 取消执行任务 |
| GET | /api/v1/executions/{exec_id}/verification | 获取执行任务验证信息 |

## 事件
### 发布的事件
- `automation.script_created` — 脚本创建
- `automation.playbook_created` — Playbook 创建
- `automation.execution_created` — 执行任务创建
- `automation.execution_approved` — 执行审批通过
- `automation.execution_started` — 执行开始
- `automation.step_completed` — 执行步骤完成
- `automation.step_failed` — 执行步骤失败
- `automation.execution_completed` — 执行完成
- `automation.execution_failed` — 执行失败
- `automation.execution_cancelled` — 执行取消
- `automation.execution_rolled_back` — 执行回滚
- `automation.dry_run_completed` — 试运行完成

### 订阅的事件
- `policy.triggered` — 策略触发后创建执行任务
- `policy.approved` — 策略审批通过后启动执行

## 领域边界
- **不直接访问**其他领域的数据库表
- **通过事件总线**与其他领域通信
- **通过Service层**对外提供能力
