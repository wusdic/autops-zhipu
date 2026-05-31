# 通知中心（notification）

## 职责
管理平台内的通知消息，支持通知的创建、已读标记和批量已读操作。作为消息推送的统一出口，订阅各领域事件并生成用户可见的通知消息。

## 核心模型
| 模型 | 说明 |
|------|------|
| Notification | 通知记录，包含标题、内容、通知类型、渠道、接收人和已读时间 |

## API端点
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/notifications | 通知列表（支持按已读/未读筛选） |
| PATCH | /api/v1/notifications/{notification_id}/read | 标记通知已读/未读 |
| POST | /api/v1/notifications/read-all | 标记所有通知已读 |

## 事件
### 发布的事件
- `notification.sent` — 通知发送
- `notification.read` — 通知已读

### 订阅的事件
- `alert.created` — 新告警生成通知
- `alert.escalated` — 告警升级生成紧急通知
- `ticket.assigned` — 工单分配通知负责人
- `ticket.status_changed` — 工单状态变更通知相关人
- `automation.execution_completed` — 执行完成通知
- `automation.execution_failed` — 执行失败通知
- `policy.approval_required` — 策略审批请求通知

## 领域边界
- **不直接访问**其他领域的数据库表
- **通过事件总线**与其他领域通信
- **通过Service层**对外提供能力
