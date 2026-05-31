# 配置与凭证中心（config）

## 职责
管理 IT 资产的配置定义、版本发布、配置绑定及凭证生命周期。支持配置版本控制、配置漂移检测和凭证与资产的安全绑定。

## 核心模型
| 模型 | 说明 |
|------|------|
| ConfigDefinition | 配置定义，定义配置项的名称、类型、默认内容等元信息 |
| ConfigVersion | 配置版本，记录每个配置定义的版本化内容和发布状态 |
| ConfigBinding | 配置绑定，将配置版本关联到目标资产 |
| Credential | 凭证，存储 SSH/SNMP/API Key 等认证信息的加密记录 |
| CredentialBinding | 凭证绑定，将凭证关联到目标资产 |

## API端点
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/configs/definitions | 配置定义列表（支持按类型筛选） |
| POST | /api/v1/configs/definitions | 创建配置定义 |
| GET | /api/v1/configs/definitions/{def_id} | 获取配置定义详情 |
| POST | /api/v1/configs/definitions/{def_id}/versions | 创建配置版本 |
| GET | /api/v1/configs/definitions/{def_id}/versions | 获取配置版本列表 |
| POST | /api/v1/configs/versions/{version_id}/publish | 发布配置版本 |
| GET | /api/v1/configs/inheritance | 获取配置继承关系 |
| GET | /api/v1/credentials | 凭证列表（支持按类型筛选） |
| POST | /api/v1/credentials | 创建凭证 |
| GET | /api/v1/credentials/{cred_id} | 获取凭证详情 |
| POST | /api/v1/credentials/{cred_id}/bind | 将凭证绑定到目标资产 |

## 事件
### 发布的事件
- `config.version_created` — 配置版本创建
- `config.version_published` — 配置版本发布
- `config.binding_created` — 配置绑定创建
- `config.drift_detected` — 配置漂移检测
- `config.credential_created` — 凭证创建
- `config.credential_tested` — 凭证测试结果

### 订阅的事件
- `asset.created` — 新资产创建时自动关联默认配置
- `collector.job_completed` — 采集完成后对比配置是否漂移

## 领域边界
- **不直接访问**其他领域的数据库表
- **通过事件总线**与其他领域通信
- **通过Service层**对外提供能力
