# 日志中心（log）

## 职责
集中管理自动化执行任务的运行日志，包括标准输出和标准错误流的实时追加与分页查询。按执行任务和执行步骤维度组织日志，支持运维操作审计和故障排查。

## 核心模型
| 模型 | 说明 |
|------|------|
| ExecutionLog | 执行日志，记录执行ID、步骤ID、流类型（stdout/stderr）、内容和偏移量 |

## API端点
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/logs/execution/{execution_id} | 获取执行任务日志（支持按步骤ID筛选） |
| POST | /api/v1/logs/execution/{execution_id} | 追加执行日志 |
| GET | /api/v1/logs/execution/{exec_id}/step/{step_id} | 获取指定步骤的日志 |

## 事件
### 发布的事件
- `log.entry_created` — 日志条目创建
- `log.execution_log_stream` — 执行日志流

### 订阅的事件
- `automation.execution_started` — 执行开始时初始化日志上下文
- `automation.step_completed` — 步骤完成时记录输出日志
- `automation.step_failed` — 步骤失败时记录错误日志
- `automation.execution_completed` — 执行完成时记录汇总日志
- `automation.execution_failed` — 执行失败时记录错误汇总

## 领域边界
- **不直接访问**其他领域的数据库表
- **通过事件总线**与其他领域通信
- **通过Service层**对外提供能力
