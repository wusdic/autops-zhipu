# AUTOPS 前后端集成验证规范

> 文档状态：current  
> 建议路径：`docs/05-implementation/FRONTEND_BACKEND_INTEGRATION.md`  
> 本文件定义前后端集成验证的方法论、检查清单和预防机制。所有前端和后端开发者必须遵守。

---

## 1. 问题根源分析

### 1.1 实测发现的 10 个集成缺陷

| # | 缺陷 | 根因分类 | 严重程度 |
|---|---|---|---|
| 1 | 所有页面 API 请求 404 | 双重 URL 前缀（client baseURL + 页面路径） | P0 |
| 2 | 登录后无侧边栏导航 | MainLayout 存在但未挂载到 App.vue | P0 |
| 3 | 登录页硬编码 localhost:8001 | 环境配置散落在组件代码中 | P0 |
| 4 | Vite proxy 指向错误端口 | 配置文件与实际部署不一致 | P0 |
| 5 | AuthGuard token key 不匹配 | 认证 key 在多处定义，无单一事实源 | P0 |
| 6 | 登录路由指向错误组件 | 路由定义与实际组件路径不一致 | P1 |
| 7 | 知识库显示 0 条 | 前端查询条件与种子数据状态不对齐 | P1 |
| 8 | 配置管理显示空 | 前端 API 路径与后端路由不匹配 | P1 |
| 9 | 采集器管理无数据 | 种子数据未覆盖全部领域 | P1 |
| 10 | 仪表盘快捷按钮无跳转 | UI 组件只有外观没有行为 | P2 |

### 1.2 根因归类

**分类 A：单一事实源缺失（5个）**
- API 路径散落在每个 .vue 文件中，无统一常量定义
- Token key 在 guards.ts / LoginPage / store 三处各写各的
- 端口和 base URL 在 vite.config.ts / LoginPage / 环境变量中重复定义
- 后端路由路径在 api.py 中定义，前端只能猜测

**分类 B：组件孤岛（3个）**
- MainLayout 已实现但未接入路由
- LoginPage.vue 有两个副本（auth/ 和 platform-admin/）
- 页面只有外观模板，交互行为未实现

**分类 C：从未以用户身份验证（全部）**
- 所有组件各自通过了类型检查和 API 测试
- 但没有人打开浏览器实际登录、点击、查看数据
- "集成"只存在于概念中，从未被物理验证

---

## 2. 预防方法论：三道防线

### 第一道防线：设计阶段 — 契约先行

**规则 FBI-01：API 路径常量化**

所有 API 路径必须定义在 `frontend/src/shared/api/routes.ts` 中：

```typescript
// frontend/src/shared/api/routes.ts
// 所有后端 API 路径的唯一来源
export const API = {
  AUTH: {
    LOGIN:    '/api/v1/auth/login',
    LOGOUT:   '/api/v1/auth/logout',
    ME:       '/api/v1/auth/me',
    REFRESH:  '/api/v1/auth/refresh',
  },
  ASSETS:     '/api/v1/assets',
  ASSET_GROUPS: '/api/v1/asset-groups',
  ALERTS:     '/api/v1/alerts',
  ALERT_RULES: '/api/v1/alert-rules',
  EVENTS:     '/api/v1/events',
  TICKETS:    '/api/v1/tickets',
  POLICIES:   '/api/v1/policies',
  SCRIPTS:    '/api/v1/scripts',
  PLAYBOOKS:  '/api/v1/playbooks',
  EXECUTIONS: '/api/v1/executions',
  COLLECTORS: '/api/v1/collectors',
  CONFIGS:    '/api/v1/configs/definitions',
  CREDENTIALS: '/api/v1/credentials',
  KNOWLEDGE:  '/api/v1/knowledge',
  AIOPS: {
    HEALTH:    '/api/v1/aiops/health',
    DIAGNOSE:  '/api/v1/aiops/diagnose',
    ANALYSES:  '/api/v1/aiops/analyses',
  },
} as const
```

任何 .vue 文件禁止硬编码 `/api/v1/xxx` 路径字符串。

**规则 FBI-02：环境配置单一化**

所有环境相关配置（端口、URL、token key）必须集中在：

```
frontend/src/shared/config.ts    ← 运行时配置
frontend/vite.config.ts           ← 构建时代理配置
```

config.ts 示例：

```typescript
export const APP_CONFIG = {
  TOKEN_KEY: 'autops_token',
  API_TIMEOUT: 30000,
  WS_URL: `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`,
} as const
```

任何 .vue 文件禁止：
- 硬编码 `localhost:8001`
- 直接定义 token key 字符串
- 使用 `window.__AUTOPS_API__` 等全局变量

