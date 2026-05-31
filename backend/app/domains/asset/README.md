# 资产中心（asset）

## 职责
管理 IT 资产的全生命周期，包括资产的注册、分组、关系拓扑和时间线。提供资产自动发现、批量导入和资产凭证/策略关联查询能力。

## 核心模型
| 模型 | 说明 |
|------|------|
| Asset | 资产主表，记录主机/网络设备/应用等资产基本信息、状态与健康度 |
| AssetIP | 资产 IP 地址，支持多 IP 绑定 |
| AssetGroup | 资产分组，支持树形层级结构 |
| AssetGroupMember | 资产分组成员关联表 |
| AssetRelation | 资产关系，记录资产间依赖/连接等拓扑关系 |
| AssetTimeline | 资产时间线，记录资产相关的事件变更历史 |

## API端点
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/assets | 资产列表（支持按类型/状态/健康度/业务系统/环境/关键字筛选） |
| POST | /api/v1/assets | 创建资产 |
| GET | /api/v1/assets/{asset_id} | 获取资产详情 |
| PUT | /api/v1/assets/{asset_id} | 更新资产 |
| DELETE | /api/v1/assets/{asset_id} | 删除资产 |
| POST | /api/v1/assets/import | 批量导入资产 |
| GET | /api/v1/assets/{asset_id}/relations | 获取资产关系列表 |
| POST | /api/v1/assets/{asset_id}/relations | 添加资产关系 |
| DELETE | /api/v1/assets/{asset_id}/relations/{relation_id} | 删除资产关系 |
| GET | /api/v1/assets/{asset_id}/timeline | 获取资产时间线 |
| GET | /api/v1/assets/{asset_id}/credentials | 获取资产关联凭证 |
| DELETE | /api/v1/assets/{asset_id}/credentials/{cred_id} | 解除资产凭证绑定 |
| GET | /api/v1/assets/{asset_id}/policies | 获取资产关联策略 |
| DELETE | /api/v1/assets/{asset_id}/policies/{policy_id} | 解除资产策略关联 |
| GET | /api/v1/assets/{asset_id}/collection-configs | 获取资产采集配置 |
| POST | /api/v1/assets/{asset_id}/collection-trigger | 触发资产采集 |
| GET | /api/v1/asset-groups | 资产分组列表 |
| POST | /api/v1/asset-groups | 创建资产分组 |
| GET | /api/v1/asset-groups/{group_id} | 获取分组详情 |
| POST | /api/v1/asset-groups/{group_id}/members | 添加分组成员 |
| DELETE | /api/v1/asset-groups/{group_id}/members/{asset_id} | 移除分组成员 |

## 事件
### 发布的事件
- `asset.created` — 资产创建
- `asset.updated` — 资产更新
- `asset.deleted` — 资产删除
- `asset.status_changed` — 资产状态变更
- `asset.health_changed` — 资产健康度变更
- `asset.discovered` — 资产自动发现
- `asset.relation_added` — 资产关系添加
- `asset.relation_removed` — 资产关系移除

### 订阅的事件
- `collector.job_completed` — 采集任务完成后更新资产信息
- `state.status_changed` — 状态变更后更新资产状态
- `config.version_published` — 配置变更后更新资产关联配置

## 领域边界
- **不直接访问**其他领域的数据库表
- **通过事件总线**与其他领域通信
- **通过Service层**对外提供能力
