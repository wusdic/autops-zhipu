<template>
  <div class="metrics-trend-page">
    <!-- ========== Page Header ========== -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">指标趋势</div>
        <div class="autops-page-desc">CPU、内存、磁盘、网络、数据库、页面响应时间</div>
      </div>
    </div>

    <!-- ========== Filters Card ========== -->
    <div class="autops-card filter-card">
      <div class="autops-card-body">
        <el-form :inline="true" class="autops-toolbar filter-form" @submit.prevent="handleQuery">
          <el-form-item label="选择资产">
            <el-select
              v-model="filters.assetId"
              placeholder="请选择资产"
              clearable
              filterable
              style="width: 240px"
            >
              <el-option
                v-for="item in assetOptions"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="filters.timeRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              format="YYYY-MM-DD HH:mm"
              value-format="YYYY-MM-DDTHH:mm:ssZ"
              style="width: 380px"
            />
          </el-form-item>
          <el-form-item label="指标名称">
            <el-input
              v-model="filters.metricName"
              placeholder="搜索指标名称"
              clearable
              :prefix-icon="Search"
              style="width: 180px"
              @keyup.enter="handleQuery"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="handleQuery" :disabled="!filters.assetId">
              查询
            </el-button>
            <el-button :icon="RefreshLeft" @click="resetFilters">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- ========== Chart Placeholder Card ========== -->
    <div class="autops-card chart-card">
      <div class="autops-card-header">
        <span class="autops-card-title">趋势图表</span>
      </div>
      <div class="autops-card-body chart-placeholder-body">
        <div v-if="!filters.assetId" class="chart-empty">
          <el-icon :size="48" color="#c9cdd4"><DataAnalysis /></el-icon>
          <p class="chart-empty-text">请先选择资产后查询</p>
        </div>
        <div v-else-if="tableData.length === 0 && !loading" class="chart-empty">
          <el-icon :size="48" color="#c9cdd4"><DataAnalysis /></el-icon>
          <p class="chart-empty-text">图表将在此显示</p>
        </div>
        <div v-else class="chart-area">
          <div class="chart-placeholder-text">图表将在此显示</div>
        </div>
      </div>
    </div>

    <!-- ========== Metrics Table Card ========== -->
    <div class="autops-card table-card">
      <div class="autops-card-header">
        <span class="autops-card-title">指标数据</span>
        <el-button :icon="Refresh" circle size="small" @click="loadData" :disabled="!filters.assetId" />
      </div>
      <div class="autops-card-body">
        <el-table stripe
 :data="tableData"
 v-loading="loading"border
 empty-text="暂无数据"
 class="metrics-table"
 >
          <el-table-column prop="metric_name" label="指标名称" min-width="160" show-overflow-tooltip />
          <el-table-column prop="value" label="数值" width="120" align="right">
            <template #default="{ row }">
              <span class="metric-value">{{ formatValue(row.value) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="timestamp" label="时间戳" width="175">
            <template #default="{ row }">
              {{ formatTime(row.timestamp) }}
            </template>
          </el-table-column>
          <el-table-column prop="unit" label="单位" width="80" align="center">
            <template #default="{ row }">
              <span class="text-muted">{{ row.unit || '-' }}</span>
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
            @change="loadData"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, RefreshLeft, DataAnalysis } from '@element-plus/icons-vue'
import { monitoringService, assetService } from '@/shared/api'

// ── State ──────────────────────────────────────────────────────────
const loading = ref(false)
const tableData = ref<any[]>([])
const assetOptions = ref<{ id: string; name: string }[]>([])

const filters = reactive({
  assetId: '',
  timeRange: null as [string, string] | null,
  metricName: '',
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

function formatValue(val: number | null | undefined): string {
  if (val == null) return '-'
  if (Number.isInteger(val)) return String(val)
  return val.toFixed(2)
}

// ── Asset Options ───────────────────────────────────────────────────
async function loadAssetOptions() {
  try {
    const { data } = await assetService.list({ page: 1, page_size: 500 })
    if (data.code === 0) {
      const items = data.data?.items || data.data?.list || []
      assetOptions.value = items.map((a: any) => ({
        id: a.id,
        name: a.name || a.ip || a.id,
      }))
    }
  } catch {
    // silently ignore — asset list is non-critical
  }
}

// ── Data Loading ────────────────────────────────────────────────────
async function loadData() {
  if (!filters.assetId) return
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.metricName) params.metric_name = filters.metricName
    if (filters.timeRange && filters.timeRange.length === 2) {
      params.start_time = filters.timeRange[0]
      params.end_time = filters.timeRange[1]
    }

    const { data } = await monitoringService.metricsTrend(filters.assetId, params)
    if (data.code === 0) {
      tableData.value = data.data?.items || data.data?.list || []
      pagination.total = data.data?.total || 0
    }
  } catch {
    ElMessage.error('加载指标趋势失败')
  } finally {
    loading.value = false
  }
}

function handleQuery() {
  if (!filters.assetId) {
    ElMessage.warning('请先选择资产')
    return
  }
  pagination.page = 1
  loadData()
}

function resetFilters() {
  filters.assetId = ''
  filters.timeRange = null
  filters.metricName = ''
  pagination.page = 1
  tableData.value = []
  pagination.total = 0
}

// ── Lifecycle ───────────────────────────────────────────────────────
onMounted(() => {
  loadAssetOptions()
})
</script>

<style scoped>
.metrics-trend-page {
  padding: 20px;
}

.filter-card {
  border-radius: 8px;
  margin-bottom: 16px;
}

.filter-form {
  margin-bottom: 0;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 8px;
}

.chart-card {
  border-radius: 8px;
  margin-bottom: 16px;
}

.chart-placeholder-body {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.chart-empty-text {
  font-size: 14px;
  color: #86909c;
}

.chart-area {
  width: 100%;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-placeholder-text {
  font-size: 14px;
  color: #86909c;
  padding: 40px 0;
}

.table-card {
  border-radius: 8px;
}

.metrics-table {
  width: 100%;
}
.text-muted {
  color: #86909c;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
