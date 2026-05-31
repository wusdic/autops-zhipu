# 工单中心（ticket）

## 职责
管理运维工单的全生命周期，包括工单创建、分配、状态流转、评论和附件管理。支持工单升级和工单转知识库，实现运维问题的规范化跟踪与处理。

## 核心模型
| 模型 | 说明 |
|------|------|
| Ticket | 工单，记录标题、描述、类型、优先级、状态、负责人和关联资产 |
| TicketComment | 工单评论，记录工单处理过程中的沟通记录 |

## API端点
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/tickets | 工单列表（支持按状态/类型/负责人筛选） |
| POST | /api/v1/tickets | 创建工单 |
| GET | /api/v1/tickets/{ticket_id} | 获取工单详情 |
| PUT | /api/v1/tickets/{ticket_id} | 更新工单 |
| POST | /api/v1/tickets/{ticket_id}/comments | 添加工单评论 |
| GET | /api/v1/tickets/{ticket_id}/comments | 获取工单评论列表 |
| GET | /api/v1/tickets/{ticket_id}/attachments | 获取工单附件列表 |
| POST | /api/v1/tickets/{ticket_id}/attachments | 上传工单附件 |

## 事件
### 发布的事件
- `ticket.created` — 工单创建
- `ticket.updated` — 工单更新
- `ticket.assigned` — 工单分配
- `ticket.status_changed` — 工单状态变更
- `ticket.comment_added` — 工单评论添加
- `ticket.resolved` — 工单解决
- `ticket.closed` — 工单关闭
- `ticket.escalated` — 工单升级
- `ticket.converted_to_knowledge` — 工单转知识文章

### 订阅的事件
- `alert.created` — 高严重级别告警自动创建工单
- `alert.escalated` — 告警升级后升级关联工单
- `automation.execution_failed` — 执行失败自动创建工单

## 领域边界
- **不直接访问**其他领域的数据库表
- **通过事件总线**与其他领域通信
- **通过Service层**对外提供能力
