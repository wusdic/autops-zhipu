# 事件中心（event）

## 职责
统一管理平台内所有运维事件的接入、存储、去重和查询。作为事件驱动架构的核心枢纽，为告警、策略等下游领域提供标准化的事件数据源。

## 核心模型
| 模型 | 说明 |
|------|------|
| Event | 事件记录，包含事件类型、关联资产、严重级别、事件来源和原始数据 |

## API端点
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/events | 事件列表（支持按类型/资产ID/严重级别筛选） |
| POST | /api/v1/events | 创建事件 |
| GET | /api/v1/events/{event_id} | 获取事件详情 |

## 事件
### 发布的事件
- `event.created` — 事件创建
- `event.deduplicated` — 事件去重

### 订阅的事件
- `collector.job_completed` — 采集异常时自动生成事件
- `state.critical_detected` — 紧急状态检测时生成事件
- `state.status_changed` — 状态变更时生成事件
- `automation.execution_failed` — 执行失败时生成事件

## 领域边界
- **不直接访问**其他领域的数据库表
- **通过事件总线**与其他领域通信
- **通过Service层**对外提供能力
