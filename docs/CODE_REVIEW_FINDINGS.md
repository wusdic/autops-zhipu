# AUTOPS 代码全面审查报告

> 审查范围：`wusdic/autops-zhipu` 全仓库（后端 FastAPI + 前端 Vue3 + 部署/文档）
> 审查日期：2026-06-25
> 审查方法：逐层走查核心基础设施（认证/事件/执行/加密）、抽样领域模块、对照 README 与 docs 声明的项目目标核验一致性。

本报告按 **严重程度** 分层组织，每条问题给出：问题描述 → 证据（文件:行）→ 影响 → 修正建议。
严重程度定义：

- 🔴 **Critical**：安全漏洞 / 数据损坏 / 生产不可用 / 与核心目标声明严重不符
- 🟠 **High**：明确的功能性 Bug / 越权 / 一致性破坏
- 🟡 **Medium**：可靠性、性能、可维护性问题
- 🔵 **Low**：规范、体验、文档类问题

---

## 一、安全与鉴权（最高优先级）

### 🔴 S1. 认证中间件不校验用户状态，禁用/删除用户在 Token 有效期内仍可访问

- **证据**：`backend/app/common/auth_middleware.py:75-89` —— 中间件只 `decode_token` 拿到 `sub`，注入 `request.state.user_id` 后即放行，**不查库、不校验 `is_deleted`/`status`**。
- **对比**：真正会校验用户状态的 `require_auth`（`auth_dependency.py:47`）**从未被挂载到任何路由**（`grep require_auth` 仅出现在定义文件），而 `require_admin` 只覆盖约 7 处管理端点。
- **影响**：Access Token 有效期默认 **1440 分钟（24h）**（`config.py:106`），且系统**无 Token 撤销/黑名单机制**。管理员禁用或删除某用户后，该用户手中的旧 Token 仍可在 24 小时内访问绝大多数业务接口。修改密码同样不会使旧 Token 失效。
- **建议**：
  1. 中间件改为加载用户并校验 `is_deleted/status`（或在 `require_auth` 真正全局挂载后由其负责）；
  2. 引入 Token 版本号 / `token_version` 字段（密码变更、禁用、登出时自增），`decode_token` 时比对；或引入 Redis 黑名单；
  3. 缩短 access token 有效期（如 15–60 分钟），配合前端 refresh 流程。

### 🔴 S2. 任意已认证用户可越权修改任意用户（含角色、状态）→ 提权

- **证据**：`backend/app/domains/governance/api.py:125-130` `update_user` **没有 `require_admin`、也没有本人校验**；`UserUpdate`（`schemas.py:30-34`）包含 `status` 与 `role_ids`，`service.py:137-150` 会直接写入并重建角色绑定。
- **影响**：任何登录用户（哪怕 viewer 角色）可调用 `PUT /users/{任意id}`，把自己的 `role_ids` 改成 admin 角色，或把他人账号 `status` 改为禁用。**这是一个直接的水平/垂直越权（IDOR + 提权）漏洞**。
- **同类**：`list_users`（`api.py:98`）、`get_user`（`api.py:119`）无任何鉴权 → 全量用户 PII 泄露；`list_roles`（`api.py:140`）无鉴权 → 权限矩阵泄露。
- **建议**：`update_user`/`list_users`/`get_user`/`list_roles` 加 `dependencies=[Depends(require_admin)]`；普通用户改资料应走独立的 `/auth/me`-类自助接口，且禁止改 `status`/`role_ids`。

### 🔴 S3. 资产发现/纳管端点完全无鉴权 → 任意用户可发起网段扫描并自动建资产

- **证据**：`backend/app/domains/asset/discovery_api.py:22-96` 所有端点（`create_task`/`start`/`onboard`/`import`）均无 `require_admin`；而 `asset/api.py:102,157,186` 的等价建资产/导入端点是受 `require_admin` 保护的——**鉴权策略自相矛盾**。
- **放大因素**：`auto_onboard` 默认 `True`（`discovery_service.py:170`），创建任务即自动扫描 + 自动纳管；`ip_range` **无目标白名单约束**，可展开至 1024 个 IP（`discovery_service.py:56`）并对其 ICMP/TCP 扫描。
- **影响**：任意登录用户可把平台当作内网扫描器（合规/滥用风险，近似 SSRF），并污染资产库。
- **建议**：发现/纳管/导入端点统一加 `require_admin`；对 `ip_range` 增加允许网段白名单校验；`auto_onboard` 默认值与权限需重新评估。

