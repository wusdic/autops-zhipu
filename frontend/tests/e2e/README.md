# 端到端测试（E2E）

两类用例：
- `smoke.spec.ts`：UI 运行时冒烟（登录跳转、关键页可开、无 401/5xx）。
- `business-flow.spec.ts`：**业务闭环 API 级 E2E**，验证"功能有效"而非仅页面渲染。

## 业务闭环覆盖
登录 → 资源(建资产) → 业务系统(挂成员/聚合/按业务过滤) → 资源发现(建任务→等 Worker 跑到终态)
→ 监控采集触发 → 告警/异常可查 → 自动化(脚本/剧本/执行可查) → 工单(建/查) → 知识可查
→ 报表统计 + 平台诊断。用例结束自动清理创建的资产/业务系统/工单。

## 前置
一套**已运行**的栈：后端 + MySQL + Redis + **Worker(autops-worker)**（发现任务终态依赖 Worker 消费 outbox）。

## 运行
```bash
cd frontend
npm install                      # 含 @playwright/test
# 业务闭环（API 级，连后端）
E2E_API_URL=http://<服务器IP>:8001 \
E2E_USERNAME=admin E2E_PASSWORD=<密码> \
  npx playwright test business-flow

# UI 冒烟（连前端）
E2E_BASE_URL=http://<服务器IP> \
E2E_USERNAME=admin E2E_PASSWORD=<密码> \
  npx playwright test smoke

# 全部
npm run test:e2e
```

## 环境变量
| 变量 | 默认 | 说明 |
|---|---|---|
| `E2E_API_URL` | `http://127.0.0.1:8001` | 业务闭环用例的后端地址 |
| `E2E_BASE_URL` | `http://127.0.0.1:5174` | UI 冒烟的前端地址 |
| `E2E_USERNAME` / `E2E_PASSWORD` | `admin` / `admin123456` | 登录账号 |

浏览器：环境预装 Chromium（`PLAYWRIGHT_BROWSERS_PATH`）。纯 API 用例不需要浏览器；
UI 冒烟需要 Chromium，缺失时执行 `npx playwright install chromium`。

> 注：`business-flow` 是 API 级（用 Playwright 的 request 上下文），无需真实浏览器，
> 适合放进 CI 在每次合并时跑，确保业务闭环功能可用。
