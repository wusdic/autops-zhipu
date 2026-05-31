<template>
  <div class="page-container">
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6"><el-card shadow="hover" class="stat-card"><div class="stat-value">{{ stats.total }}</div><div class="stat-label">API Key 总数</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover" class="stat-card success"><div class="stat-value">{{ stats.active }}</div><div class="stat-label">有效 Key</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover" class="stat-card danger"><div class="stat-value">{{ stats.expired }}</div><div class="stat-label">已过期</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover" class="stat-card warning"><div class="stat-value">{{ stats.expiringSoon }}</div><div class="stat-label">即将过期</div></el-card></el-col>
    </el-row>

    <div class="toolbar">
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
      <el-table-column prop="name" label="名称" min-width="160">
        <template #default="{ row }"><el-link type="primary" @click="viewDetail(row)">{{ row.name }}</el-link></template>
      </el-table-column>
      <el-table-column prop="key_id" label="Key ID" width="160">
        <template #default="{ row }"><code style="font-size:12px">{{ row.key_id ? row.key_id.substring(0,12)+'...' : '-' }}</code></template>
      </el-table-column>
      <el-table-column label="权限范围" min-width="200">
        <template #default="{ row }">
          <el-tag v-for="s in (row.scopes || []).slice(0,3)" :key="s" size="small" style="margin-right:4px" :type="scopeType(s)">{{ scopeLabels[s] || s }}</el-tag>
          <el-tag v-if="(row.scopes||[]).length > 3" size="small" type="info">+{{ row.scopes.length - 3 }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="有效期" width="120">
        <template #default="{ row }">
          <el-tag v-if="isExpired(row)" type="danger" size="small">已过期</el-tag>
          <el-tag v-else-if="isExpiringSoon(row)" type="warning" size="small">即将过期</el-tag>
          <el-tag v-else-if="row.expires_at" type="success" size="small">有效</el-tag>
          <el-tag v-else type="info" size="small">永久</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="expires_at" label="过期时间" width="170">
        <template #default="{ row }">{{ row.expires_at ? fmt(row.expires_at) : '永不过期' }}</template>
      </el-table-column>
      <el-table-column label="最近使用" width="100" align="center">
        <template #default="{ row }">{{ row.last_used_at ? fmtDate(row.last_used_at) : '从未' }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">{{ fmt(row.created_at) }}</template>
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
    <el-dialog v-model="dialogVisible" title="创建 API Key" width="560px">
      <el-form :model="formData" label-width="100px">
        <el-form-item label="名称" required><el-input v-model="formData.name" placeholder="API Key 名称" /></el-form-item>
        <el-form-item label="权限范围">
          <el-checkbox-group v-model="formData.scopes">
            <el-row :gutter="8">
              <el-col :span="12" v-for="opt in scopeOptions" :key="opt.value">
                <el-checkbox :label="opt.value">{{ opt.label }}</el-checkbox>
              </el-col>
            </el-row>
          </el-checkbox-group>
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
    <el-drawer v-model="showDetail" :title="detailData?.name||'Key 详情'" size="500px">
      <template v-if="detailData">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="名称">{{ detailData.name }}</el-descriptions-item>
          <el-descriptions-item label="Key ID"><code>{{ detailData.key_id || detailData.id }}</code></el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag v-if="detailData.disabled" type="danger" size="small">已禁用</el-tag>
            <el-tag v-else-if="isExpired(detailData)" type="danger" size="small">已过期</el-tag>
            <el-tag v-else type="success" size="small">有效</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="过期时间">{{ detailData.expires_at ? fmt(detailData.expires_at) : '永不过期' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ fmt(detailData.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="最近使用">{{ detailData.last_used_at ? fmt(detailData.last_used_at) : '从未使用' }}</el-descriptions-item>
          <el-descriptions-item label="使用次数">{{ detailData.use_count || 0 }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin:16px 0 8px">权限范围</h4>
        <el-tag v-for="s in (detailData.scopes||[])" :key="s" style="margin-right:4px;margin-bottom:4px" :type="scopeType(s)">{{ scopeLabels[s]||s }}</el-tag>

        <h4 style="margin:16px 0 8px">使用审计</h4>
        <el-table :data="auditLogs" stripe size="small" v-loading="auditLoading">
          <el-table-column prop="timestamp" label="时间" width="170"><template #default="{row}">{{ fmt(row.timestamp) }}</template></el-table-column>
          <el-table-column prop="action" label="操作" width="100" />
          <el-table-column prop="endpoint" label="端点" min-width="150" show-overflow-tooltip />
          <el-table-column prop="status_code" label="状态码" width="80" />
        </el-table>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const scopeOptions = [
  { value: 'asset:read', label: '资产读取' }, { value: 'asset:write', label: '资产写入' },
  { value: 'alert:read', label: '告警读取' }, { value: 'alert:write', label: '告警处理' },
  { value: 'event:read', label: '事件读取' }, { value: 'config:read', label: '配置读取' },
  { value: 'config:write', label: '配置写入' }, { value: 'policy:read', label: '策略读取' },
  { value: 'policy:write', label: '策略写入' }, { value: 'execution:read', label: '执行读取' },
  { value: 'execution:write', label: '执行操作' }, { value: 'knowledge:read', label: '知识读取' },
  { value: 'knowledge:write', label: '知识写入' }, { value: 'ticket:read', label: '工单读取' },
  { value: 'ticket:write', label: '工单操作' }, { value: 'admin', label: '全部管理' },
]
const scopeLabels: Record<string, string> = {}
scopeOptions.forEach(o => { scopeLabels[o.value] = o.label })

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

function resetFilters() { filters.keyword=''; filters.status=''; filters.scope='' }

function setExpiry(days: number) {
  const d = new Date(); d.setDate(d.getDate() + days)
  formData.expires_at = d.toISOString()
}

function isExpired(row: any) { return row.expires_at && new Date(row.expires_at) < new Date() }
function isExpiringSoon(row: any) { return row.expires_at && !isExpired(row) && (new Date(row.expires_at).getTime() - Date.now()) < 7*86400000 }
function scopeType(s: string) { return s.includes('write') || s === 'admin' ? 'warning' : 'info' }
function fmt(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '-' }
function fmtDate(t: string) { return t ? new Date(t).toLocaleDateString('zh-CN') : '-' }

function computeStats() {
  stats.total = apiKeys.value.length
  stats.active = apiKeys.value.filter(k => !k.disabled && !isExpired(k)).length
  stats.expired = apiKeys.value.filter(k => isExpired(k)).length
  stats.expiringSoon = apiKeys.value.filter(k => isExpiringSoon(k)).length
}

async function load() {
  loading.value = true
  try {
    const { data } = await api.get(API.API_KEYS, { params: { page: page.value, page_size: pageSize } })
    if (data?.code === 0) { apiKeys.value = data.data?.items || data.data || []; total.value = data.data?.total || apiKeys.value.length }
    computeStats()
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

function showCreateDialog() { formData.name=''; formData.scopes=[]; formData.expires_at=''; dialogVisible.value=true }

async function handleCreate() {
  if (!formData.name) return ElMessage.warning('请输入名称')
  saving.value = true
  try {
    const payload: any = { name: formData.name, scopes: formData.scopes }
    if (formData.expires_at) payload.expires_at = formData.expires_at
    const { data } = await api.post(API.API_KEYS, payload)
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
    const { data } = await api.get('/api/v1/audit-logs', { params: { api_key_id: keyId, page_size: 20 } })
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
.secret-row { display: flex; align-items: center; gap: 8px; width: 100%; }
.secret-row code { flex: 1; padding: 6px 10px; background: #f5f7fa; border-radius: 4px; font-size: 13px; word-break: break-all; }
.secret-value { color: #e6a23c; font-weight: bold; }
</style>
