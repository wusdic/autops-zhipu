# 工单与协同中心 (Ticket Center)

> 文档状态：current
> 是否为事实源：yes
> 领域目录：`backend/app/domains/ticket/`

---

## 1. 职责

管理工单生命周期，连接告警、执行、AI 分析和知识沉淀。

## 2. 工单类型

| 类型 | 说明 | 来源 |
|---|---|---|
| incident | 故障工单 | 告警转工单、手动创建 |
| change | 变更工单 | 策略审批、手动创建 |
| task | 任务工单 | 手动创建 |
| knowledge_draft | 知识草稿 | 工单关闭后生成、AI 生成 |

## 3. 工单状态机

```text
open → assigned → in_progress → pending_approval → resolved → closed
  ↑                                            ↓
  └─────────────── rejected ←───────────────────┘
```

## 4. 工单来源

| 来源 | 触发条件 |
|---|---|
| 告警转工单 | 告警升级、手动转工单 |
| 策略触发工单 | 策略动作包含 create_ticket |
| 自动化失败转工单 | 执行失败 + failure_handling=create_ticket |
| 人工创建 | 用户手动创建 |
| AI 推荐 | AI 分析后推荐转工单 |

## 5. 工单上下文

工单应展示完整上下文：
- 关联告警（标题、时间线、指标）
- 关联事件
- 关联执行记录和日志
- AI 分析结果
- 资产信息
- 历史相似工单

## 6. SLA

| 优先级 | 响应时间 | 解决时间 |
|---|---|---|
| critical | 15 分钟 | 2 小时 |
| high | 30 分钟 | 4 小时 |
| medium | 2 小时 | 8 小时 |
| low | 4 小时 | 24 小时 |

SLA 时长可配置。

## 7. 知识沉淀

工单关闭时可选生成知识草稿：
1. 用户确认是否生成知识草稿
2. 系统自动汇总：告警摘要、处置步骤、结果
3. 生成知识草稿
4. 审核后发布为正式知识文章

## 8. 数据模型

见 `DATA_ARCHITECTURE.md` 3.12 节：
- tickets
- ticket_comments

## 9. API 设计

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/v1/tickets | 工单列表 |
| POST | /api/v1/tickets | 创建工单 |
| GET | /api/v1/tickets/{id} | 工单详情 |
| PUT | /api/v1/tickets/{id} | 更新工单 |
| POST | /api/v1/tickets/{id}/assign | 指派 |
| POST | /api/v1/tickets/{id}/comments | 添加评论 |
| GET | /api/v1/tickets/{id}/comments | 评论列表 |
| POST | /api/v1/tickets/{id}/resolve | 解决 |
| POST | /api/v1/tickets/{id}/close | 关闭 |
| POST | /api/v1/tickets/{id}/create-knowledge | 生成知识草稿 |
| GET | /api/v1/tickets/{id}/timeline | 工单时间线 |

## 10. 领域事件

| 事件 | 说明 |
|---|---|
| TicketCreated | 工单创建 |
| TicketAssigned | 工单指派 |
| TicketStatusChanged | 状态变更 |
| TicketCommentAdded | 评论添加 |
| TicketResolved | 工单解决 |
| TicketClosed | 工单关闭 |
| KnowledgeDraftCreated | 知识草稿生成 |

## 11. 与其他领域交互

| 领域 | 交互方式 | 说明 |
|---|---|---|
| alert | 告警转工单 | service 调用 |
| automation | 执行失败转工单 | 事件订阅 |
| aiops | 工单触发 AI 分析 | 事件发布 |
| knowledge | 工单关闭生成知识 | service 调用 |
| governance | 工单权限控制 | service 调用 |