### 🔴 S4. 生产环境无可用的自动化执行器，"执行层已实现"与代码不符

- **证据**：`automation/service.py:31` 硬编码 `_executor = LocalDevExecutor()`；`executor/local_dev.py:56-61` 在 `env == "prod"` 时 **直接 `raise RuntimeError`**；仓库中**不存在任何 SSH / 沙箱执行器实现**（`executor/` 目录仅 `base.py` + `local_dev.py`）。
- **影响**：README 宣称"自动化执行 ✅ 已实现""M0-M5 全部完成，执行层已实现"，但**生产环境每次 `execute()` 都会抛异常**，核心闭环（…→自动化执行→…）在生产不可用。所谓"已验证的端到端事件链路"实际只在 dev 进程内模式下成立。
- **建议**：要么实现生产级执行器（SSH/Agent/沙箱）并通过配置选择，要么在 README/文档中将自动化执行明确标注为"仅开发态/预览"，避免目标声明误导。

### 🟠 S5. `decode_token` / 中间件不校验 token `type`，refresh token 可当 access token 使用

- **证据**：`auth.py:46-53` `decode_token` 不检查 `type`；中间件（`auth_middleware.py:76-86`）也只看 `sub`。只有 `AuthService.refresh_token`（`service.py:83`）单独校验了 `type=="refresh"`。
- **影响**：长有效期（7 天）的 refresh token 可直接作为 Bearer 访问所有受中间件保护的业务接口，扩大了 token 泄露的危害面。
- **建议**：中间件/`require_auth` 显式要求 `payload["type"] == "access"`。

### 🟠 S6. JWT/敏感 token 通过 URL query 参数传递

- **证据**：`governance/api.py:57`(`refresh`)、`192-235`（`create_api_key`/`revoke_api_key`/`patch_api_key`）均以 `token: str` 作为查询参数接收 JWT。
- **影响**：Token 进入 Nginx/网关访问日志、浏览器历史、Referer，易泄露。（注意：`change_password`、`me` 已改为从 Header 读取，但这几个端点遗漏。）
- **建议**：统一从 `Authorization` Header 读取（或直接用中间件注入的 `request.state.user_id`），移除 query 形式的 token。

### 🟠 S7. 缺少登录限流 / 账户锁定

- **证据**：`AuthService.login`（`service.py:42-65`）密码错误仅抛异常，无失败计数、无锁定、无验证码、无 IP 限流。`GovernanceEvents.USER_LOCKED` 事件常量已定义但无人触发。
- **影响**：账户可被在线暴力破解。
- **建议**：基于 Redis 实现失败次数累计与临时锁定/退避，并发 `USER_LOCKED` 事件落审计。

### 🟠 S8. WebSocket 广播无频道级授权，存在跨用户/跨租户数据泄露

- **证据**：`api/websocket.py:124-167` 任意持有有效 token 的连接可 `subscribe` 任意频道（`alerts`/`executions`/`events`），`broadcast`（`:77`）向所有订阅者发送**全平台**事件，无任何按资产/租户/角色的过滤。
- **影响**：低权限用户可订阅到全平台告警、执行结果、事件流。
- **建议**：在订阅与推送两端加入授权过滤（按用户可见资产/租户/角色裁剪 payload 或频道）。

### 🟡 S9. 凭证加密每次操作都跑 60 万次 PBKDF2，存在严重性能隐患

