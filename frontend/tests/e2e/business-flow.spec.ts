import { test, expect, request, type APIRequestContext } from '@playwright/test'

/**
 * 业务闭环 E2E（API 级，验证"功能有效"而非仅页面渲染）。
 *
 * 覆盖闭环：登录 → 资源(建资产) → 业务系统(挂成员/聚合) → 资源发现(建任务→等完成)
 * → 监控采集触发 → 告警/异常可查 → 自动化(脚本/剧本/执行可查) → 工单(建/查)
 * → 知识可查 → 报表统计/平台诊断。最后清理创建的数据。
 *
 * 前置：一套已运行的后端 + DB + Worker。
 *   E2E_API_URL   后端地址（默认 http://127.0.0.1:8001）
 *   E2E_USERNAME / E2E_PASSWORD  登录账号（默认 admin / admin123456）
 * 运行：cd frontend && E2E_API_URL=http://<服务器IP>:8001 npx playwright test business-flow
 */

const API = process.env.E2E_API_URL || 'http://127.0.0.1:8001'
const USERNAME = process.env.E2E_USERNAME || 'admin'
const PASSWORD = process.env.E2E_PASSWORD || 'admin123456'
const SFX = Date.now().toString().slice(-6) // 唯一后缀，避免重名

let api: APIRequestContext
let token = ''
const created = { assetId: '', bizId: '', taskId: '', ticketId: '' }

/** 统一断言响应信封 {code,data}；返回 data */
async function ok(resp: import('@playwright/test').APIResponse, label: string) {
  expect(resp.status(), `${label} HTTP`).toBeLessThan(400)
  const body = await resp.json()
  expect(body.code, `${label} code=${body.code} msg=${body.message}`).toBe(0)
  return body.data
}

test.describe.configure({ mode: 'serial' })

test.beforeAll(async () => {
  api = await request.newContext({ baseURL: API, timeout: 20_000 })
  const resp = await api.post('/api/v1/auth/login', { data: { username: USERNAME, password: PASSWORD } })
  const data = await ok(resp, '登录')
  token = data.access_token
  expect(token, '应返回 access_token').toBeTruthy()
})

test.afterAll(async () => {
  const h = { Authorization: `Bearer ${token}` }
  if (created.ticketId) await api.delete(`/api/v1/tickets/${created.ticketId}`, { headers: h }).catch(() => {})
  if (created.assetId) await api.delete(`/api/v1/assets/${created.assetId}`, { headers: h }).catch(() => {})
  if (created.bizId) await api.delete(`/api/v1/business-systems/${created.bizId}`, { headers: h }).catch(() => {})
  await api.dispose()
})

function auth() { return { Authorization: `Bearer ${token}` } }

test('资源中心：创建资产并可检索', async () => {
  const create = await api.post('/api/v1/assets', {
    headers: auth(),
    data: { name: `e2e-asset-${SFX}`, asset_type: 'linux_server', ip: `10.255.${(Number(SFX) % 250) + 1}.9` },
  })
  const asset = await ok(create, '建资产')
  created.assetId = asset.id
  expect(asset.id).toBeTruthy()

  const get = await api.get(`/api/v1/assets/${created.assetId}`, { headers: auth() })
  const got = await ok(get, '查资产')
  expect(got.name).toBe(`e2e-asset-${SFX}`)
})

