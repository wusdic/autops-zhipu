# AUTOPS 前端架构设计

> 文档状态：current
> 建议路径：`docs/01-architecture/FRONTEND_ARCHITECTURE.md`

---

## 1. 技术栈

| 组件 | 选择 | 版本 |
|---|---|---|
| 框架 | Vue 3 | 3.4+ |
| 语言 | TypeScript | 5.0+ |
| 构建工具 | Vite | 5.0+ |
| 状态管理 | Pinia | 2.1+ |
| UI 组件库 | Element Plus | 2.4+ |
| 图表 | ECharts | 5.4+ |
| 路由 | Vue Router | 4.2+ |
| HTTP Client | Axios | 1.6+ |
| WebSocket | 原生 WebSocket | - |
| E2E 测试 | Playwright | 1.40+ |

---

## 2. 分层结构

```text
Pages (views)
  ↓ 使用
Composables (hooks)
  ↓ 调用
API Client (shared/api)
  ↓ 请求
Backend API
```

---

## 3. 状态管理

### 3.1 全局 Store

| Store | 说明 |
|---|---|
| useAuthStore | 认证状态、Token、用户信息 |
| usePermissionStore | 权限列表、角色 |
| useAppStore | 应用状态、侧边栏、主题 |
| useNotificationStore | 实时通知 |
| useWebSocketStore | WebSocket 连接管理 |

### 3.2 页面级 Store

每个 feature 可有自己的 Store，按需加载。

---

## 4. API Client

```typescript
// shared/api/client.ts
const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// 请求拦截：注入 Token
// 响应拦截：统一错误处理、trace_id 提取
// 响应拦截：Token 过期自动刷新
```

---

## 5. 权限守卫

```typescript
// app/router/guards.ts
router.beforeEach(async (to, from) => {
  // 检查认证
  // 检查权限
  // 动态路由
})
```

---

## 6. 主题配置

- 基于 Element Plus 主题变量
- 支持亮色/暗色模式
- 品牌色可配置

---

## 7. 构建优化

- 路由懒加载
- 组件按需导入
- Vite 分包策略
- Gzip 压缩
- 静态资源 CDN（可选）
