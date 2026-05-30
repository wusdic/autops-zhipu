# AUTOPS 安全架构设计

> 文档状态：current
> 是否为事实源：yes
> 建议路径：`docs/01-architecture/SECURITY_ARCHITECTURE.md`

---

## 1. 安全总则

AUTOPS 作为运维操作系统，拥有对生产环境的直接操作能力，安全是最高优先级。

**核心安全原则：**
1. 最小权限原则
2. 纵深防御
3. 默认拒绝
4. 审计不可篡改
5. AI 受控，不可绕过安全边界

---

## 2. 认证体系

### 2.1 JWT 认证

- **算法：** HS256 或 RS256（配置化）
- **Token 类型：** Access Token + Refresh Token
- **Access Token 有效期：** 可配置，默认 30 分钟
- **Refresh Token 有效期：** 可配置，默认 7 天
- **Token 载荷：** user_id, roles, scopes, exp, iat

### 2.2 密码策略

- 最小长度 8 位
- 必须包含大小写字母和数字
- 使用 bcrypt 或 argon2 哈希
- 支持密码过期策略
- 登录失败锁定（5 次失败锁定 30 分钟）

### 2.3 API Key 认证

- 用于系统集成和自动化场景
- Key 通过加密随机生成
- 存储时只保存哈希值
- 有作用域和有效期限制
- 支持 Key 撤销和轮换

### 2.4 会话管理

- 支持同时在线会话数限制
- 支持强制下线
- 异地登录检测
- 会话超时自动失效

---

## 3. 权限模型

### 3.1 RBAC（基于角色的访问控制）

**预定义角色：**

| 角色 | 说明 | 权限范围 |
|---|---|---|
| super_admin | 超级管理员 | 全部权限 |
| admin | 管理员 | 除安全配置外的全部权限 |
| operator | 运维工程师 | 资产、采集、告警、自动化（受限） |
| viewer | 只读用户 | 查看权限 |
| ai_operator | AI 操作员 | AI 分析、知识管理 |

### 3.2 权限定义

权限格式：`{domain}:{action}`

| 域 | 动作 | 说明 |
|---|---|---|
| asset | create, read, update, delete, discover | 资产管理 |
| config | create, read, update, delete, publish | 配置管理 |
| credential | create, read, test, bind, delete | 凭证管理 |
| collector | create, read, update, delete, execute | 采集管理 |
| alert | read, acknowledge, resolve, suppress, escalate | 告警管理 |
| policy | create, read, update, delete, simulate, execute | 策略管理 |
| automation | create, read, update, delete, execute, dry_run | 自动化管理 |
| aiops | analyze, read, feedback | AI 分析 |
| knowledge | create, read, update, delete, publish | 知识管理 |
| ticket | create, read, update, assign, close | 工单管理 |
| governance | user_mgmt, role_mgmt, audit_read, system_config | 平台治理 |
| execution | execute, approve, reject, cancel, force_stop | 执行控制 |

### 3.3 数据权限

- 按业务系统过滤资产
- 按环境过滤（生产/测试/开发）
- 按资产组过滤
- 告警只看自己负责范围

---

## 4. 凭证安全

### 4.1 加密方案

- **算法：** AES-256-GCM
- **主密钥管理：** 通过环境变量 `MASTER_ENCRYPTION_KEY` 注入，不写入代码和数据库
- **数据密钥：** 每次加密生成随机 data key，用主密钥加密后存储
- **密钥轮换：** 支持主密钥轮换，轮换时逐条重新加密

### 4.2 凭证生命周期

```text
创建 → 加密存储 → 绑定资产 → 使用时解密 → 使用审计 → 轮换/过期/删除
```

### 4.3 凭证使用约束

- AI 不读取明文凭证
- 凭证只在采集器/执行引擎中使用
- 每次使用记录审计日志
- 凭证导出时脱敏处理
- 凭证过期前通知

### 4.4 数据结构

```text
credentials 表:
  encrypted_data = AES-256-GCM-Encrypt(credential_json, data_key, iv)
  encryption_key_id → 指向加密所用的 data key（主密钥加密后的）
```

---

## 5. 动态脱敏

### 5.1 脱敏规则

| 字段类型 | 脱敏规则 | 示例 |
|---|---|---|
| 手机号 | 保留前3后4 | 138****1234 |
| 邮箱 | 保留首字母和域名 | a***@example.com |
| IP地址 | 根据权限决定 | 192.168.*.* 或完整 |
| 密码 | 完全隐藏 | ****** |
| API Key | 保留前4后4 | ak81****9k2n |
| 身份证 | 保留前3后4 | 110***********1234 |

### 5.2 实现方式

- 响应序列化时自动脱敏
- 基于用户权限决定脱敏级别
- 脱敏规则可配置
- API 返回的 `credential` 字段永远脱敏

---

## 6. 自动化安全

### 6.1 执行安全链

```text
执行请求
  ↓ 身份认证
  ↓ 权限检查
  ↓ 策略匹配
  ↓ 风险评估
  ↓ dry-run（可选）
  ↓ 审批（如需）
  ↓ 高危命令检查
  ↓ 并发锁检查
  ↓ 影响面检查
  ↓ 执行
  ↓ 实时日志
  ↓ 验证
  ↓ 审计记录
```

### 6.2 高危命令黑名单

