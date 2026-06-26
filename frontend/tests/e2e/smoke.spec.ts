import { expect, test } from '@playwright/test'

/**
 * 运行时冒烟：覆盖真机测试报告暴露过的回归点
 * 1) 未登录访问 / 应跳登录页，且不产生 500
 * 2) 登录后 /auth/me 不 500、token 持久化
 * 3) 关键菜单页可打开、main 有内容、无 401/500
 *
 * 运行前置：前端(默认 5174)+后端+DB 已启动。
 * 账号经 E2E_USERNAME/E2E_PASSWORD（默认 admin / 见种子日志）。
 */

const USERNAME = process.env.E2E_USERNAME || 'admin'
const PASSWORD = process.env.E2E_PASSWORD || 'admin123456'

const KEY_PAGES = [
  '/assets',
  '/tickets',
  '/alerts',
  '/inspection/tasks',
  '/platform/license',
]

/** 监听并收集 API 5xx / 401 */
function trackBadResponses(page: import('@playwright/test').Page) {
  const bad: string[] = []
  page.on('response', (resp) => {
    const s = resp.status()
    const u = resp.url()
    if (u.includes('/api/') && (s >= 500 || s === 401)) {
      bad.push(`${s} ${u}`)
    }
  })
  return bad
}

async function login(page: import('@playwright/test').Page) {
  await page.goto('/login')
  await page.getByPlaceholder(/用户名|账号|username/i).first().fill(USERNAME)
  await page.getByPlaceholder(/密码|password/i).first().fill(PASSWORD)
  await page.getByRole('button', { name: /登录|登 录|login/i }).first().click()
  await page.waitForURL((u) => !u.pathname.startsWith('/login'), { timeout: 15_000 })
}

test('未登录访问 / 跳登录页且无 5xx', async ({ page }) => {
  const bad = trackBadResponses(page)
  await page.goto('/')
  await page.waitForLoadState('networkidle')
  expect(page.url()).toContain('/login')
  expect(bad.filter((b) => b.startsWith('5'))).toEqual([])
})

test('登录后 /auth/me 正常且 token 持久化', async ({ page }) => {
  const bad = trackBadResponses(page)
  await login(page)
  const token = await page.evaluate(() => localStorage.getItem('autops_token'))
  expect(token).toBeTruthy()
  expect(bad.filter((b) => b.startsWith('5'))).toEqual([])
})

test('关键菜单页可打开且无 401/500', async ({ page }) => {
  await login(page)
  for (const path of KEY_PAGES) {
    const bad = trackBadResponses(page)
    await page.goto(path)
    await page.waitForLoadState('networkidle')
    const mainLen = await page.evaluate(() => document.querySelector('main')?.textContent?.length || 0)
    expect(mainLen, `${path} main 应有内容`).toBeGreaterThan(0)
    expect(bad, `${path} 不应有 401/500: ${bad.join(', ')}`).toEqual([])
  }
})
