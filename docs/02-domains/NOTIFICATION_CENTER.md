# AUTOPS 通知中心设计

> 文档路径：`docs/02-domains/NOTIFICATION_CENTER.md`
> 状态：current | 事实源：yes
> 反向同步时间：2026-05-31

---

## 1. 职责定义

通知中心负责管理平台内向用户推送的所有通知消息，包括告警通知、执行完成通知、工单变更通知和系统通知。

**核心职责：**
- 接收各领域产生的通知事件
- 管理通知的已读/未读状态
- 通过 WebSocket 实时推送给在线用户
- 支持按类型筛选和批量标记已读

**边界：**
- 不负责通知的触发逻辑（由各领域自行决定何时发通知）
- 不负责外部渠道推送（邮件、短信等，属于 M5 增强阶段）
- 通知内容由调用方构造，通知中心只负责投递和状态管理

---

## 2. 数据模型

### 2.1 notifications 表

| 列名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | VARCHAR(36) | PK | UUID |
| user_id | VARCHAR(36) | NOT NULL, FK→users.id | 接收用户 |
| type | VARCHAR(16) | NOT NULL | 通知类型：alert / execution / ticket / system |
| title | VARCHAR(128) | NOT NULL | 通知标题 |
| message | TEXT | | 通知内容 |
| link | VARCHAR(255) | | 跳转链接 |
| ref_id | VARCHAR(36) | | 关联实体ID（告警ID/执行ID/工单ID） |
| read_at | DATETIME | NULL | 已读时间（NULL=未读） |
| created_at | DATETIME | NOT NULL, DEFAULT now() | 创建时间 |

### 2.2 通知类型枚举

| type | 说明 | 触发来源 |
|---|---|---|
| alert | 告警通知 | 新告警创建、告警升级 |
| execution | 执行通知 | 自动化执行完成/失败 |
| ticket | 工单通知 | 工单创建、状态变更、新评论 |
| system | 系统通知 | 备份完成、平台异常 |

---

## 3. API 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/notifications` | 获取当前用户通知列表（支持 type 筛选） |
| PATCH | `/api/v1/notifications/{id}/read` | 标记单条已读 |
| POST | `/api/v1/notifications/read-all` | 全部标记已读 |

---

## 4. WebSocket 实时推送

### 4.1 连接

- 路径：`/api/v1/ws`
- 认证：通过 query 参数传递 token
- 心跳：30秒 ping/pong

### 4.2 事件类型

| 事件 | 方向 | 说明 |
|---|---|---|
| `notification.new` | 服务端→客户端 | 新通知 |
| `alert.created` | 服务端→客户端 | 新告警 |
| `alert.status_changed` | 服务端→客户端 | 告警状态变更 |
| `execution.started` | 服务端→客户端 | 执行开始 |
| `execution.completed` | 服务端→客户端 | 执行完成 |
| `execution.log` | 服务端→客户端 | 实时日志行 |
| `ticket.created` | 服务端→客户端 | 新工单 |
| `ticket.updated` | 服务端→客户端 | 工单更新 |
| `state.changed` | 服务端→客户端 | 资产状态变更 |
| `policy.triggered` | 服务端→客户端 | 策略触发 |
| `system.health` | 服务端→客户端 | 平台健康状态 |

---

## 5. 前端组件

### 5.1 NotificationBell

- 位置：`shared/components/NotificationBell.vue`
- 功能：头部通知铃铛图标，显示未读数角标
- 交互：点击弹出通知面板，支持分类Tab（全部/告警/执行/工单/系统）
- WebSocket：实时接收新通知，自动更新未读数

### 5.2 WebSocket 服务

- 位置：`shared/api/websocket.ts`
- 功能：自动连接、心跳、重连、事件分发
- 使用：在 MainLayout.vue 的 onMounted 中初始化

---

## 6. 交互流程

```
告警产生 → 告警中心调用 notification service.create()
         → 写入 notifications 表
         → 通过 WebSocket 推送给相关用户
         → 前端 NotificationBell 收到通知
         → 用户点击查看 → 跳转到告警详情
```