```text
rm -rf /
dd if=... of=/dev/...
mkfs
fdisk
shutdown / reboot / halt
init 0 / init 6
:(){ :|:& };:  (fork bomb)
DROP DATABASE
DROP TABLE
TRUNCATE
DELETE FROM (without WHERE)
UPDATE (without WHERE)
```

黑名单可配置，支持正则匹配。

### 6.3 自动执行白名单

低风险动作可在策略允许范围内自动执行：
- 清理临时文件（指定目录）
- 压缩日志文件
- 服务健康检查
- 磁盘使用率查询

### 6.4 影响面控制

- 单次执行最大目标资产数可配置
- 超出限制必须分批执行
- 支持灰度执行（先 1 台 → 10% → 50% → 100%）

### 6.5 并发控制

- 同一资产同一类操作加分布式锁
- 同一策略的执行互斥
- 同一 Playbook 对同一资产不并发

---

## 7. AI 安全

### 7.1 AI 权限边界

| 能力 | 是否允许 | 说明 |
|---|---|---|
| 读取资产信息 | ✅ | 通过 Service 接口 |
| 读取状态/指标 | ✅ | 通过 Service 接口 |
| 读取告警/事件 | ✅ | 通过 Service 接口 |
| 读取日志 | ✅ | 通过 Service 接口，自动脱敏 |
| 读取凭证 | ❌ | 不可读取明文凭证 |
| 生成分析报告 | ✅ | 结构化输出 |
| 推荐动作 | ✅ | 推荐不等于执行 |
| 直接执行动作 | ❌ | 必须通过策略中心 |
| 绕过审批 | ❌ | 不可绕过 |
| 修改策略 | ❌ | 只能推荐 |

### 7.2 AI 工具调用审计

每次 AI 工具调用记录：
- tool_call_id
- 调用工具名称
- 输入参数
- 输出结果
- 触发来源（alert_id / ticket_id / user_id）
- 用户确认状态
- 策略校验结果
- 执行结果
- 耗时和 Token 用量

### 7.3 Prompt 注入防护

- 用户输入不直接拼接到 Prompt
- 使用结构化模板 + 参数填充
- AI 输出不直接执行，必须经过策略层

---

## 8. 网络安全

### 8.1 API 安全

- CORS 白名单配置
- Rate Limiting（每用户每分钟请求数限制）
- 请求大小限制
- SQL 注入防护（SQLAlchemy 参数化查询）
- XSS 防护（响应头 + 输入过滤）
- CSRF Token（Cookie 认证时）

### 8.2 WebSocket 安全

- 连接时必须携带有效 JWT
- 消息类型白名单
- 消息频率限制
- 连接超时自动断开

---

## 9. 审计日志

### 9.1 审计范围

| 操作类型 | 审计内容 |
|---|---|
| 用户认证 | 登录、登出、Token 刷新、登录失败 |
| 资产操作 | 创建、修改、删除、导入 |
| 配置变更 | 创建版本、发布、回滚 |
| 凭证操作 | 创建、测试、绑定、使用、删除 |
| 采集操作 | 手动触发、配置变更 |
| 告警操作 | 确认、关闭、抑制、升级 |
| 策略操作 | 创建、修改、发布、模拟 |
| 自动化执行 | 创建、审批、执行、取消、强制停止 |
| AI 分析 | 触发、工具调用、结果、反馈 |
| 工单操作 | 创建、指派、状态变更、关闭 |
| 用户管理 | 创建、角色变更、禁用 |
| 系统配置 | 参数修改、备份、恢复、升级 |

### 9.2 审计日志特性

- 不可篡改（只追加，不修改不删除）
- 包含完整上下文（who, what, when, where, result）
- 支持按时间、用户、操作类型查询
- 支持导出（合规审计）
- 保留周期可配置，默认 180 天

---

## 10. 安全配置

### 10.1 security.yaml 配置

```yaml
security:
  auth:
    jwt_algorithm: HS256
    access_token_expire_minutes: 30
    refresh_token_expire_days: 7
    max_login_attempts: 5
    lockout_minutes: 30

  password:
    min_length: 8
    require_uppercase: true
    require_lowercase: true
    require_digit: true
    require_special: false
    expire_days: 90

  encryption:
    algorithm: AES-256-GCM
    key_rotation_enabled: false

  rate_limit:
    enabled: true
    requests_per_minute: 120

  audit:
    retention_days: 180
    export_enabled: true

  automation:
    dangerous_commands_file: configs/dangerous_commands.yaml
    auto_execute_whitelist_file: configs/auto_execute_whitelist.yaml
    max_concurrent_per_asset: 1
    max_impact_assets: 50
    require_approval_for_risk: high
```

---

## 11. 安全检查清单

- [ ] 凭证加密存储
- [ ] 主密钥不写入代码
- [ ] AI 不读取明文凭证
- [ ] 所有执行有 execution_id
- [ ] 所有执行有审计日志
- [ ] 所有执行有实时日志
- [ ] 高危命令有黑名单
- [ ] 高危动作需要审批
- [ ] 支持 dry-run
- [ ] 支持回滚
- [ ] 支持并发锁
- [ ] 支持影响面控制
- [ ] API 有权限控制
- [ ] 敏感数据动态脱敏
- [ ] 审计日志不可篡改
- [ ] 登录有失败锁定
- [ ] Token 有过期机制
- [ ] WebSocket 有认证
