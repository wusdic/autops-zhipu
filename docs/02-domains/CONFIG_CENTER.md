# 配置与凭证中心 (Config & Credential Center)

> 文档状态：current
> 是否为事实源：yes
> 领域目录：`backend/app/domains/config/`

---

## 1. 职责

管理平台期望状态，包括采集配置、阈值、通知、策略、脚本、AI 模板和凭证。

## 2. 配置层级

```text
全局配置 (scope=global)
  ↓ 继承
组织/租户配置 (scope=organization)
  ↓ 继承
业务系统配置 (scope=business_system)
  ↓ 继承
资产组配置 (scope=asset_group)
  ↓ 继承
单资产配置 (scope=asset)
```

优先级：资产 > 资产组 > 业务系统 > 组织 > 全局

## 3. 配置能力

### 3.1 配置版本化

- 每次修改产生新版本
- 版本号自增
- 支持回滚到任意版本
- 版本间差异对比

### 3.2 配置发布

```text
draft → published → archived
```

- 发布前可预览影响范围
- 发布有审计记录
- 支持灰度发布（先部分资产）

### 3.3 配置漂移检测

- 采集配置事实与期望配置对比
- 发现漂移生成事件
- 支持自动修正

### 3.4 配置绑定

- 配置绑定到资产/资产组/业务系统
- 同一配置定义可多处绑定
- 绑定有优先级

## 4. 凭证能力

### 4.1 凭证类型

| 类型 | 说明 | 存储字段 |
|---|---|---|
| ssh_password | SSH 密码认证 | username, password |
| ssh_key | SSH 密钥认证 | username, private_key, passphrase |
| windows | Windows 认证 | username, password |
| snmp | SNMP 认证 | community/community_string, version |
| database | 数据库连接 | host, port, username, password, database |
| api_token | API Token | token, header_name |
| custom | 自定义 | 自定义字段 JSON |

### 4.2 凭证安全

- AES-256-GCM 加密存储
- 主密钥从环境变量加载
- 读取时解密，传输时脱敏
- 每次使用审计
- AI 不可读取明文

### 4.3 凭证测试

- 支持连接测试
- 测试结果记录
- 定期自动测试

## 5. 数据模型

见 `DATA_ARCHITECTURE.md` 3.3-3.4 节：
- config_definitions
- config_versions
- config_bindings
- config_drifts
- change_records
- credentials
- credential_bindings

## 6. API 设计

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/v1/config-definitions | 配置定义列表 |
| POST | /api/v1/config-definitions | 创建配置定义 |
| GET | /api/v1/config-definitions/{id}/versions | 配置版本列表 |
| POST | /api/v1/config-definitions/{id}/versions | 创建新版本 |
| POST | /api/v1/config-versions/{id}/publish | 发布版本 |
| POST | /api/v1/config-versions/{id}/rollback | 回滚版本 |
| GET | /api/v1/config-bindings | 绑定列表 |
| POST | /api/v1/config-bindings | 绑定配置 |
| GET | /api/v1/config-drifts | 漂移列表 |
| GET | /api/v1/credentials | 凭证列表（脱敏） |
| POST | /api/v1/credentials | 创建凭证 |
| POST | /api/v1/credentials/{id}/test | 测试凭证 |
| POST | /api/v1/credential-bindings | 绑定凭证到资产 |
| GET | /api/v1/change-records | 变更记录 |

## 7. 领域事件

| 事件 | 说明 |
|---|---|
| ConfigCreated | 配置创建 |
| ConfigVersionCreated | 新版本创建 |
| ConfigPublished | 配置发布 |
| ConfigRolledBack | 配置回滚 |
| ConfigDriftDetected | 配置漂移检测 |
| CredentialCreated | 凭证创建 |
| CredentialTested | 凭证测试 |
| CredentialUsed | 凭证使用 |

## 8. 与其他领域交互

| 领域 | 交互方式 | 说明 |
|---|---|---|
| asset | 配置绑定到资产 | service 调用 |
| collector | 采集任务使用配置版本 | service 调用 |
| policy | 策略引用配置 | service 调用 |
| automation | 执行时记录配置版本 | 事件订阅 |
| governance | 变更有审计 | 事件发布 |
