<template>
  <div class="alert-list-page">
    <!-- ========== Page Header ========== -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">告警中心</div>
        <div class="autops-page-subtitle">实时监控告警事件，支持确认、恢复、转工单等操作</div>
      </div>
    </div>

    <!-- ========== Statistics Row ========== -->
    <el-row :gutter="16" class="stats-row mb-lg">
      <el-col :span="6">
        <div class="autops-card stat-card stat-card--critical">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="32"><WarningFilled /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.critical }}</div>
              <div class="stat-card__label">严重告警</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card stat-card--warning">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="32"><Warning /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.warning }}</div>
              <div class="stat-card__label">警告告警</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card stat-card--active">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="32"><Bell /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.active }}</div>
              <div class="stat-card__label">活跃告警</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card stat-card--resolved">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="32"><CircleCheckFilled /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.resolvedToday }}</div>
              <div class="stat-card__label">今日已恢复</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- ========== Main Card ========== -->
    <div class="autops-card main-card">
      <div class="autops-card-header">
        <span class="autops-card-title">告警列表</span>
        <el-button :icon="Refresh" circle size="small" @click="loadAlerts" />
      </div>
      <div class="autops-card-body">
        <!-- ========== Filters ========== -->
        <el-form :inline="true" class="autops-toolbar filter-form" @submit.prevent="handleSearch">
        <el-form-item label="告警级别">
          <el-select v-model="filters.severity" placeholder="全部级别" clearable style="width: 130px">
            <el-option label="严重" value="critical" />
            <el-option label="警告" value="warning" />
            <el-option label="信息" value="info" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 130px">
            <el-option label="告警中" value="firing" />
            <el-option label="已确认" value="acknowledged" />
            <el-option label="已恢复" value="resolved" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="filters.dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DDTHH:mm:ssZ"
            style="width: 360px"
          />
        </el-form-item>
        <el-form-item label="关联资产">
          <el-input
            v-model="filters.asset"
            placeholder="搜索资产名称"
            clearable
            :prefix-icon="Search"
            style="width: 180px"
          />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索告警标题"
            clearable
            :prefix-icon="Search"
            style="width: 180px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="RefreshLeft" @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- ========== Batch Operations Bar ========== -->
      <transition name="el-fade-in">
        <div v-if="selectedIds.length > 0" class="batch-bar">
          <span class="batch-bar__info">
            已选择 <strong>{{ selectedIds.length }}</strong> 条告警
          </span>
          <el-button type="warning" size="small" :icon="Check" @click="batchAcknowledge">
            批量确认
          </el-button>
          <el-button type="info" size="small" :icon="TurnOff" @click="batchSuppress">
            批量抑制
          </el-button>
          <el-button type="success" size="small" :icon="CircleCheck" @click="batchResolve">
            批量恢复
          </el-button>
          <el-button size="small" @click="clearSelection">取消选择</el-button>
        </div>
      </transition>

      <!-- ========== Alert Table ========== -->
      <el-table
        ref="tableRef"
        :data="alerts"
        v-loading="loading"
        stripe
        border
        row-key="id"
        @selection-change="handleSelectionChange"
        class="alert-table"
      >
        <el-table-column type="selection" width="45" fixed="left" />
        <el-table-column prop="severity" label="级别" width="90" align="center">
          <template #default="{ row }">
            <SeverityBadge :severity="row.severity" size="small" />
          </template>
        </el-table-column>
        <el-table-column prop="title" label="告警标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="asset_name" label="关联资产" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.asset_name || row.asset?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <StatusBadge :status="row.status" size="small" show-icon />
          </template>
        </el-table-column>
        <el-table-column prop="triggered_at" label="触发时间" width="175">
          <template #default="{ row }">
            {{ formatTime(row.triggered_at || row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="acknowledged_at" label="确认时间" width="175">
          <template #default="{ row }">
            {{ row.acknowledged_at ? formatTime(row.acknowledged_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="持续时间" width="120" align="center">
          <template #default="{ row }">
            <span v-if="row.status === 'resolved'">{{ computeDuration(row.triggered_at || row.created_at, row.resolved_at) }}</span>
            <span v-else>{{ computeDuration(row.triggered_at || row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'firing'"
              size="small"
              type="warning"
              link
              @click="ackAlert(row.id)"
            >确认</el-button>
            <el-button
              v-if="row.status !== 'resolved'"
              size="small"
              type="success"
              link
              @click="resolveAlert(row.id)"
            >恢复</el-button>
            <el-button
              size="small"
              type="primary"
              link
              @click="createTicket(row)"
            >转工单</el-button>
            <el-button
              size="small"
              link
              @click="viewDetail(row)"
            >详情</el-button>
          </template>
        </el-table-column>
      </el-table>

        <!-- ========== Pagination ========== -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            background
            @change="loadAlerts"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  RefreshLeft,
  Check,
  TurnOff,
  CircleCheck,
  WarningFilled,
  Warning,
  Bell,
  CircleCheckFilled,
} from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import SeverityBadge from '@/shared/components/SeverityBadge.vue'

const router = useRouter()

// ── State ──────────────────────────────────────────────────────────
const loading = ref(false)
const alerts = ref<any[]>([])
const selectedRows = ref<any[]>([])
const selectedIds = ref<string[]>([])
const tableRef = ref()

const stats = reactive({
  critical: 0,
  warning: 0,
  active: 0,
  resolvedToday: 0,
})

const filters = reactive({
  severity: '',
  status: '',
  dateRange: null as [string, string] | null,
  asset: '',
  keyword: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

// ── Helpers ─────────────────────────────────────────────────────────
function formatTime(val: string | null | undefined): string {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function computeDuration(start: string | null | undefined, end?: string | null): string {
  if (!start) return '-'
  const s = new Date(start).getTime()
  if (isNaN(s)) return '-'
  const e = end ? new Date(end).getTime() : Date.now()
  if (isNaN(e)) return '-'
  const diff = Math.max(0, Math.floor((e - s) / 1000))
  if (diff < 60) return `${diff}秒`
  if (diff < 3600) return `${Math.floor(diff / 60)}分${diff % 60}秒`
  if (diff < 86400) return `${Math.floor(diff / 3600)}时${Math.floor((diff % 3600) / 60)}分`
  return `${Math.floor(diff / 86400)}天${Math.floor((diff % 86400) / 3600)}时`
}

// ── Statistics ──────────────────────────────────────────────────────
async function loadStats() {
  try {
    const { data } = await api.get(R.ALERT_STATS)
    if (data.code === 0 && data.data) {
      const d = data.data
      // Backend returns: { total, firing, acknowledged, resolved }
      // Map to display fields
      stats.critical = d.critical_count ?? d.critical ?? d.firing ?? 0
      stats.warning = d.warning_count ?? d.warning ?? d.acknowledged ?? 0
      stats.active = d.active_count ?? d.active ?? (d.firing ?? 0) + (d.acknowledged ?? 0)
      stats.resolvedToday = d.resolved_today ?? d.resolvedToday ?? d.resolved ?? 0
    }
  } catch {
    // stats are non-critical; silently ignore
  }
}

// ── Alert List ──────────────────────────────────────────────────────
async function loadAlerts() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.severity) params.severity = filters.severity
    if (filters.status) params.status = filters.status
    if (filters.asset) params.asset = filters.asset
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_time = filters.dateRange[0]
      params.end_time = filters.dateRange[1]
    }
    const { data } = await api.get(R.ALERTS, { params })
    if (data.code === 0) {
      alerts.value = data.data.items || data.data.list || []
      pagination.total = data.data.total || 0
    }
  } catch {
    ElMessage.error('加载告警列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  loadAlerts()
}

function resetFilters() {
  filters.severity = ''
  filters.status = ''
  filters.dateRange = null
  filters.asset = ''
  filters.keyword = ''
  pagination.page = 1
  loadAlerts()
}

// ── Selection ───────────────────────────────────────────────────────
function handleSelectionChange(rows: any[]) {
  selectedRows.value = rows
  selectedIds.value = rows.map((r) => r.id)
}

function clearSelection() {
  tableRef.value?.clearSelection()
}

// ── Single Operations ───────────────────────────────────────────────
async function ackAlert(id: string) {
  try {
    const { data } = await api.post(R.ALERT_ACKNOWLEDGE(id))
    if (data.code === 0) {
      ElMessage.success('告警已确认')
      loadAlerts()
      loadStats()
    }
  } catch {
    ElMessage.error('操作失败')
  }
}

async function resolveAlert(id: string) {
  try {
    const { data } = await api.post(R.ALERT_RESOLVE(id))
    if (data.code === 0) {
      ElMessage.success('告警已恢复')
      loadAlerts()
      loadStats()
    }
  } catch {
    ElMessage.error('操作失败')
  }
}

async function createTicket(alert: any) {
  try {
    const { value: description } = await ElMessageBox.prompt('工单描述（可选）', '转工单', {
      confirmButtonText: '创建',
      cancelButtonText: '取消',
      inputPlaceholder: '请输入工单描述',
    })
    const { data } = await api.post(R.TICKETS, {
      title: `[告警] ${alert.title}`,
      ticket_type: 'incident',
      priority: alert.severity === 'critical' ? 'high' : 'medium',
      description: description || alert.title,
      alert_ids: JSON.stringify([alert.id]),
    })
    if (data.code === 0) {
      ElMessage.success('工单已创建')
    }
  } catch {
    // user cancelled
  }
}

function viewDetail(row: any) {
  router.push({ name: 'AlertDetail', params: { id: row.id } })
}

// ── Batch Operations ────────────────────────────────────────────────
async function batchAcknowledge() {
  const ids = selectedIds.value
  if (!ids.length) return
  try {
    await ElMessageBox.confirm(`确认批量确认 ${ids.length} 条告警？`, '批量确认', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
    })
    const promises = ids.map((id) => api.post(R.ALERT_ACKNOWLEDGE(id)))
    const results = await Promise.allSettled(promises)
    const failed = results.filter((r) => r.status === 'rejected').length
    if (failed === 0) {
      ElMessage.success(`${ids.length} 条告警已全部确认`)
    } else {
      ElMessage.warning(`${ids.length - failed} 条成功，${failed} 条失败`)
    }
    clearSelection()
    loadAlerts()
    loadStats()
  } catch {
    // cancelled
  }
}

async function batchSuppress() {
  const ids = selectedIds.value
  if (!ids.length) return
  try {
    await ElMessageBox.confirm(`确认批量抑制 ${ids.length} 条告警？抑制后告警将不再通知。`, '批量抑制', {
      confirmButtonText: '抑制',
      cancelButtonText: '取消',
      type: 'warning',
    })
    // Suppress uses resolve endpoint as the backend treatment for suppression
    const promises = ids.map((id) => api.post(R.ALERT_RESOLVE(id), { suppress: true }))
    const results = await Promise.allSettled(promises)
    const failed = results.filter((r) => r.status === 'rejected').length
    if (failed === 0) {
      ElMessage.success(`${ids.length} 条告警已全部抑制`)
    } else {
      ElMessage.warning(`${ids.length - failed} 条成功，${failed} 条失败`)
    }
    clearSelection()
    loadAlerts()
    loadStats()
  } catch {
    // cancelled
  }
}

async function batchResolve() {
  const ids = selectedIds.value
  if (!ids.length) return
  try {
    await ElMessageBox.confirm(`确认批量恢复 ${ids.length} 条告警？`, '批量恢复', {
      confirmButtonText: '恢复',
      cancelButtonText: '取消',
      type: 'success',
    })
    const promises = ids.map((id) => api.post(R.ALERT_RESOLVE(id)))
    const results = await Promise.allSettled(promises)
    const failed = results.filter((r) => r.status === 'rejected').length
    if (failed === 0) {
      ElMessage.success(`${ids.length} 条告警已全部恢复`)
    } else {
      ElMessage.warning(`${ids.length - failed} 条成功，${failed} 条失败`)
    }
    clearSelection()
    loadAlerts()
    loadStats()
  } catch {
    // cancelled
  }
}

// ── Lifecycle ───────────────────────────────────────────────────────
let statsTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  loadStats()
  loadAlerts()
  // Auto-refresh stats every 30s
  statsTimer = setInterval(loadStats, 30_000)
})

onBeforeUnmount(() => {
  if (statsTimer) {
    clearInterval(statsTimer)
    statsTimer = null
  }
})
</script>

<style scoped>
.alert-list-page {
  padding: 20px;
}

/* ── Statistics Cards ── */
.stats-row {
  margin-bottom: 16px;
}

.stat-card {
  border-radius: 8px;
  overflow: hidden;
}

.stat-card__body {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-card__icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-card__info {
  flex: 1;
  min-width: 0;
}

.stat-card__value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-card__label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.stat-card--critical .stat-card__icon {
  background: rgba(245, 108, 108, 0.12);
  color: #f56c6c;
}
.stat-card--critical .stat-card__value {
  color: #f56c6c;
}

.stat-card--warning .stat-card__icon {
  background: rgba(230, 162, 60, 0.12);
  color: #e6a23c;
}
.stat-card--warning .stat-card__value {
  color: #e6a23c;
}

.stat-card--active .stat-card__icon {
  background: rgba(64, 158, 255, 0.12);
  color: #409eff;
}
.stat-card--active .stat-card__value {
  color: #409eff;
}

.stat-card--resolved .stat-card__icon {
  background: rgba(103, 194, 58, 0.12);
  color: #67c23a;
}
.stat-card--resolved .stat-card__value {
  color: #67c23a;
}

/* ── Main Card ── */
.main-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header__title {
  font-size: 16px;
  font-weight: 600;
}

/* ── Filter Form ── */
.filter-form {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

/* ── Batch Operations Bar ── */
.batch-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  margin-bottom: 12px;
  background: #ecf5ff;
  border: 1px solid #d9ecff;
  border-radius: 6px;
}

.batch-bar__info {
  margin-right: auto;
  font-size: 14px;
  color: #606266;
}

/* ── Table ── */
.alert-table {
  width: 100%;
}

.alert-table :deep(.el-table__fixed-right) {
  right: 0 !important;
}

/* ── Pagination ── */
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* ── Responsive ── */
@media (max-width: 1200px) {
  .filter-form :deep(.el-form-item__content) {
    max-width: 160px;
  }
  .filter-form :deep(.el-date-editor) {
    width: 280px !important;
  }
}
</style>