- **证据**：`common/crypto.py:21,44-66` 每条凭证 **加密和解密都** 以 per-credential 随机盐执行 600,000 次 PBKDF2-SHA256，无法缓存派生密钥。
- **影响**：采集/执行场景需频繁解密资产凭证时，每次约数十毫秒 CPU 开销，批量解密 N 条 = N×600k 次哈希，可成为吞吐瓶颈，并易被高频解密放大为 CPU DoS。
- **建议**：凭证加密应使用"主密钥直接作为 KEK + 数据密钥"或固定/低频派生 + 缓存；PBKDF2 适用于"由口令派生"，不适用于已是高熵主密钥的场景。可改为 `Fernet(base64(master_key))` 或 HKDF（开销极小）。

### 🟡 S10. 前端 JWT 存于 localStorage

- **证据**：`frontend/src/shared/api/client.ts:15`、`config.ts` `TOKEN_KEY`。
- **影响**：任何 XSS 都能窃取可访问基础设施的长效 token。
- **建议**：考虑 HttpOnly Cookie + CSRF 防护，或至少缩短 token 寿命并启用 refresh 轮换。

---

## 二、正确性 / 功能性 Bug

### 🟠 B1. 多行脚本 / Playbook 实际无法执行

- **证据**：`automation/service.py:395-418`：
  - playbook 分支把 `pb.steps`（结构化步骤的 JSON 字符串）整体当作 `command` 传给执行器（`:397,411`），执行器再 `shlex.split` 这段 JSON —— 不可能正确执行。
  - 脚本分支把整段 `script.content` 当作单条命令；而 `local_dev.py:64` 检测到 `\n` 等 shell 元字符会直接拒绝，**任何多行脚本必被 block**。
- **影响**：自动化中心对外宣称支持脚本库/Playbook，但实质只能跑"单行、无管道/重定向"的命令。
- **建议**：playbook 需按 step 逐条解析执行；脚本需定义清晰的执行语义（解释器 + stdin 投喂，而非拼成一条命令行）。

### 🟠 B2. "需要审批"的风险命令未被强制拦截，PENDING 执行可直接运行

- **证据**：`command_policy.py` 计算出的 `requires_approval` 仅用于 dry-run 输出（`local_dev.py:32-52`），真实 `execute()`（`local_dev.py:54-103`）只看 `policy_result.allowed`，**不看 `requires_approval`**；`service.run_execution`（`service.py:380`）允许 `PENDING` 或 `APPROVED` 状态直接执行，**没有"中/高风险必须先 APPROVED"的强约束**。
- **影响**：标注为"需审批"的中风险命令（如 `systemctl stop`、`rm`）在未经审批时仍会执行。审批机制形同虚设。
- **建议**：`run_execution` 在执行前重新评估命令策略，若 `requires_approval` 且当前非 `APPROVED` 则拒绝并置为待审批。

### 🟠 B3. `EventBus.replay_pending` 写入不存在的列 `error`

- **证据**：`common/events.py:268-271` 失败分支 `UPDATE event_outbox SET status='dead', error='replay_failed'`，但 `event_outbox` 表只有 `last_error` 列（迁移 `0002_event_outbox.py:41`，且 `outbox.py` 全程用 `last_error`）。
- **影响**：一旦 replay 中某事件 handler 抛错，进入该分支会触发 `Unknown column 'error'`，replay 整体失败。
- **建议**：改为 `last_error`，并补充对应单测。

### 🟠 B4. 自动纳管发布事件未复用业务事务，存在"事件先于数据提交"的竞态

- **证据**：`discovery_service.onboard_results:464-476` 发布 `ASSET_CREATED` 时 **未传 `session`**，`events._persist_to_outbox` 会用独立 session 立即提交 outbox（`events.py:217-223`）；而 Asset 行此时还在 `_auto_onboard_task` 的事务里未提交（commit 在 `:510`）。
- **对比**：`workers/scheduler.run_collection_for_asset:209-224` 正确地把 `session=` 传入 publish 实现原子性。
- **影响**：Worker 消费到 `ASSET_CREATED` 后执行立即采集，可能查不到尚未提交的 Asset（`scheduler.on_asset_created_run_collection:320` 找不到则直接 return），导致纳管后首次采集被静默跳过。
- **建议**：`onboard_results`/`import_asset` 的 `publish` 统一传入 `self.db`，与业务数据原子提交。

### 🟡 B5. 时间比较 UTC（Python）与 `NOW()`（DB）混用

