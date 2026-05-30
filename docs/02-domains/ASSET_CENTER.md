# 资产中心 (Asset Center)

> 文档状态：current
> 是否为事实源：yes
> 领域目录：`backend/app/domains/asset/`

---

## 1. 职责

管理平台中所有可观测、可配置、可告警、可执行、可分析的对象。

## 2. 资产类型

| 类型 | 枚举值 | 说明 |
|---|---|---|
| Linux 主机 | linux_server | SSH 管理 |
| Windows 主机 | windows_server | WMI/WinRM 管理 |
| 网络设备 | network_device | SNMP 管理 |
| 安全设备 | security_device | 防火墙、IDS/IPS |
| 存储设备 | storage_device | SAN/NAS |
| 数据库 | database | MySQL/PostgreSQL/Oracle/达梦 |
| 中间件 | middleware | Redis/Kafka/Nginx/Tomcat |
| Web 服务 | web_service | HTTP/HTTPS 服务 |
| API 服务 | api_service | REST/gRPC 接口 |
| 容器 | container | Docker 容器 |
| K8s 工作负载 | k8s_workload | Pod/Deployment/Service |
| 虚拟化 | virtual_machine | VMware/KVM |
| 云资源 | cloud_resource | 云服务器/云数据库 |
| 业务系统 | business_system | 业务应用 |
| 外部依赖 | external_dependency | 第三方服务 |

## 3. 核心能力

### 3.1 资产生命周期

```text
discovered → registered → active → maintenance → inactive → decommissioned
```

### 3.2 资产发现

- 支持 IP 段扫描（ICMP/TCP）
- 支持 SNMP 发现
- 支持 Agent 注册
- 支持 CSV/Excel 导入
- 支持 API 批量导入

### 3.3 资产分组

- 静态分组：手动添加成员
- 动态分组：基于标签/属性自动匹配
- 分组支持层级结构
- 分组可用于策略范围和权限过滤

### 3.4 资产关系

关系类型：
- `depends_on`：依赖关系（应用 → 数据库）
- `contains`：包含关系（集群 → 节点）
- `runs_on`：运行关系（服务 → 主机）
- `connects_to`：连接关系（应用 → 中间件）
- `provides`：提供关系（主机 → 服务）

### 3.5 健康状态

| 状态 | 说明 |
|---|---|
| healthy | 所有采集正常，无告警 |
| warning | 有告警或采集异常 |
| critical | 不可达或有严重告警 |
| unknown | 未采集或数据过期 |

## 4. 数据模型

见 `DATA_ARCHITECTURE.md` 3.1-3.2 节：
- assets（资产主表）
- asset_ips（资产IP）
- asset_tags（资产标签）
- asset_groups（资产分组）
- asset_group_members（分组成员）
- asset_relations（资产关系）

## 5. API 设计

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/v1/assets | 资产列表（分页、过滤、搜索） |
| POST | /api/v1/assets | 创建资产 |
| GET | /api/v1/assets/{id} | 资产详情 |
| PUT | /api/v1/assets/{id} | 更新资产 |
| DELETE | /api/v1/assets/{id} | 删除资产（软删除） |
| POST | /api/v1/assets/import | 批量导入 |
| GET | /api/v1/assets/{id}/relations | 资产关系图 |
| POST | /api/v1/assets/{id}/relations | 添加关系 |
| GET | /api/v1/assets/{id}/timeline | 资产时间线 |
| GET | /api/v1/asset-groups | 分组列表 |
| POST | /api/v1/asset-groups | 创建分组 |
| POST | /api/v1/discovery-tasks | 创建发现任务 |
| GET | /api/v1/discovery-tasks/{id} | 发现任务状态 |

## 6. 领域事件

| 事件 | 说明 |
|---|---|
| AssetCreated | 资产创建 |
| AssetUpdated | 资产更新 |
| AssetDeleted | 资产删除 |
| AssetStatusChanged | 资产状态变更 |
| AssetRelationAdded | 资产关系添加 |
| AssetDiscovered | 资产发现完成 |

## 7. 与其他领域交互

| 领域 | 交互方式 | 说明 |
|---|---|---|
| config | 资产绑定采集模板、阈值配置 | config binding |
| collector | 采集目标为资产 | service 调用 |
| state | 资产状态由采集结果驱动 | 事件订阅 |
| alert | 告警关联资产 | service 调用 |
| policy | 策略适用范围基于资产 | service 调用 |
| automation | 自动化执行目标为资产 | service 调用 |
| knowledge | 知识库关联资产类型 | service 调用 |
