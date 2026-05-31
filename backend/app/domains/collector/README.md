# 采集中心（collector）

## 职责
管理数据采集器的注册、健康监控和采集任务的调度执行。负责通过 SNMP/SSH/API 等协议采集资产状态数据，并将采集结果持久化。

## 核心模型
| 模型 | 说明 |
|------|------|
| Collector | 采集器，记录采集器类型、协议、调度间隔和健康状态 |
| CollectionJob | 采集任务，记录单次采集的目标资产、关联采集器和执行状态 |
| CollectionResult | 采集结果，存储采集任务返回的结构化数据 |

## API端点
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/collectors | 采集器列表 |
| POST | /api/v1/collectors | 注册采集器 |
| GET | /api/v1/collection-jobs | 采集任务列表（支持按资产ID筛选） |
| POST | /api/v1/collection-jobs | 创建采集任务 |
| GET | /api/v1/collection-jobs/{job_id}/results | 获取采集任务结果 |

## 事件
### 发布的事件
- `collector.registered` — 采集器注册
- `collector.health_changed` — 采集器健康状态变更
- `collector.job_created` — 采集任务创建
- `collector.job_completed` — 采集任务完成
- `collector.job_failed` — 采集任务失败
- `collector.job_timeout` — 采集任务超时

### 订阅的事件
- `asset.created` — 新资产创建时触发初始采集
- `config.version_published` — 配置变更后更新采集参数

## 领域边界
- **不直接访问**其他领域的数据库表
- **通过事件总线**与其他领域通信
- **通过Service层**对外提供能力
