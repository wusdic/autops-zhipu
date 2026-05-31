# 状态中心（state）

## 职责
记录和追踪资产的运行状态快照与状态变更历史。通过定时采集或事件驱动检测状态变化，识别异常状态并触发恢复通知。

## 核心模型
| 模型 | 说明 |
|------|------|
| StateSnapshot | 状态快照，记录某时刻资产的某类状态（CPU/内存/网络等）数值 |
| StateChange | 状态变更，记录状态从旧值到新值的变化及变更时间 |

## API端点
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/states/snapshots | 记录状态快照 |
| GET | /api/v1/states/latest/{asset_id} | 获取资产最新状态 |
| GET | /api/v1/states/changes/{asset_id} | 获取资产状态变更历史（支持按状态类型筛选） |
| GET | /api/v1/states/changes | 全局状态变更列表（支持按状态类型筛选） |

## 事件
### 发布的事件
- `state.snapshot_recorded` — 状态快照记录
- `state.status_changed` — 状态变更
- `state.critical_detected` — 检测到紧急状态
- `state.recovered` — 状态恢复正常

### 订阅的事件
- `collector.job_completed` — 采集完成后记录状态快照
- `alert.resolved` — 告警恢复后更新资产状态

## 领域边界
- **不直接访问**其他领域的数据库表
- **通过事件总线**与其他领域通信
- **通过Service层**对外提供能力
