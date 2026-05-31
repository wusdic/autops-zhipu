# 治理中心（governance）

## 职责
管理平台的用户认证、角色权限和 API Key 生命周期。提供 JWT 登录认证、用户/角色 CRUD、基于 RBAC 的权限控制和 API Key 管理，是平台安全治理的核心领域。

## 核心模型
| 模型 | 说明 |
|------|------|
| User | 用户，记录用户名、密码哈希、邮箱、状态和锁定信息 |
| Role | 角色，定义角色名称、显示名和权限列表（JSON） |
| UserRole | 用户角色关联，实现多对多的用户-角色绑定 |
| ApiKey | API 密钥，记录密钥名称、哈希值、作用域和过期时间 |

## API端点
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/login | 用户登录 |
| POST | /api/v1/auth/logout | 用户登出 |
| POST | /api/v1/auth/refresh | 刷新 Token |
| GET | /api/v1/auth/me | 获取当前用户信息 |
| PUT | /api/v1/auth/password | 修改密码 |
| GET | /api/v1/users | 用户列表 |
| POST | /api/v1/users | 创建用户 |
| GET | /api/v1/users/{user_id} | 获取用户详情 |
| PUT | /api/v1/users/{user_id} | 更新用户 |
| DELETE | /api/v1/users/{user_id} | 删除用户 |
| GET | /api/v1/roles | 角色列表 |
| POST | /api/v1/roles | 创建角色 |
| GET | /api/v1/api-keys | API Key 列表 |
| POST | /api/v1/api-keys | 创建 API Key |
| DELETE | /api/v1/api-keys/{key_id} | 撤销 API Key |
| PATCH | /api/v1/api-keys/{key_id} | 部分更新 API Key |

## 事件
### 发布的事件
- `governance.user_created` — 用户创建
- `governance.user_updated` — 用户更新
- `governance.user_login` — 用户登录
- `governance.user_locked` — 用户锁定
- `governance.role_created` — 角色创建
- `governance.role_updated` — 角色更新
- `governance.api_key_created` — API Key 创建
- `governance.api_key_revoked` — API Key 撤销

### 订阅的事件
- （暂无订阅其他领域事件，治理中心作为基础设施工具域独立运行）

## 领域边界
- **不直接访问**其他领域的数据库表
- **通过事件总线**与其他领域通信
- **通过Service层**对外提供能力