- **证据**：`outbox.py:60`（租约回收用 DB `NOW()`）与 `:84`（`locked_until` 用 Python `datetime.now(timezone.utc)`）混用；`crypto`/各处 `datetime.now(timezone.utc)` 与 SQL `NOW()` 并存。
- **影响**：当 DB 会话时区非 UTC 时，租约过期判断、`next_retry_at` 比较可能偏移，导致事件提前/延迟重试或租约误回收。
- **建议**：统一时间源（要么全用 DB `UTC_TIMESTAMP()`/`NOW()`，要么全用应用层 UTC 并确保连接时区为 UTC）。

### 🟡 B6. 采集调度全量串行 + 单事务，扩展性差且与注释不符

- **证据**：`scheduler._run_all_assets:269-301` 一次性 `select` 全部未删除资产，**串行**逐个采集，**最后统一一次 commit**；注释写"遍历所有在线资产"但查询并未过滤 online。
- **影响**：资产规模上千时单轮耗时长、长事务占用连接；任一环节异常回滚会丢整批结果。
- **建议**：分页/分批 + 受限并发 + 每资产独立小事务；修正注释或加 `status` 过滤。

### 🟡 B7. 前端 401 拦截直接登出，未使用已有的 refresh 流程

- **证据**：`client.ts:36-39` 收到 401 即清 token 跳登录；后端已实现 `/auth/refresh`，前端未接入。
- **影响**：access token（24h）一过，用户被强制重新登录，refresh token 形同摆设。
- **建议**：在拦截器中实现一次性 refresh 重试队列。

---

## 三、架构 / 平台级问题

### 🟠 A1. 多租户为"空壳"——有租户管理 UI/接口，但数据层无租户隔离

- **证据**：存在 `TenantManagementPage.vue`、`platform_extra.tenant_router`；但 `grep tenant_id` 在**所有领域模型中均无**该字段（全仓仅 11 处引用，集中在 tenant 自身），资产/告警/执行等核心表无 `tenant_id`，查询也无租户过滤。
- **影响**：若多租户是产品目标，则当前实现无法做任何数据隔离；若不是目标，则该 UI/接口为误导性"伪功能"。
- **建议**：明确多租户是否在范围内。若在范围内需引入租户维度（字段 + 查询过滤 + 行级隔离）；若不在范围内应移除/标注。

### 🟠 A2. 存在两套并行且不自洽的认证实现，`require_auth` 为死代码

- **证据**：`auth_middleware` 注入 `request.state.user_id`（字符串）；`auth_dependency.require_auth/get_current_user` 用 `request.state.current_user`（User 对象），但 `require_auth` 从未挂载；`AuthService.get_current_user` 又是第三套（重复 decode + 查库）。`get_current_user`（`auth_dependency.py:77`）仅在 require_admin 跑过时才有值，否则抛"未认证"——若有路由只依赖它而不挂 require_admin，会出现已登录却被拒。
- **影响**：鉴权语义分散、易踩坑、难以统一加固（如 S1/S5）。
- **建议**：收敛为单一认证入口（建议中间件加载并校验用户，统一注入 `current_user`），删除死代码。

### 🟡 A3. `get_db` 依赖无条件 commit，掩盖只读语义并放大副作用

- **证据**：`infra/database.py:62-68` 每个请求结束**无条件 commit**；服务层（如 `discovery_service.start_task:213`）还会在请求中途自行 `commit`。
- **影响**：只读请求也产生提交；中途 commit 让"请求级事务"边界模糊，异常回滚不再覆盖全请求，配合 B4 类问题更易出数据不一致。
- **建议**：只读端点避免写；统一事务边界，服务层不擅自 commit（由依赖层统一管理）。

### 🟡 A4. 命令安全策略的允许清单与判定逻辑存在缺口

- **证据**：`command_policy.py`：
  - `curl`/`wget` 被列为低风险免审批（`:103-104`），可用于数据外传/下载载荷/SSRF；
  - 路径授权仅黑名单 `FORBIDDEN_PATHS`（`:61-74`）+ 通常为空的 `allowed_paths`，导致 `cat /root/.ssh/id_rsa` 这类读取**未被禁止的敏感文件**按低风险放行；
  - 诊断判定 `cmd_prefix == d.split()[0]`（`:248-251`）较宽松，依赖 medium 列表兜底，扩展命令时易误判。
