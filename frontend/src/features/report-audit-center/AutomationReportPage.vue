<template>
  <div class="automation-report-page">
    <!-- Page Header -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">自动化报告</div>
        <div class="autops-page-desc">自动化执行统计与详细分析</div>
      </div>
      <div class="header-actions">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 300px"
          @change="loadAll"
        />
        <el-button :icon="Refresh" circle size="small" @click="loadAll" />
      </div>
    </div>

    <!-- Statistics Cards -->
    <el-row :gutter="16" class="stats-row mb-lg">
      <el-col :xs="12" :sm="6">
        <div class="autops-card stat-card stat-card--total">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="28"><Operation /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.total }}</div>
              <div class="stat-card__label">执行总数</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="autops-card stat-card stat-card--success">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="28"><CircleCheckFilled /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.successRate }}%</div>
              <div class="stat-card__label">成功率</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="autops-card stat-card stat-card--failed">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="28"><CircleCloseFilled /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.failedCount }}</div>
              <div class="stat-card__label">失败数</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="autops-card stat-card stat-card--duration">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="28"><Timer /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.avgDuration }}</div>
              <div class="stat-card__label">平均耗时</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Execution Breakdown Table -->
    <div class="autops-card mb-lg">
      <div class="autops-card-header">
        <span class="autops-card-title">执行分类统计</span>
      </div>
      <div class="autops-card-body p-0">
        <el-table stripe
 :data="breakdownData"
 v-loading="statsLoading"border
 size="small"
 empty-text="暂无数据"
 class="breakdown-table"
 >
          <el-table-column prop="category" label="分类" min-width="160" show-overflow-tooltip />
          <el-table-column prop="total" label="执行总数" width="100" align="center" />
          <el-table-column prop="success" label="成功" width="80" align="center">
            <template #default="{ row }">
              <span style="color: #00b42a; font-weight: 500">{{ row.success || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="failed" label="失败" width="80" align="center">
            <template #default="{ row }">
              <span style="color: #f53f3f; font-weight: 500">{{ row.failed || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="success_rate" label="成功率" width="100" align="center">
            <template #default="{ row }">
              <el-progress
                :percentage="Number(row.success_rate || 0)"
                :stroke-width="14"
                :text-inside="true"
                :color="row.success_rate >= 90 ? '#00b42a' : row.success_rate >= 70 ? '#ff7d00' : '#f53f3f'"
                style="max-width: 120px"
              />
            </template>
          </el-table-column>
          <el-table-column prop="avg_duration" label="平均耗时" width="120" align="center">
            <template #default="{ row }">{{ formatDuration(row.avg_duration) }}</template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- Recent Executions Table -->
    <div class="autops-card">
      <div class="autops-card-header">
        <span class="autops-card-title">最近执行记录</span>
        <div class="card-header__actions">
          <el-button :icon="Refresh" circle size="small" @click="loadExecutions" />
        </div>
      </div>
      <div class="autops-card-body">
        <!-- Filters -->
        <el-form :inline="true" class="autops-toolbar filter-form" @submit.prevent="handleSearch">
          <el-form-item label="状态">
            <el-select v-model="execFilters.status" placeholder="全部状态" clearable style="width: 130px">
              <el-option label="成功" value="success" />
              <el-option label="失败" value="failed" />
              <el-option label="运行中" value="running" />
              <el-option label="超时" value="timeout" />
            </el-select>
          </el-form-item>
          <el-form-item label="关键词">
            <el-input
              v-model="execFilters.keyword"
              placeholder="搜索Playbook名称"
              clearable
              :prefix-icon="Search"
              style="width: 180px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
            <el-button :icon="RefreshLeft" @click="resetExecFilters">重置</el-button>
          </el-form-item>
        </el-form>

        <el-table stripe
 :data="executions"
 v-loading="execLoading"border
 row-key="id"
 class="exec-table"
 >
          <el-table-column label="Playbook" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.playbook_name || row.execution_type || row.target_id || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="execStatusType(row.status)" size="small">{{ execStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="trigger_source" label="触发方式" width="100" align="center">
            <template #default="{ row }">
              <el-tag size="small" type="info">{{ triggerLabel(row.trigger_source) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="耗时" width="100" align="center">
            <template #default="{ row }">
              {{ calcExecDuration(row.started_at, row.completed_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="started_at" label="开始时间" width="170">
            <template #default="{ row }">{{ formatTime(row.started_at || row.created_at) }}</template>
          </el-table-column>
          <el-table-column prop="completed_at" label="完成时间" width="170">
            <template #default="{ row }">{{ formatTime(row.completed_at) }}</template>
          </el-table-column>
        </el-table>

        <!-- Pagination -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="execPagination.page"
            v-model:page-size="execPagination.pageSize"
            :total="execPagination.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            background
            @change="loadExecutions"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, RefreshLeft } from '@element-plus/icons-vue'
import { Operation, CircleCheckFilled, CircleCloseFilled, Timer } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

// ── State ──────────────────────────────────────────────────────────
const statsLoading = ref(false)
const execLoading = ref(false)
const dateRange = ref<[string, string] | null>(null)
const breakdownData = ref<any[]>([])
const executions = ref<any[]>([])

const stats = reactive({
  total: 0,
  successRate: 0,
  failedCount: 0,
  avgDuration: '-',
})

const execFilters = reactive({
  status: '',
  keyword: '',
})

const execPagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

// ── Helpers ────────────────────────────────────────────────────────
function formatTime(val: string | null | undefined): string {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds())
}

function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null) return '-'
  if (seconds < 60) return seconds.toFixed(1) + 's'
  const min = Math.floor(seconds / 60)
  const sec = Math.round(seconds % 60)
  if (min < 60) return min + 'm' + sec + 's'
  const hr = Math.floor(min / 60)
  return hr + 'h' + min % 60 + 'm'
}

function execStatusType(s: string): string {
  const map: Record<string, string> = { success: 'success', failed: 'danger', running: 'warning', timeout: 'info', cancelled: 'info' }
  return map[s] || 'info'
}

function execStatusLabel(s: string): string {
  const map: Record<string, string> = { success: '成功', failed: '失败', running: '运行中', timeout: '超时', cancelled: '已取消' }
  return map[s] || s || '-'
}

function triggerLabel(t: string): string {
  var map: Record<string, string> = { manual: '手动', policy: '策略', schedule: '定时', alert: '告警', api: 'API' }
  return map[t] || t || '-'
}

function calcExecDuration(startAt: string | null, completedAt: string | null): string {
  if (!startAt) return '-'
  var start = new Date(startAt).getTime()
  if (isNaN(start)) return '-'
  var end = completedAt ? new Date(completedAt).getTime() : Date.now()
  var diff = Math.max(0, end - start)
  var seconds = Math.round(diff / 1000)
  return formatDuration(seconds)
}

// ── Data Loading ───────────────────────────────────────────────────
async function loadStats() {
  statsLoading.value = true
  try {
    const params: Record<string, any> = {}
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const { data } = await client.get(API.AUTOMATION.STATS, { params })
    if (data.code === 0 && data.data) {
      const d = data.data
      stats.total = d.total ?? d.total_executions ?? 0
      stats.successRate = d.success_rate ?? Math.round(((d.success ?? 0) / Math.max(stats.total, 1)) * 100)
      stats.failedCount = d.failed ?? d.failed_count ?? 0
      stats.avgDuration = d.avg_duration != null ? formatDuration(d.avg_duration) : '-'

      // Breakdown data from stats
      breakdownData.value = d.breakdown || d.by_category || d.categories || []
    }
  } catch {
    // silently ignore
  } finally {
    statsLoading.value = false
  }
}

async function loadExecutions() {
  execLoading.value = true
  try {
    const params: Record<string, any> = {
      page: execPagination.page,
      page_size: execPagination.pageSize,
    }
    if (execFilters.status) params.status = execFilters.status
    if (execFilters.keyword) params.keyword = execFilters.keyword
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }

    const { data } = await client.get(API.EXECUTIONS, { params })
    if (data.code === 0) {
      executions.value = data.data?.items || data.data?.list || []
      execPagination.total = data.data?.total || 0

      // Derive stats from execution list if stats API didn't return data
      if (stats.total === 0 && executions.value.length > 0) {
        const total = execPagination.total
        const successList = executions.value.filter(e => e.status === 'success')
        const failedList = executions.value.filter(e => e.status === 'failed')
        stats.total = total
        stats.successRate = total > 0 ? Math.round((successList.length / executions.value.length) * 100) : 0
        stats.failedCount = failedList.length
      }
    }
  } catch (err: any) {
    ElMessage.error(err.message || '加载执行记录失败')
  } finally {
    execLoading.value = false
  }
}

function loadAll() {
  loadStats()
  execPagination.page = 1
  loadExecutions()
}

function handleSearch() {
  execPagination.page = 1
  loadExecutions()
}

function resetExecFilters() {
  execFilters.status = ''
  execFilters.keyword = ''
  execPagination.page = 1
  loadExecutions()
}

// ── Lifecycle ──────────────────────────────────────────────────────
onMounted(() => {
  loadAll()
})
</script>

<style scoped>
.automation-report-page {
  padding: var(--autops-space-xl);
}


.stats-row {
  margin-bottom: var(--autops-space-lg);
}
.stat-card__body {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: var(--autops-space-xs) 0;
}

.stat-card__icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
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
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-card__label {
  font-size: var(--autops-font-12);
  color: var(--autops-info);
  margin-top: 2px;
}

.autops-metric-card--total .stat-card__icon { background: rgba(64, 158, 255, 0.12); color: var(--autops-primary); }
.autops-metric-card--total .stat-card__value { color: var(--autops-primary); }
.autops-metric-card--success .stat-card__icon { background: rgba(103, 194, 58, 0.12); color: var(--autops-success); }
.autops-metric-card--success .stat-card__value { color: var(--autops-success); }
.autops-metric-card--failed .stat-card__icon { background: rgba(245, 108, 108, 0.12); color: var(--autops-danger); }
.autops-metric-card--failed .stat-card__value { color: var(--autops-danger); }
.autops-metric-card--duration .stat-card__icon { background: rgba(144, 147, 153, 0.12); color: var(--autops-info); }
.autops-metric-card--duration .stat-card__value { color: var(--autops-text-2); }
.filter-form {
  margin-bottom: var(--autops-space-lg);
  padding-bottom: 16px;
  border-bottom: 1px solid var(--autops-bg-4);
}

.filter-form :deep(.el-form-item) {
  margin-bottom: var(--autops-space-md);
}

.breakdown-table,
.exec-table {
  width: 100%;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--autops-space-lg);
}
</style>