test('业务系统：创建 + 挂载成员 + 聚合/过滤生效', async () => {
  const create = await api.post('/api/v1/business-systems', {
    headers: auth(), data: { name: `e2e-biz-${SFX}`, importance: 'high' },
  })
  const biz = await ok(create, '建业务系统')
  created.bizId = biz.id

  // 挂成员
  const add = await api.post(`/api/v1/business-systems/${created.bizId}/members`, {
    headers: auth(), data: { asset_ids: [created.assetId] },
  })
  await ok(add, '挂成员')

  // 成员列表应含该资产
  const members = await ok(await api.get(`/api/v1/business-systems/${created.bizId}/members`, { headers: auth() }), '成员列表')
  const memberIds = (members.items || []).map((a: any) => a.id)
  expect(memberIds, '成员应包含刚挂的资产').toContain(created.assetId)

  // 资产详情应已写入 business_system_id（关系事实源）
  const got = await ok(await api.get(`/api/v1/assets/${created.assetId}`, { headers: auth() }), '查资产归属')
  expect(got.business_system_id).toBe(created.bizId)

  // 按业务过滤资产列表应能查到
  const filtered = await ok(await api.get(`/api/v1/assets?business_system_id=${created.bizId}`, { headers: auth() }), '按业务过滤')
  expect((filtered.items || []).map((a: any) => a.id)).toContain(created.assetId)
})

test('资源发现：建任务并由 Worker 跑到终态（验证事件闭环）', async () => {
  const create = await api.post('/api/v1/discovery/tasks', {
    headers: auth(),
    data: { name: `e2e-scan-${SFX}`, ip_mode: 'cidr', cidr: '127.0.0.1/32', protocols: ['icmp'], auto_onboard: false, timeout: 15 },
  })
  const task = await ok(create, '建发现任务')
  created.taskId = task.id || task.task_id
  expect(created.taskId).toBeTruthy()

  // 轮询任务状态最多 ~60s，断言最终不再停留在 pending/running（验证 Worker 消费 outbox 闭环）
  let status = task.status
  for (let i = 0; i < 30 && (status === 'pending' || status === 'running'); i++) {
    await new Promise((r) => setTimeout(r, 2000))
    const d = await ok(await api.get(`/api/v1/discovery/tasks/${created.taskId}`, { headers: auth() }), '查发现任务')
    status = d.status
  }
  expect(['completed', 'failed', 'success'], `任务终态=${status}（若一直 running 多为 Worker 未运行）`).toContain(status)
})

test('监控采集：手动触发一次采集周期', async () => {
  const resp = await api.post('/api/v1/collection-jobs/trigger', { headers: auth(), data: {} })
  await ok(resp, '触发采集')
})

test('告警/异常：列表接口可用且为分页结构', async () => {
  for (const [path, label] of [['/api/v1/alerts', '告警列表'], ['/api/v1/anomalies', '异常列表']] as const) {
    const data = await ok(await api.get(path, { headers: auth() }), label)
    expect(Array.isArray(data.items), `${label} 应为分页 items`).toBeTruthy()
  }
})

test('自动化：脚本/剧本/执行历史可查', async () => {
  for (const [path, label] of [['/api/v1/scripts', '脚本库'], ['/api/v1/playbooks', '剧本库'], ['/api/v1/executions', '执行历史']] as const) {
    const data = await ok(await api.get(path, { headers: auth() }), label)
    expect(Array.isArray(data.items)).toBeTruthy()
  }
})

test('工单协同：创建工单并可检索', async () => {
  const create = await api.post('/api/v1/tickets', {
    headers: auth(),
    data: { title: `e2e-ticket-${SFX}`, ticket_type: 'incident', priority: 'medium', description: 'E2E 业务闭环验证工单' },
  })
  const ticket = await ok(create, '建工单')
  created.ticketId = ticket.id
  const got = await ok(await api.get(`/api/v1/tickets/${created.ticketId}`, { headers: auth() }), '查工单')
  expect(got.title).toBe(`e2e-ticket-${SFX}`)
})

test('知识库：列表可查', async () => {
  const data = await ok(await api.get('/api/v1/knowledge', { headers: auth() }), '知识列表')
  expect(Array.isArray(data.items)).toBeTruthy()
})

test('报表/平台：dashboard 统计 + 平台诊断可用', async () => {
  const stats = await ok(await api.get('/api/v1/dashboard/stats', { headers: auth() }), 'dashboard 统计')
  expect(stats).toHaveProperty('asset_stats')
  const diag = await ok(await api.get('/api/v1/platform/diagnostics', { headers: auth() }), '平台诊断')
  expect(Array.isArray(diag.checks)).toBeTruthy()
})
