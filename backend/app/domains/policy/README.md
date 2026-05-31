# 策略中心（policy）

## 职责
管理运维自动化策略的定义、触发条件配置和模拟执行。策略可绑定到资产或资产组，在特定事件触发时执行预定义的自动化操作，支持审批流程和模拟测试。

## 核心模型
| 模型 | 说明 |
|------|------|
| Policy | 策略定义，包含触发类型、触发条件、关联动作、审批设置和启用状态 |
| PolicyExecution | 策略执行记录，记录策略触发后的执行历史和结果 |

## API端点
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/policies | 策略列表（支持按触发类型/状态筛选） |
| POST | /api/v1/policies | 创建策略 |
| GET | /api/v1/policies/{policy_id} | 获取策略详情 |
| PUT | /api/v1/policies/{policy_id} | 更新策略 |
| POST | /api/v1/policies/{policy_id}/simulate | 模拟策略执行 |
| DELETE | /api/v1/policies/{policy_id} | 禁用策略 |

## 事件
### 发布的事件
- `policy.created` — 策略创建
- `policy.updated` — 策略更新
- `policy.activated` — 策略激活
- `policy.triggered` — 策略触发
- `policy.simulated` — 策略模拟执行
- `policy.approval_required` — 策略审批请求
- `policy.approved` — 策略审批通过
- `policy.rejected` — 策略审批拒绝

### 订阅的事件
- `event.created` — 新事件触发策略匹配
- `alert.created` — 新告警触发响应策略
- `state.critical_detected` — 紧急状态触发自愈策略
- `automation.execution_completed` — 执行完成后更新策略执行记录

## 领域边界
- **不直接访问**其他领域的数据库表
- **通过事件总线**与其他领域通信
- **通过Service层**对外提供能力
