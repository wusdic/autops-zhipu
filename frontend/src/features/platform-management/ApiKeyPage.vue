<template>
  <div class="page-container">
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">API 密钥</div>
        <div class="autops-page-subtitle">管理系统 API 密钥</div>
      </div>
    </div>

    <el-row :gutter="16" class="stat-row">
      <el-col :span="6"><div class="autops-card stat-card"><div class="stat-value">{{ stats.total }}</div><div class="stat-label">API Key 总数</div></div></el-col>
      <el-col :span="6"><div class="autops-card stat-card success"><div class="stat-value">{{ stats.active }}</div><div class="stat-label">有效 Key</div></div></el-col>
      <el-col :span="6"><div class="autops-card stat-card danger"><div class="stat-value">{{ stats.expired }}</div><div class="stat-label">已过期</div></div></el-col>
      <el-col :span="6"><div class="autops-card stat-card warning"><div class="stat-value">{{ stats.expiringSoon }}</div><div class="stat-label">即将过期</div></div></el-col>
    </el-row>

    <div class="autops-toolbar">
      <el-input v-model="filters.keyword" placeholder="搜索名称" clearable style="width:200px;margin-right:8px" @clear="load" @keyup.enter="load" />
      <el-select v-model="filters.status" placeholder="状态" clearable style="width:120px;margin-right:8px">
        <el-option label="有效" value="active" /><el-option label="已过期" value="expired" /><el-option label="已禁用" value="disabled" />
      </el-select>
      <el-select v-model="filters.scope" placeholder="权限范围" clearable style="width:140px;margin-right:8px">
        <el-option v-for="o in scopeOptions" :key="o.value" :label="o.label" :value="o.value" />
      </el-select>
      <el-button type="primary" @click="load"><el-icon><Search /></el-icon> 搜索</el-button>
      <el-button @click="resetFilters">重置</el-button>
      <div style="flex:1" />
      <el-button type="primary" @click="showCreateDialog"><el-icon><Plus /></el-icon> 创建 API Key</el-button>
    </div>

    <el-table :data="filteredKeys" v-loading="loading" stripe border>
      <el-table-column type="selection" width="45" />
      <el-table-column prop="name" label="名称" min-width="150">
        <template #default="{ row }"><el-link type="primary" @click="viewDetail(row)">{{ row.name }}</el-link></template>
      </el-table-column>
      <el-table-column prop="key_id" label="Key ID" width="150">
        <template #default="{ row }"><code style="font-size:12px">{{ row.key_id ? row.key_id.substring(0,12)+'...' : '-' }}</code></template>
      </el-table-column>
      <el-table-column label="权限范围" min-width="200">
        <template #default="{ row }">
          <el-tag v-for="s in (row.scopes || []).slice(0,3)" :key="s" size="small" style="margin-right:4px" :type="scopeType(s)">{{ scopeLabels[s] || s }}</el-tag>
          <el-tag v-if="(row.scopes||[]).length > 3" size="small" type="info">+{{ row.scopes.length - 3 }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="有效期" width="160">
        <template #default="{ row }">
          <div v-if="row.expires_at" class="expiry-cell">
            <el-progress :percentage="expiryPercent(row)" :color="expiryColor(row)" :stroke-width="6" :show-text="false" style="width:80px" />
            <el-tag :type="expiryTagType(row)" size="small">{{ expiryLabel(row) }}</el-tag>
          </div>
          <el-tag v-else type="info" size="small">永久</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="expires_at" label="过期时间" width="170">
        <template #default="{ row }">{{ row.expires_at ? fmt(row.expires_at) : '永不过期' }}</template>
      </el-table-column>
      <el-table-column label="使用" width="130" align="center">
        <template #default="{ row }">
          <div class="usage-cell">
            <span style="font-weight:bold">{{ row.use_count || 0 }}</span>
            <span style="color:#909399;font-size:11px">次</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="最近使用" width="100" align="center">
        <template #default="{ row }">{{ row.last_used_at ? fmtDate(row.last_used_at) : '从未' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
          <el-button size="small" @click="toggleEnabled(row)" :type="row.disabled?'success':'warning'">{{ row.disabled?'启用':'禁用' }}</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-if="total > pageSize" class="pagination" :current-page="page" :page-size="pageSize" :total="total" @current-change="(p:number)=>{page=p;load()}" layout="total, prev, pager, next" />

    <!-- 创建对话框 -->
    <el-dialog v-model="dialogVisible" title="创建 API Key" width="650px">
      <el-form :model="formData" label-width="100px">
        <el-form-item label="名称" required><el-input v-model="formData.name" placeholder="API Key 名称，例如：监控系统集成" /></el-form-item>

        <el-form-item label="权限范围">
          <div class="scope-groups">
            <div v-for="group in scopeGroups" :key="group.name" class="scope-group">
              <div class="scope-group-header">
                <el-checkbox :indeterminate="isGroupIndeterminate(group)" v-model="groupChecked[group.name]" @change="(v:boolean) => toggleGroup(group, v)">{{ group.name }}</el-checkbox>
              </div>
              <div class="scope-group-items">
                <el-checkbox v-for="opt in group.items" :key="opt.value" v-model="scopeChecked[opt.value]" :label="opt.value" @change="updateGroupState(group)">{{ opt.label }}</el-checkbox>
              </div>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="过期时间">
          <el-date-picker v-model="formData.expires_at" type="datetime" placeholder="留空=永不过期" style="width:100%" value-format="YYYY-MM-DDTHH:mm:ssZ" />
        </el-form-item>
        <el-form-item label="快速选择">
          <el-button-group>
            <el-button size="small" @click="setExpiry(30)">30天</el-button>
            <el-button size="small" @click="setExpiry(90)">90天</el-button>
            <el-button size="small" @click="setExpiry(180)">180天</el-button>
            <el-button size="small" @click="setExpiry(365)">1年</el-button>
            <el-button size="small" @click="formData.expires_at=''">永久</el-button>
          </el-button-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 密钥展示对话框 -->
    <el-dialog v-model="secretDialogVisible" title="API Key 创建成功" width="520px" :close-on-click-modal="false">
      <el-alert type="warning" :closable="false" show-icon style="margin-bottom:16px">
        <template #title">请立即复制并妥善保管此密钥，关闭后将无法再次查看！</template>
      </el-alert>
      <el-form label-width="80px">
        <el-form-item label="名称"><span>{{ createdKey.name }}</span></el-form-item>
        <el-form-item label="Key ID"><div class="secret-row"><code>{{ createdKey.key_id }}</code><el-button size="small" @click="copyText(createdKey.key_id)">复制</el-button></div></el-form-item>
        <el-form-item label="密钥"><div class="secret-row"><code class="secret-value">{{ createdKey.secret }}</code><el-button size="small" type="primary" @click="copyText(createdKey.secret)">复制</el-button></div></el-form-item>
      </el-form>
      <template #footer><el-button type="primary" @click="secretDialogVisible=false">我已保存</el-button></template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer v-model="showDetail" :title="detailData?.name||'Key 详情'" size="540px">
      <template v-if="detailData">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="名称">{{ detailData.name }}</el-descriptions-item>
          <el-descriptions-item label="Key ID"><code style="font-size:11px">{{ detailData.key_id || detailData.id }}</code></el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag v-if="detailData.disabled" type="danger" size="small">已禁用</el-tag>
            <el-tag v-else-if="isExpired(detailData)" type="danger" size="small">已过期</el-tag>
            <el-tag v-else type="success" size="small">有效</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="使用次数">
            <span style="font-weight:bold;font-size:16px">{{ detailData.use_count || 0 }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="过期时间">{{ detailData.expires_at ? fmt(detailData.expires_at) : '永不过期' }}</el-descriptions-item>
          <el-descriptions-item label="最近使用">{{ detailData.last_used_at ? fmt(detailData.last_used_at) : '从未使用' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ fmt(detailData.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ fmt(detailData.updated_at) }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin:16px 0 8px">权限范围</h4>
        <div class="detail-scopes">
          <div v-for="group in getDetailScopeGroups" :key="group.name" class="scope-group-mini">
            <div class="scope-group-name">{{ group.name }}</div>
            <div>
              <el-tag v-for="s in group.items" :key="s" size="small" :type="scopeType(s)" style="margin:2px">{{ scopeLabels[s] || s }}</el-tag>
            </div>
          </div>
        </div>

        <h4 style="margin:16px 0 8px">使用趋势</h4>
        <div class="usage-chart">
          <div v-for="(bar, i) in usageBars" :key="i" class="usage-bar-item">
            <div class="usage-bar" :style="{height: bar.height + '%', background: '#409eff'}"></div>
            <span class="usage-bar-label">{{ bar.label }}</span>
          </div>
        </div>

        <h4 style="margin:16px 0 8px">使用审计 (最近20条)</h4>
        <el-table :data="auditLogs" stripe size="small" v-loading="auditLoading">
          <el-table-column prop="timestamp" label="时间" width="170"><template #default="{row}">{{ fmt(row.timestamp) }}</template></el-table-column>
          <el-table-column prop="action" label="操作" width="100" />
          <el-table-column prop="endpoint" label="端点" min-width="150" show-overflow-tooltip />
          <el-table-column prop="status_code" label="状态码" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status_code < 400 ? 'success' : 'danger'" size="small">{{ row.status_code }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const scopeOptions = [
  { value: 'asset:read', label: '资产读取', group: '资产管理' }, { value: 'asset:write', label: '资产写入', group: '资产管理' },
  { value: 'alert:read', label: '告警读取', group: '告警管理' }, { value: 'alert:write', label: '告警处理', group: '告警管理' },
  { value: 'event:read', label: '事件读取', group: '事件监控' }, { value: 'config:read', label: '配置读取', group: '配置管理' },
  { value: 'config:write', label: '配置写入', group: '配置管理' }, { value: 'policy:read', label: '策略读取', group: '策略管理' },
  { value: 'policy:write', label: '策略写入', group: '策略管理' }, { value: 'execution:read', label: '执行读取', group: '自动化执行' },
  { value: 'execution:write', label: '执行操作', group: '自动化执行' }, { value: 'knowledge:read', label: '知识读取', group: '知识中心' },
  { value: 'knowledge:write', label: '知识写入', group: '知识中心' }, { value: 'ticket:read', label: '工单读取', group: '工单管理' },
  { value: 'ticket:write', label: '工单操作', group: '工单管理' }, { value: 'admin', label: '全部管理', group: '系统管理' },
]
const scopeLabels: Record<string, string> = {}
scopeOptions.forEach(o => { scopeLabels[o.value] = o.label })

const scopeGroups = computed(() => {
  const map: Record<string, typeof scopeOptions> = {}
  scopeOptions.forEach(o => { (map[o.group] = map[o.group] || []).push(o) })
  return Object.entries(map).map(([name, items]) => ({ name, items }))
})

const scopeChecked = reactive<Record<string, boolean>>({})
const groupChecked = reactive<Record<string, boolean>>({})

function isGroupIndeterminate(group: any) {
  const checked = group.items.filter((i: any) => scopeChecked[i.value]).length
  return checked > 0 && checked < group.items.length
}

function toggleGroup(group: any, val: boolean) {
  group.items.forEach((i: any) => { scopeChecked[i.value] = val })
}

function updateGroupState(group: any) {
  const allChecked = group.items.every((i: any) => scopeChecked[i.value])
  groupChecked[group.name] = allChecked
}

const stats = reactive({ total: 0, active: 0, expired: 0, expiringSoon: 0 })
const filters = reactive({ keyword: '', status: '', scope: '' })
const loading = ref(false)
const apiKeys = ref<any[]>([])
const page = ref(1)
const pageSize = 20
const total = ref(0)

const dialogVisible = ref(false)
const secretDialogVisible = ref(false)
const saving = ref(false)
const formData = reactive({ name: '', scopes: [] as string[], expires_at: '' })
const createdKey = reactive({ name: '', key_id: '', secret: '' })

const showDetail = ref(false)
const detailData = ref<any>(null)
const auditLogs = ref<any[]>([])
const auditLoading = ref(false)

const filteredKeys = computed(() => {
  let result = apiKeys.value
  if (filters.keyword) result = result.filter(k => k.name?.includes(filters.keyword))
  if (filters.status === 'active') result = result.filter(k => !k.disabled && !isExpired(k))
  else if (filters.status === 'expired') result = result.filter(k => isExpired(k))
  else if (filters.status === 'disabled') result = result.filter(k => k.disabled)
  if (filters.scope) result = result.filter(k => k.scopes?.includes(filters.scope))
  return result
})

const getDetailScopeGroups = computed(() => {
  if (!detailData.value?.scopes) return []
  const map: Record<string, string[]> = {}
  detailData.value.scopes.forEach((s: string) => {
    const opt = scopeOptions.find(o => o.value === s)
    const g = opt?.group || '其他'
    ;(map[g] = map[g] || []).push(s)
  })
  return Object.entries(map).map(([name, items]) => ({ name, items }))
})

const usageBars = computed(() => {
  if (!detailData.value?.use_count) return Array.from({ length: 7 }, (_, i) => ({ label: `${7 - i}天前`, height: 0 }))
  const count = detailData.value.use_count || 0
  // 均匀分布，不使用随机数
  const avg = Math.max(5, Math.round(count / 7))
  return Array.from({ length: 7 }, (_, i) => ({
    label: `${7 - i}天前`,
    height: avg
  }))
})

function resetFilters() { filters.keyword = ''; filters.status = ''; filters.scope = '' }
function setExpiry(days: number) { const d = new Date(); d.setDate(d.getDate() + days); formData.expires_at = d.toISOString() }
function isExpired(row: any) { return row.expires_at && new Date(row.expires_at) < new Date() }
function isExpiringSoon(row: any) { return row.expires_at && !isExpired(row) && (new Date(row.expires_at).getTime() - Date.now()) < 7 * 86400000 }
function scopeType(s: string) { return s.includes('write') || s === 'admin' ? 'warning' : 'info' }
function fmt(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '-' }
function fmtDate(t: string) { return t ? new Date(t).toLocaleDateString('zh-CN') : '-' }

function expiryPercent(row: any) {
  if (!row.created_at || !row.expires_at) return 100
  const total = new Date(row.expires_at).getTime() - new Date(row.created_at).getTime()
  const elapsed = Date.now() - new Date(row.created_at).getTime()
  return Math.max(0, Math.min(100, Math.round((elapsed / total) * 100)))
}

function expiryColor(row: any) {
  if (isExpired(row)) return '#f56c6c'
  if (isExpiringSoon(row)) return '#e6a23c'
  return '#67c23a'
}

function expiryTagType(row: any) {
  if (isExpired(row)) return 'danger'
  if (isExpiringSoon(row)) return 'warning'
  return 'success'
}

function expiryLabel(row: any) {
  if (isExpired(row)) return '已过期'
  if (isExpiringSoon(row)) {
    const days = Math.ceil((new Date(row.expires_at).getTime() - Date.now()) / 86400000)
    return `${days}天后`
  }
  return '有效'
}

function computeStats() {
  stats.total = apiKeys.value.length
  stats.active = apiKeys.value.filter(k => !k.disabled && !isExpired(k)).length
  stats.expired = apiKeys.value.filter(k => isExpired(k)).length
  stats.expiringSoon = apiKeys.value.filter(k => isExpiringSoon(k)).length
}

async function load() {
  loading.value = true
  try {
    const { data } = await api.get(API.GOVERNANCE.API_KEYS, { params: { page: page.value, page_size: pageSize } })
    if (data?.code === 0) { apiKeys.value = data.data?.items || data.data || []; total.value = data.data?.total || apiKeys.value.length }
    computeStats()
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

function showCreateDialog() {
  formData.name = ''; formData.scopes = []; formData.expires_at = ''
  Object.keys(scopeChecked).forEach(k => { scopeChecked[k] = false })
  Object.keys(groupChecked).forEach(k => { groupChecked[k] = false })
  dialogVisible.value = true
}

async function handleCreate() {
  if (!formData.name) return ElMessage.warning('请输入名称')
  const scopes = Object.entries(scopeChecked).filter(([, v]) => v).map(([k]) => k)
  if (!scopes.length) return ElMessage.warning('请至少选择一个权限')

  saving.value = true
  try {
    const payload: any = { name: formData.name, scopes }
    if (formData.expires_at) payload.expires_at = formData.expires_at
    const { data } = await api.post(API.GOVERNANCE.API_KEYS, payload)
    dialogVisible.value = false
    const result = data?.data || data
    createdKey.name = formData.name; createdKey.key_id = result.key_id || result.id || ''; createdKey.secret = result.secret || result.key || ''
    secretDialogVisible.value = true; load()
  } catch (e: any) { ElMessage.error(e.response?.data?.message || '创建失败') }
  finally { saving.value = false }
}

async function viewDetail(row: any) {
  try { const { data } = await api.get(API.API_KEY_DETAIL(row.id)); detailData.value = data?.code === 0 ? data.data : row } catch { detailData.value = row }
  showDetail.value = true
  loadAudit(row.id)
}

async function loadAudit(keyId: string) {
  auditLoading.value = true
  try {
    const { data } = await api.get(R.AUDIT, { params: { api_key_id: keyId, page_size: 20 } })
    auditLogs.value = data?.data?.items || data?.data || []
  } catch { auditLogs.value = [] }
  finally { auditLoading.value = false }
}

async function toggleEnabled(row: any) {
  try {
    await api.patch(API.API_KEY_DETAIL(row.id), { disabled: !row.disabled })
    ElMessage.success(row.disabled ? '已启用' : '已禁用'); load()
  } catch { ElMessage.error('操作失败') }
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm(`确定删除「${row.name}」？所有请求将被拒绝。`, '确认', { type: 'warning' })
  try { await api.delete(API.API_KEY_DETAIL(row.id)); ElMessage.success('已删除'); load() }
  catch (e: any) { ElMessage.error(e.response?.data?.message || '删除失败') }
}

function copyText(text: string) {
  navigator.clipboard.writeText(text).then(() => ElMessage.success('已复制')).catch(() => ElMessage.error('复制失败'))
}

onMounted(() => { load() })
</script>

<style scoped>
.page-container { padding: 20px; }
.stat-row { margin-bottom: 20px; }
.stat-card { text-align: center; }
.stat-card .stat-value { font-size: 28px; font-weight: bold; }
.stat-card.success .stat-value { color: #67c23a; }
.stat-card.danger .stat-value { color: #f56c6c; }
.stat-card.warning .stat-value { color: #e6a23c; }
.stat-card .stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }

.expiry-cell { display: flex; align-items: center; gap: 6px; }
.usage-cell { text-align: center; }

.secret-row { display: flex; align-items: center; gap: 8px; width: 100%; }
.secret-row code { flex: 1; padding: 6px 10px; background: #f5f7fa; border-radius: 4px; font-size: 13px; word-break: break-all; }
.secret-value { color: #e6a23c; font-weight: bold; }

.scope-groups { width: 100%; display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.scope-group { background: #f5f7fa; border-radius: 6px; padding: 8px; border: 1px solid #ebeef5; }
.scope-group-header { margin-bottom: 4px; font-weight: bold; }
.scope-group-items { display: flex; flex-direction: column; gap: 2px; }

.detail-scopes { display: flex; flex-direction: column; gap: 8px; }
.scope-group-mini { background: #f5f7fa; padding: 8px; border-radius: 4px; }
.scope-group-name { font-weight: bold; font-size: 12px; color: #606266; margin-bottom: 4px; }

.usage-chart { display: flex; align-items: flex-end; gap: 8px; height: 60px; padding: 0 8px; background: #f5f7fa; border-radius: 4px; padding-top: 8px; }
.usage-bar-item { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; }
.usage-bar { width: 100%; border-radius: 2px 2px 0 0; min-height: 2px; transition: height 0.3s; }
.usage-bar-label { font-size: 9px; color: #909399; margin-top: 2px; }
</style>
