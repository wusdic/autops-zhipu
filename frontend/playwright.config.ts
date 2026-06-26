import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright E2E 配置（冒烟）.
 *
 * 针对“侧边栏页面/登录跳转/401-500”这类运行时回归。需要一套已运行的栈：
 *   - 前端：E2E_BASE_URL（默认 http://127.0.0.1:5174）
 *   - 后端：经前端反代或同源；登录账号由 E2E_USERNAME/E2E_PASSWORD 提供
 *
 * 环境已预装 Chromium（PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers），无需 install。
 */
export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://127.0.0.1:5174',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
})
