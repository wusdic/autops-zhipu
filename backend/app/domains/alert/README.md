# 告警中心（alert）

## 职责
管理告警规则的创建、更新和匹配触发，以及告警的确认、解决、升级和抑制。基于事件驱动模式实时生成告警，并提供告警统计概览。

## 核心模型
| 模型 | 说明 |
|------|------|
| AlertRule | 告警规则，定义事件类型匹配条件、严重级别、抑制时长和启用状态 |
| Alert | 告警记录，包含关联规则、触发事件、状态流转和升级信息 |

## API端点
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/alert-rules | 告警规则列表（支持按启用状态筛选） |
| POST | /api/v1/alert-rules | 创建告警规则 |
| PUT | /api/v1/alert-rules/{rule_id} | 更新告警规则 |
| PATCH | /api/v1/alert-rules/{rule_id} | 部分更新告警规则 |
| POST | /api/v1/alert-rules/{rule_id}/test | 测试告警规则（模拟触发） |
| GET | /api/v1/alerts | 告警列表（支持按状态/严重级别筛选） |
| POST | /api/v1/alerts | 手动创建告警 |
| GET | /api/v1/alerts/stats/overview | 告警统计概览 |
| GET | /api/v1/alerts/{alert_id} | 获取告警详情 |
| POST | /api/v1/alerts/{alert_id}/acknowledge | 确认告警 |
| POST | /api/v1/alerts/{alert_id}/resolve | 解决告警 |
| POST | /api/v1/alerts/{alert_id}/escalate | 升级告警 |

## 事件
### 发布的事件
- `alert.rule_created` — 告警规则创建
- `alert.rule_updated` — 告警规则更新
- `alert.created` — 告警生成
- `alert.acknowledged` — 告警确认
- `alert.resolved` — 告警解决
- `alert.escalated` — 告警升级
- `alert.suppressed` — 告警抑制

### 订阅的事件
- `event.created` — 新事件到达时匹配告警规则
- `state.critical_detected` — 紧急状态触发告警

## 领域边界
- **不直接访问**其他领域的数据库表
- **通过事件总线**与其他领域通信
- **通过Service层**对外提供能力
