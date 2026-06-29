<template>
  <div class="autops-page-container">
    <PageHeader title="执行历史" desc="查看所有自动化执行记录与状态" />

    <!-- ========== Statistics Row ========== -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <div class="autops-card stat-card stat-card--today">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="32"><Document /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.todayTotal }}</div>
              <div class="stat-card__label">今日执行</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card stat-card--running">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="32"><Loading /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.runningNow }}</div>
              <div class="stat-card__label">执行中</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card stat-card--success">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="32"><CircleCheckFilled /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.successRate }}%</div>
              <div class="stat-card__label">成功率</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card stat-card--failed">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="32"><CircleCloseFilled /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.failedCount }}</div>
              <div class="stat-card__label">失败数</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- ========== Trend Chart ========== -->
    <div class="autops-card trend-card">
      
        <div class="autops-card-header">
          <span class="autops-card-title">执行趋势（近 7 天）</span>
        </div>
      
      <MetricChart
        :multiple="trendSeries"
        chart-type="bar"
        :height="260"
      />
    </div>

    <!-- ========== Main Card ========== -->
    <div class="autops-card main-card">
      
        <div class="autops-card-header">
          <span class="autops-card-title">执行历史</span>
          <div class="autops-card-header-actions">
            <el-switch
              v-model="autoRefresh"
              active-text="自动刷新"
              inactive-text=""
              style="margin-right: 12px"
            />
            <el-button :icon="Refresh" circle size="small" @click="handleSearch" />
          </div>
        </div>
      

      <!-- ========== Filters ========== -->
      <div class="autops-toolbar">
      <el-form :inline="true" class="filter-form" @submit.prevent="handleSearch">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 140px">
            <el-option label="已创建" value="created" />
            <el-option label="已校验" value="validated" />
            <el-option label="执行中" value="running" />
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
            <el-option label="部分成功" value="partial_success" />
            <el-option label="已回滚" value="rollback" />
          </el-select>
        </el-form-item>
        <el-form-item label="触发来源">
          <el-select v-model="filters.triggerSource" placeholder="全部来源" clearable style="width: 140px">
            <el-option label="手动触发" value="manual" />
            <el-option label="策略触发" value="policy" />
            <el-option label="AIOps触发" value="aiops" />
            <el-option label="工单触发" value="ticket" />
          </el-select>
        </el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="filters.riskLevel" placeholder="全部等级" clearable style="width: 130px">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="严重" value="critical" />
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
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            placeholder="执行ID / Playbook / 脚本"
            clearable
            :prefix-icon="Search"
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="RefreshLeft" @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

      <!-- ========== Batch Operations Bar ========== -->
      <transition name="el-fade-in">
        <div v-if="selectedIds.length > 0" class="batch-bar">
          <span class="batch-bar__info">
            已选择 <strong>{{ selectedIds.length }}</strong> 条执行
          </span>
          <el-button type="warning" size="small" :icon="CloseBold" @click="batchCancel">
            批量取消
          </el-button>
          <el-button type="danger" size="small" :icon="RefreshRight" @click="batchRetry">
            批量重试
          </el-button>
          <el-button size="small" @click="clearSelection">取消选择</el-button>
        </div>
      </transition>

      <!-- ========== Execution Table ========== -->
      <el-table stripe
 ref="tableRef"
 :data="executions"
 v-loading="loading"border
 row-key="execution_id"
 @selection-change="handleSelectionChange"
 class="execution-table"
 >
        <el-table-column type="selection" width="45" fixed="left" />
        <el-table-column prop="id" label="执行ID" width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <el-button plain type="primary" @click="goDetail(row)">
              {{ truncateId(row.id) }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="execution_type" label="类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.execution_type || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="trigger_source" label="触发来源" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="(triggerSourceType(row.trigger_source)) as TagType" size="small" effect="plain">
              {{ triggerSourceLabel(row.trigger_source) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="asset_ids" label="目标资产" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.asset_ids && row.asset_ids.length">
              {{ row.asset_ids.length }} 个资产
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_dry_run" label="Dry-run" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_dry_run" size="small" type="warning">模拟</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险等级" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              v-if="row.risk_level"
              :type="(riskLevelType(row.risk_level)) as TagType"
              size="small"
            >
              {{ riskLevelLabel(row.risk_level) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <StatusBadge :status="row.status" size="small" show-icon />
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="175">
          <template #default="{ row }">
            {{ formatTime(row.started_at || row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="120" align="center">
          <template #default="{ row }">
            <span v-if="row.duration">{{ formatDuration(row.duration) }}</span>
            <span v-else-if="row.started_at">{{ computeDuration(row.started_at, row.finished_at) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              type="primary" plain
              @click="viewLogs(row)"
            >日志</el-button>
            <el-button
              type="warning" plain
              @click="cancelExecution(row)"
            >取消</el-button>
            <el-button
              type="danger" plain
              @click="retryExecution(row)"
            >重试</el-button>
            <el-button
              size="small"
              plain
              @click="goDetail(row)"
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
          @change="loadExecutions"
        />
      </div>
    </div>

    <!-- ========== Log Drawer ========== -->
    <el-drawer
      v-model="logDrawerVisible"
      :title="'执行日志 - ' + logDrawerTitle"
      direction="rtl"
      size="55%"
      :destroy-on-close="true"
    >
      <div class="log-drawer-content">
        <div v-if="logLoading" style="text-align: center; padding: 40px">
          <el-icon :size="24" class="is-loading"><Loading /></el-icon>
          <span style="margin-left: 8px; color: #86909c">加载日志中...</span>
        </div>
        <LogStream
          v-else-if="logLines.length > 0"
          :lines="logLines"
          height="calc(100vh - 100px)"
        />
        <div v-else class="log-empty">
          <el-empty description="暂无日志" />
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  RefreshLeft,
  RefreshRight,
  CloseBold,
  Document,
  Loading,
  CircleCheckFilled,
  CircleCloseFilled,
} from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import PageHeader from '@/shared/components/PageHeader.vue'
import { API as R } from '@/shared/api/routes'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import MetricChart from '@/shared/components/MetricChart.vue'
import LogStream from '@/shared/components/LogStream.vue'
import { riskTag, riskLabel } from '@/shared/utils/labels'

const router = useRouter()

// ── State ──────────────────────────────────────────────────────────
const loading = ref(false)
const executions = ref<any[]>([])
const selectedRows = ref<any[]>([])
const selectedIds = ref<string[]>([])
const tableRef = ref()
const autoRefresh = ref(false)

const stats = reactive({
  todayTotal: 0,
  runningNow: 0,
  successRate: 0,
  failedCount: 0,
})

const trendSeries = ref<Array<{ name: string; data: Array<{ time: string; value: number }>; color: string }>>([])

const filters = reactive({
  status: '',
  triggerSource: '',
  riskLevel: '',
  dateRange: null as [string, string] | null,
  keyword: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const logDrawerVisible = ref(false)
const logDrawerTitle = ref('')
const logExecutionId = ref('')
const logLines = ref<string[]>([])
const logLoading = ref(false)

// ── Helpers ─────────────────────────────────────────────────────────
function formatTime(val: string | null | undefined): string {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds())
}

function computeDuration(start: string | null | undefined, end?: string | null): string {
  if (!start) return '-'
  const s = new Date(start).getTime()
  if (isNaN(s)) return '-'
  const e = end ? new Date(end).getTime() : Date.now()
  if (isNaN(e)) return '-'
  const diff = Math.max(0, Math.floor((e - s) / 1000))
  return formatDuration(diff)
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return seconds + '秒'
  if (seconds < 3600) return Math.floor(seconds / 60) + '分' + seconds % 60 + '秒'
  if (seconds < 86400) return Math.floor(seconds / 3600) + '时' + Math.floor((seconds % 3600) / 60) + '分'
  return Math.floor(seconds / 86400) + '天' + Math.floor((seconds % 86400) / 3600) + '时'
}

function truncateId(id: string | undefined): string {
  if (!id) return '-'
  return id.length > 12 ? id.slice(0, 8) + '...' + id.slice(-4) : id
}

function triggerSourceType(source: string): TagType {
  const map: Record<string, string> = {
    manual: 'primary', policy: 'success', aiops: 'warning', ticket: 'info',
  }
  return (map[source] || 'info') as TagType
}

function triggerSourceLabel(source: string): string {
  const map: Record<string, string> = {
    manual: '手动', policy: '策略', aiops: 'AIOps', ticket: '工单',
  }
  return map[source] || source || '-'
}

// 风险等级统一取自 shared/utils/labels.ts
const riskLevelType = (level: string): TagType => riskTag(level) as TagType
const riskLevelLabel = (level: string): string => riskLabel(level)

function canCancel(status: string): boolean {
  return ['pending', 'awaiting_approval', 'approved', 'running'].includes(status)
}

function canRetry(status: string): boolean {
  return ['failed', 'rollback_failed', 'dry_run_failed'].includes(status)
}

// ── Statistics ──────────────────────────────────────────────────────
async function loadStats() {
  try {
    const { data } = await api.get(R.EXECUTIONS, {
      params: { page: 1, page_size: 1, stats: true },
    })
    if (data.code === 0 && data.data) {
      const d = data.data
      stats.todayTotal = d.today_total ?? d.todayTotal ?? 0
      stats.runningNow = d.running_now ?? d.runningNow ?? 0
      stats.successRate = d.success_rate ?? d.successRate ?? 0
      stats.failedCount = d.failed_count ?? d.failedCount ?? 0
    }
  } catch {
    // stats are non-critical; silently ignore
  }
}

// ── Trend Chart ─────────────────────────────────────────────────────
async function loadTrend() {
  try {
    const now = new Date()
    const days: string[] = []
    for (let i = 6; i >= 0; i--) {
      const d = new Date(now)
      d.setDate(d.getDate() - i)
      const pad = (n: number) => String(n).padStart(2, '0')
      days.push(pad(d.getMonth() + 1) + '-' + pad(d.getDate()))
    }

    // Build the trend data for the chart
    const successData: Array<{ time: string; value: number }> = []
    const failData: Array<{ time: string; value: number }> = []

    // Try fetching trend data from API; fall back to computed from list
    try {
      const { data } = await api.get(R.EXECUTIONS, {
        params: { trend: '7d' },
      })
      if (data.code === 0 && data.data?.trend) {
        const trend = data.data.trend
        for (const day of days) {
          const entry = trend.find((t: any) => t.date === day || t.time === day)
          successData.push({ time: day, value: entry?.success ?? entry?.success_count ?? 0 })
          failData.push({ time: day, value: entry?.failed ?? entry?.fail_count ?? 0 })
        }
      } else {
        // Generate zero data
        for (const day of days) {
          successData.push({ time: day, value: 0 })
          failData.push({ time: day, value: 0 })
        }
      }
    } catch {
      for (const day of days) {
        successData.push({ time: day, value: 0 })
        failData.push({ time: day, value: 0 })
      }
    }

    trendSeries.value = [
      { name: '成功', data: successData, color: '#00b42a' },
      { name: '失败', data: failData, color: '#f53f3f' },
    ]
  } catch {
    // trend is non-critical
  }
}

// ── Execution List ──────────────────────────────────────────────────
async function loadExecutions() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.status) params.status = filters.status
    if (filters.triggerSource) params.trigger_source = filters.triggerSource
    if (filters.riskLevel) params.risk_level = filters.riskLevel
    if (filters.keyword) params.search = filters.keyword
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_time = filters.dateRange[0]
      params.end_time = filters.dateRange[1]
    }
    const { data } = await api.get(R.EXECUTIONS, { params })
    if (data.code === 0) {
      executions.value = data.data.items || data.data.list || []
      pagination.total = data.data.total || 0
    }
  } catch {
    ElMessage.error('加载执行历史失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  loadExecutions()
}

function resetFilters() {
  filters.status = ''
  filters.triggerSource = ''
  filters.riskLevel = ''
  filters.dateRange = null
  filters.keyword = ''
  pagination.page = 1
  loadExecutions()
}

// ── Selection ───────────────────────────────────────────────────────
function handleSelectionChange(rows: any[]) {
  selectedRows.value = rows
  selectedIds.value = rows.map((r) => r.execution_id || r.id)
}

function clearSelection() {
  tableRef.value?.clearSelection()
}

// ── Navigation ──────────────────────────────────────────────────────
function goDetail(row: any) {
  router.push({ name: 'execution-detail', params: { id: row.execution_id || row.id } })
}

// ── Quick Actions ───────────────────────────────────────────────────
async function viewLogs(row: any) {
  const id = row.execution_id || row.id
  logExecutionId.value = id
  logDrawerTitle.value = truncateId(id)
  logLines.value = []
  logDrawerVisible.value = true
  logLoading.value = true
  try {
    const { data } = await api.get(R.LOGS.EXECUTION(id))
    if (data.code === 0 && data.data) {
      // API may return lines array or log string
      if (Array.isArray(data.data)) {
        logLines.value = data.data
      } else if (data.data.lines) {
        logLines.value = data.data.lines
      } else if (data.data.log) {
        logLines.value = data.data.log.split('\n')
      } else if (typeof data.data === 'string') {
        logLines.value = data.data.split('\n')
      }
    }
  } catch {
    ElMessage.warning('加载日志失败')
  } finally {
    logLoading.value = false
  }
}

async function cancelExecution(row: any) {
  const id = row.execution_id || row.id
  try {
    await ElMessageBox.confirm(
      '确认取消执行 ' + truncateId(id) + '？执行中的任务将被终止。',
      '取消执行',
      { confirmButtonText: '确认取消', cancelButtonText: '返回', type: 'warning' },
    )
    const { data } = await api.post(R.EXECUTION_CANCEL(id))
    if (data.code === 0) {
      ElMessage.success('执行已取消')
      loadExecutions()
      loadStats()
    }
  } catch {
    // cancelled by user
  }
}

async function retryExecution(row: any) {
  const id = row.execution_id || row.id
  try {
    await ElMessageBox.confirm(
      '确认重新执行 ' + truncateId(id) + '？将使用相同的参数重新发起执行。',
      '重新执行',
      { confirmButtonText: '确认重试', cancelButtonText: '返回', type: 'info' },
    )
    // 调用专用 retry 端点克隆并入队（参数由后端从源执行复制）
    const { data } = await api.post(R.EXECUTION_RETRY(id))
    if (data.code === 0) {
      ElMessage.success('已重新发起执行')
      loadExecutions()
      loadStats()
    }
  } catch {
    // cancelled by user or error
  }
}

// ── Batch Operations ────────────────────────────────────────────────
async function batchCancel() {
  const ids = selectedIds.value
  if (!ids.length) return
  const cancellable = selectedRows.value.filter((r) => canCancel(r.status))
  if (!cancellable.length) {
    ElMessage.warning('所选执行中没有可取消的项（仅待执行/运行中可取消）')
    return
  }
  try {
    await ElMessageBox.confirm(
      '确认批量取消 ' + cancellable.length + ' 条执行？',
      '批量取消',
      { confirmButtonText: '确认取消', cancelButtonText: '返回', type: 'warning' },
    )
    const promises = cancellable.map((r) =>
      api.post(R.EXECUTION_CANCEL(r.execution_id || r.id)),
    )
    const results = await Promise.allSettled(promises)
    const failed = results.filter((r) => r.status === 'rejected').length
    if (failed === 0) {
      ElMessage.success(cancellable.length + ' 条执行已全部取消')
    } else {
      ElMessage.warning(cancellable.length - failed + ' 条成功，' + failed + ' 条失败')
    }
    clearSelection()
    loadExecutions()
    loadStats()
  } catch {
    // cancelled
  }
}

async function batchRetry() {
  const ids = selectedIds.value
  if (!ids.length) return
  const retriable = selectedRows.value.filter((r) => canRetry(r.status))
  if (!retriable.length) {
    ElMessage.warning('所选执行中没有可重试的项（仅失败/部分成功/回滚可重试）')
    return
  }
  try {
    await ElMessageBox.confirm(
      '确认批量重新执行 ' + retriable.length + ' 条执行？',
      '批量重试',
      { confirmButtonText: '确认重试', cancelButtonText: '返回', type: 'info' },
    )
    const promises = retriable.map((r) =>
      api.post(R.EXECUTIONS, {
        source_execution_id: r.execution_id || r.id,
        trigger_source: 'manual',
      }),
    )
    const results = await Promise.allSettled(promises)
    const failed = results.filter((r) => r.status === 'rejected').length
    if (failed === 0) {
      ElMessage.success(retriable.length + ' 条执行已全部重新发起')
    } else {
      ElMessage.warning(retriable.length - failed + ' 条成功，' + failed + ' 条失败')
    }
    clearSelection()
    loadExecutions()
    loadStats()
  } catch {
    // cancelled
  }
}

// ── Auto-refresh ────────────────────────────────────────────────────
let refreshTimer: ReturnType<typeof setInterval> | null = null

watch(autoRefresh, (enabled) => {
  if (enabled) {
    refreshTimer = setInterval(() => {
      loadExecutions()
      loadStats()
    }, 10_000)
  } else {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }
})

// ── Lifecycle ───────────────────────────────────────────────────────
onMounted(() => {
  loadStats()
  loadTrend()
  loadExecutions()
})

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.execution-list-page {
  padding: var(--autops-space-xl);
}

/* ── Statistics Cards ── */
.stats-row {
  margin-bottom: var(--autops-space-lg);
}
.stat-card__body {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-card__icon {
  width: 56px;
  height: 56px;
  border-radius: var(--autops-radius-lg);
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
  font-size: var(--autops-font-13);
  color: var(--autops-info);
  margin-top: 4px;
}

.autops-metric-card--today .stat-card__icon {
  background: rgba(64, 158, 255, 0.12);
  color: var(--autops-primary);
}
.autops-metric-card--today .stat-card__value {
  color: var(--autops-primary);
}

.autops-metric-card--running .stat-card__icon {
  background: rgba(230, 162, 60, 0.12);
  color: var(--autops-warning);
}
.autops-metric-card--running .stat-card__value {
  color: var(--autops-warning);
}

.autops-metric-card--success .stat-card__icon {
  background: rgba(103, 194, 58, 0.12);
  color: var(--autops-success);
}
.autops-metric-card--success .stat-card__value {
  color: var(--autops-success);
}

.autops-metric-card--failed .stat-card__icon {
  background: rgba(245, 108, 108, 0.12);
  color: var(--autops-danger);
}
.autops-metric-card--failed .stat-card__value {
  color: var(--autops-danger);
}

/* ── Trend Card ── */
.trend-card {
  margin-bottom: var(--autops-space-lg);
  border-radius: var(--autops-radius-md);
}

/* ── Main Card ── */
.main-card {
  border-radius: var(--autops-radius-md);
}
/* ── Filter Form ── */
.filter-form {
  margin-bottom: var(--autops-space-lg);
  padding-bottom: 16px;
  border-bottom: 1px solid var(--autops-bg-4);
}

.filter-form :deep(.el-form-item) {
  margin-bottom: var(--autops-space-md);
}

/* ── Batch Operations Bar ── */
.batch-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  margin-bottom: var(--autops-space-md);
  background: var(--autops-primary-light-5);
  border: 1px solid var(--autops-primary-light-5);
  border-radius: 6px;
}

.batch-bar__info {
  margin-right: auto;
  font-size: var(--autops-font-14);
  color: var(--autops-text-2);
}

/* ── Table ── */
.execution-table {
  width: 100%;
}

.execution-table :deep(.el-table__fixed-right) {
  right: 0 !important;
}

/* ── Pagination ── */
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--autops-space-lg);
}

/* ── Log Drawer ── */
.log-drawer-content {
  padding: 0 8px;
  height: calc(100vh - 80px);
  overflow-y: auto;
}

.log-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
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