**规则 FBI-03：路由-组件映射验证**

每个路由定义必须包含 `meta.title` 和 `meta.icon`，确保 MainLayout 可以自动渲染：

```typescript
{ path: '/assets', name: 'assets', 
  component: () => import('@/features/asset-config/AssetListPage.vue'),
  meta: { title: '资产管理', icon: 'Grid' } }
```

### 第二道防线：实现阶段 — 组件接入检查

**规则 FBI-04：新组件五步接入清单**

任何新页面组件完成时，必须执行以下 5 步：

```text
[ ] 1. 组件文件存在于正确目录
[ ] 2. router/index.ts 已注册路由（含 meta.title）
[ ] 3. MainLayout.vue 侧边栏已添加菜单项
[ ] 4. API 路径使用 routes.ts 常量（非硬编码）
[ ] 5. 浏览器实际访问页面，确认数据加载成功
```

**规则 FBI-05：认证流程一致性**

认证涉及三个文件，它们必须使用同一个 TOKEN_KEY 常量：

```
frontend/src/shared/config.ts     → TOKEN_KEY 定义
frontend/src/shared/api/client.ts → 读取 TOKEN_KEY 注入 header
frontend/src/app/router/guards.ts → 读取 TOKEN_KEY 判断登录
frontend/src/app/store/auth.ts    → 读取/写入 TOKEN_KEY
```

任何一处不得私自定义 token key 字符串。

**规则 FBI-06：种子数据对齐**

每个领域的种子数据必须确保：

1. 状态值与前端筛选条件一致（如 published vs draft）
2. 外键关联有效（资产ID、凭证ID）
3. 前端页面首次加载能看到非空数据

种子数据脚本：`scripts/data_seed/seed_all.py`

### 第三道防线：验收阶段 — 实际浏览器验证

**规则 FBI-07：首次部署验证协议（First Run Protocol）**

每次以下场景之一发生后，必须执行完整的首次部署验证：

- 新功能合并到 main
- 部署配置变更
- 数据库 migration
- 前端路由变更
- 环境变量变更

验证步骤：

```text
1. 清除浏览器 localStorage
2. 访问前端 URL → 应跳转到登录页
3. 输入 admin/admin123 → 应跳转到仪表盘
4. 确认侧边栏显示所有菜单
5. 逐一点击每个菜单 → 确认页面加载无报错
6. 确认仪表盘显示真实数据（非全零）
7. 确认创建/查看/编辑/删除操作可执行
8. 打开浏览器控制台 → 确认无 JS 错误和 API 404
9. 打开 Network 面板 → 确认所有 API 请求路径正确
10. 确认退出登录后跳转到登录页
```

**规则 FBI-08：页面级验收矩阵**

每个页面必须验证以下矩阵：

| 检查项 | 验证方法 |
|---|---|
| 页面可访问（无白屏/JS报错） | 浏览器直接访问 URL |
| API 请求路径正确 | Network 面板无 404 |
| 数据正常显示 | 表格/列表有数据 |
| 筛选/排序/分页 | 操作后数据正确刷新 |
| 创建操作 | 弹窗提交后列表新增 |
| 查看/编辑操作 | 详情页/抽屉正确展示 |
| 删除操作 | 确认后数据消失 |
| Token 认证 | 过期后跳转登录页 |

---

## 3. 现有问题修复记录

### 修复 #1：API 双重前缀

```diff
- client.ts: baseURL: '/api/v1'
+ client.ts: baseURL: ''
```

所有页面使用 `/api/v1/xxx` 完整路径。

### 修复 #2：MainLayout 未挂载

```diff
  // App.vue
- <router-view />
+ <router-view v-if="isLoginPage" />
+ <MainLayout v-else />
```

### 修复 #3：LoginPage 硬编码 URL

```diff
- const API = (window as any).__AUTOPS_API__ || 'http://localhost:8001'
- const res = await fetch(`${API}/api/v1/auth/login`, ...)
+ const res = await fetch('/api/v1/auth/login', ...)
```

### 修复 #4：Vite proxy 端口

```diff
- target: 'http://localhost:8000'
+ target: 'http://localhost:8001'
```

### 修复 #5：Token Key 统一

```diff
- guards.ts: const TOKEN_KEY = '***'
+ guards.ts: import { APP_CONFIG } from '@/shared/config'; const TOKEN_KEY = APP_CONFIG.TOKEN_KEY
```

### 修复 #6：知识库状态过滤

```diff
- params: { status: 'published' }
+ params: {}  // 显示全部状态
```

### 修复 #7：配置管理 API 路径

```diff
- const API = '/api/v1/configs'
+ const API = '/api/v1/configs/definitions'
```
