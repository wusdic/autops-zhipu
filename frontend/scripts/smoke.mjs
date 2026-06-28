/**
 * 逐页冒烟检查（防止合并/改动引入坏页、白屏）。
 *
 * 做法：启动 vite dev → 注入登录态 + mock 后端 API → 用无头 Chromium 遍历
 * router 里所有 component 路由 → 捕获 pageerror/console.error 与"是否渲染出内容"。
 * 任一页崩溃或空白则以非 0 退出，适合本地与 CI 把关。
 *
 * 用法：
 *   npm run smoke
 * 环境变量：
 *   SMOKE_PORT          dev 端口（默认 5199）
 *   CHROMIUM_PATH       指定 Chromium 可执行文件（CI 用 `npx playwright install chromium` 后可省略；
 *                       本仓部署环境可设 /opt/pw-browsers/chromium-<ver>/chrome-linux/chrome）
 */
import { chromium } from 'playwright'
import { readFileSync } from 'fs'
import { spawn } from 'child_process'
import { setTimeout as sleep } from 'timers/promises'

const PORT = process.env.SMOKE_PORT || '5199'
const BASE = `http://localhost:${PORT}`

// 1. 提取所有带 component 的路由（排除 redirect / 公共页 / 通配；:param 用占位 id）
const src = readFileSync('src/app/router/index.ts', 'utf8')
const routes = []
const re = /path:\s*'([^']+)'[^\n]*component:/g
let m
while ((m = re.exec(src))) {
  let p = m[1]
  if (/login|forbidden|session-expired|not-found|pathMatch/.test(p)) continue
  p = p.replace(/:alertId/g, '1').replace(/:[A-Za-z]+/g, '1')
  routes.push(p)
}

// 2. 启动 dev server
const vite = spawn('npx', ['vite', '--port', PORT, '--strictPort'], { stdio: 'ignore' })
const cleanup = () => { try { vite.kill('SIGTERM') } catch { /* noop */ } }
process.on('exit', cleanup)

async function waitServer(ms = 60000) {
  const t0 = Date.now()
  while (Date.now() - t0 < ms) {
    try { const r = await fetch(BASE + '/'); if (r.ok) return true } catch { /* retry */ }
    await sleep(1000)
  }
  return false
}

let exitCode = 0
try {
  if (!(await waitServer())) { console.error('smoke: vite 启动超时'); process.exit(2) }

  const browser = await chromium.launch(
    process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {}
  )
  const ctx = await browser.newContext()
  // mock 后端 API：统一成功空壳，避免 401 登出，使页面能真正渲染
  await ctx.route('**/api/v1/**', async (route) => {
    const url = route.request().url()
    let data = { items: [], total: 0, page: 1, page_size: 20, total_pages: 0 }
    if (/\/users\/me|\/auth\/me|\/profile/.test(url)) data = { id: '1', username: 'admin', roles: ['admin'], permissions: ['*'] }
    else if (/\/stats|\/overview|\/summary|\/dashboard|diagnostics|platform\/status|health/.test(url)) data = { total: 0, items: [], asset_stats: {}, components: {}, checks: [] }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ code: 0, message: 'ok', data, trace_id: 't' }) })
  })
  const page = await ctx.newPage()
  await page.goto(BASE + '/login')
  await page.evaluate(() => {
    localStorage.setItem('autops_token', 'dev')
    localStorage.setItem('autops_roles', JSON.stringify(['admin']))
    localStorage.setItem('username', 'admin')
  })

  console.log(`smoke: 检查 ${routes.length} 条路由 ...`)
  let bad = 0
  for (const r of routes) {
    const errs = []
    const pe = (e) => errs.push('PAGEERROR: ' + (e.message || String(e)).split('\n')[0])
    const ce = (msg) => { if (msg.type() === 'error') errs.push('CONSOLE: ' + msg.text().split('\n')[0]) }
    page.on('pageerror', pe); page.on('console', ce)
    try { await page.goto(BASE + r, { waitUntil: 'domcontentloaded', timeout: 8000 }) }
    catch (e) { errs.push('NAV: ' + String(e).split('\n')[0]) }
    await page.waitForTimeout(250)
    const ok = await page.evaluate(() => {
      const c = document.querySelector('.autops-page-container,.autops-page-header,.el-tabs,main,.chat-container,.el-table,.el-form')
      return !!c && document.body.innerText.trim().length > 10
    })
    page.off('pageerror', pe); page.off('console', ce)
    // 过滤纯网络/数据噪声，只保留代码级错误
    const code = errs.filter(e => !/Failed to load resource|net::ERR|status of 40|status of 50|ECONNREFUSED|AxiosError|Network Error|timeout of|favicon/i.test(e))
    if (!ok || code.length) {
      bad++
      console.log(`  BAD ${r}` + (!ok ? ' [NO CONTENT]' : '') + (code.length ? ' :: ' + code.slice(0, 2).join(' | ') : ''))
    }
  }
  await browser.close()
  if (bad > 0) { console.error(`smoke: ❌ ${bad}/${routes.length} 页异常`); exitCode = 1 }
  else console.log(`smoke: ✅ ${routes.length}/${routes.length} 页全部正常`)
} catch (e) {
  console.error('smoke: 运行失败', e)
  exitCode = 2
} finally {
  cleanup()
}
process.exit(exitCode)