- **影响**：即便仅在 dev 执行器生效，仍是值得收紧的安全面（且未来若复用此策略到生产执行器，缺口会被继承）。
- **建议**：改为严格白名单（命令 + 子命令 + 参数模式）；`curl/wget` 提级；强制 `allowed_paths` 非空才允许文件类命令。

### 🔵 A5. CORS 默认 `["*"]`、OpenAPI UI 默认开启

- **证据**：`config.py:155,158`；生产经 `env==prod` 硬化会拒绝 `*`（`:202`），但默认 dev 态宽松。
- **建议**：保持现有 prod 硬化，文档强调部署必须设 `AUTOPS_ENV=prod` 才会触发硬化（否则全套默认值偏宽松）。

---

## 四、规范 / 一致性 / 文档

### 🔵 D1. README 的能力声明与代码实现存在多处夸大

- 自动化执行（见 S4）、多租户（A1）、"M0-M5 全部完成"、"已验证端到端链路"等表述需按实际可用范围（dev/prod）重新校准。`项目统计` 中的端点/页面数也建议以脚本自动统计，避免漂移。

### 🔵 D2. 鉴权装饰覆盖不一致

- 同类"创建/删除/导入"操作，asset 域受 `require_admin` 保护而 discovery 域不受（S3）；建议建立"高危端点清单 + 统一鉴权"的检查项纳入 `PR_CHECKLIST`。

### 🔵 D3. 大量 service 内部 `from ... import` 延迟导入

- 普遍存在函数内导入（如 `governance/api.py` 多处、`scheduler.py`、`crypto` 等）。少量为破循环依赖可接受，但大面积使用会降低可读性并掩盖真实依赖关系。建议梳理模块依赖、上移可静态化的导入。

### 🔵 D4. `auth/logout` 为纯空操作

- `governance/api.py:51-53` logout 不做任何服务端失效（与 S1 无撤销机制一致）。前端清本地 token 后，服务端 token 仍有效。建议配合 token 版本/黑名单实现真正登出。

---

## 五、修复优先级建议（Roadmap）

| 优先级 | 项 | 说明 |
|---|---|---|
| P0 | S2, S3 | 直接越权/提权与无鉴权扫描，应立即修复 |
| P0 | S1, S5 | 认证根基：用户状态校验 + token 类型/撤销 |
| P0 | S4 / D1 | 生产执行器缺失，须实现或如实降级声明 |
| P1 | B1, B2, B3, B4 | 自动化与事件链路的功能性 Bug |
| P1 | S6, S7, S8 | token 泄露面、暴力破解、WS 越权 |
| P2 | S9, B5, B6, A2, A3 | 性能、事务、架构收敛 |
| P3 | A1, A4, A5, D2-D4 | 架构定位、策略收紧、规范一致性 |

---

## 附：本次审查已实际走读的关键文件

- 基础设施：`main.py`、`infra/config.py`、`infra/database.py`
- 认证鉴权：`common/auth.py`、`auth_middleware.py`、`auth_dependency.py`、`governance/{api,service,schemas}.py`
- 事件/Outbox：`common/events.py`、`common/outbox.py`（+迁移 `0002`）、`api/websocket.py`
- 执行/策略：`automation/service.py`、`automation/command_policy.py`、`executor/{base,local_dev}.py`、`aiops/tools/{guard,execution}.py`
- 采集/发现：`workers/scheduler.py`、`asset/discovery_service.py`、`asset/discovery_api.py`
- 加密：`common/crypto.py`
- 前端：`shared/api/client.ts`、`shared/config.ts`
- 工程化：`.github/workflows/ci.yml`、`pyproject.toml`

> 说明：仓库规模较大（后端 ~280 文件、前端 ~240 文件），本报告聚焦核心链路与高风险面进行深度走查并抽样验证。建议将上述 P0/P1 项补充对应回归测试后再逐项修复。
