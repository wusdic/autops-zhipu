# 平台治理中心 (Governance Center)

> 文档状态：current
> 是否为事实源：yes
> 领域目录：`backend/app/domains/governance/`

---

## 1. 职责

管理用户、角色、权限、API Key、审计、系统配置和平台健康。

## 2. 用户管理

### 2.1 用户属性

- 用户名（唯一）
- 邮箱（唯一，可选）
- 显示名
- 密码（bcrypt/argon2 哈希）
- 状态（active/disabled/locked）
- 最后登录时间

### 2.2 用户操作

- 创建、修改、删除（软删除）
- 启用/禁用
- 锁定/解锁
- 密码重置
- 批量导入

## 3. 角色与权限

### 3.1 预定义角色

| 角色 | 说明 |
|---|---|
| super_admin | 超级管理员，全部权限 |
| admin | 管理员，除安全配置外 |
| operator | 运维工程师，日常操作权限 |
| viewer | 只读查看 |
| ai_operator | AI 分析和知识管理 |

### 3.2 权限格式

`{domain}:{action}`，例如：
- `asset:read`
- `automation:execute`
- `policy:create`
- `governance:user_mgmt`

### 3.3 数据权限

- 按业务系统过滤
- 按环境过滤
- 按资产组过滤
- 管理员可看全部

## 4. API Key 管理

### 4.1 API Key 属性

- 名称
- Key 值（加密随机生成，只显示一次）
- Key 哈希（存储）
- Key 前缀（用于识别）
- 所属用户
- 作用域（权限范围）
- 有效期
- 状态

### 4.2 Key 使用

- 请求头 `X-API-Key: <key>`
- Key 认证后继承所属用户权限
- Key 作用域可限制为部分权限
- 过期自动失效

## 5. 审计日志

### 5.1 审计范围

覆盖所有敏感操作：
- 认证事件（登录、登出、失败）
- 资产操作（CRUD）
- 配置变更
- 凭证操作
- 策略操作
- 自动化执行
- AI 分析
- 工单操作
- 用户管理
- 系统配置

### 5.2 审计特性

- 不可篡改（只追加）
- 包含完整上下文
- 支持查询和导出
- 保留期可配置

## 6. 系统配置

| 配置项 | 说明 |
|---|---|
| 平台名称 | 可自定义 |
| 默认语言 | 中文/英文 |
| 会话超时 | 可配置 |
| 密码策略 | 最小长度、复杂度 |
| SLA 模板 | 响应时间、解决时间 |
| 备份策略 | 频率、保留期 |
| 安全基线 | 安全配置检查规则 |

## 7. 平台健康

### 7.1 组件监控

| 组件 | 检查方式 |
|---|---|
| 后端 API | /health, /ready |
| 数据库 | 连接查询 |
| Redis | PING |
| Worker | 最后活动时间 |
| 采集器 | 心跳 |
| AI 模型 | HTTP health |

### 7.2 平台指标

- API 请求量/错误率/响应时间
- 活跃告警数
- 执行成功率
- 采集成功率
- 在线用户数
- 系统资源使用

## 8. 数据模型

见 `DATA_ARCHITECTURE.md` 3.15 节：
- users
- roles
- user_roles
- api_keys

## 9. API 设计

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/v1/auth/login | 登录 |
| POST | /api/v1/auth/logout | 登出 |
| POST | /api/v1/auth/refresh | 刷新 Token |
| GET | /api/v1/auth/me | 当前用户信息 |
| PUT | /api/v1/auth/password | 修改密码 |
| GET | /api/v1/users | 用户列表 |
| POST | /api/v1/users | 创建用户 |
| PUT | /api/v1/users/{id} | 更新用户 |
| DELETE | /api/v1/users/{id} | 删除用户 |
| GET | /api/v1/roles | 角色列表 |
| POST | /api/v1/roles | 创建角色 |
| PUT | /api/v1/roles/{id} | 更新角色 |
| GET | /api/v1/api-keys | API Key 列表 |
| POST | /api/v1/api-keys | 创建 API Key |
| DELETE | /api/v1/api-keys/{id} | 撤销 API Key |
| GET | /api/v1/audit-logs | 审计日志查询 |
| GET | /api/v1/audit-logs/export | 审计日志导出 |
| GET | /api/v1/platform/status | 平台状态 |
| GET | /api/v1/platform/config | 系统配置 |
| PUT | /api/v1/platform/config | 更新配置 |
| POST | /api/v1/platform/backup | 触发备份 |
| POST | /api/v1/platform/self-check | 触发自检 |

## 10. 领域事件

| 事件 | 说明 |
|---|---|
| UserCreated | 用户创建 |
| UserUpdated | 用户更新 |
| UserLogin | 用户登录 |
| UserLoginFailed | 登录失败 |
| RoleCreated | 角色创建 |
| RoleUpdated | 角色更新 |
| ApiKeyCreated | API Key 创建 |
| ApiKeyRevoked | API Key 撤销 |
| SystemConfigChanged | 系统配置变更 |

## 11. 与其他领域交互

| 领域 | 交互方式 | 说明 |
|---|---|---|
| 所有领域 | 提供认证和权限检查 | 中间件依赖 |
| 所有领域 | 接收审计日志 | 事件订阅 |
| automation | 提供审批流程 | service 调用 |
| log | 审计日志存储 | service 调用 |
