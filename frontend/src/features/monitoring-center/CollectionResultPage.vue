<template>
  <div class="collection-result-page">
    <!-- ========== Page Header ========== -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">采集结果</div>
        <div class="autops-page-desc">原始输出、标准化指标、解析结果、错误详情</div>
      </div>
    </div>

    <!-- ========== Main Card ========== -->
    <div class="autops-card main-card">
      <div class="autops-card-header">
        <span class="autops-card-title">采集结果列表</span>
        <el-button :icon="Refresh" circle size="small" @click="loadData" />
      </div>
      <div class="autops-card-body">
        <!-- ========== Filters ========== -->
        <el-form :inline="true" class="autops-toolbar filter-form" @submit.prevent="handleSearch">
          <el-form-item label="关键词">
            <el-input
              v-model="filters.keyword"
              placeholder="搜索资产名称"
              clearable
              :prefix-icon="Search"
              style="width: 200px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 140px">
              <el-option label="成功" value="success" />
              <el-option label="失败" value="failed" />
              <el-option label="超时" value="timeout" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
            <el-button :icon="RefreshLeft" @click="resetFilters">重置</el-button>
          </el-form-item>
        </el-form>

        <!-- ========== Table ========== -->
        <el-table stripe
 :data="tableData"
 v-loading="loading"border
 empty-text="暂无数据"
 class="result-table"
 >
          <el-table-column prop="asset_name" label="资产名" min-width="160" show-overflow-tooltip />
          <el-table-column prop="collector_type" label="采集器类型" min-width="130" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag
                :type="statusTagType(row.status)"
                size="small"
                effect="light"
              >
                {{ statusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="started_at" label="开始时间" width="175">
            <template #default="{ row }">
              {{ formatTime(row.started_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="duration" label="耗时" width="100" align="center">
            <template #default="{ row }">
              <span v-if="row.duration != null">{{ formatDuration(row.duration) }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="output_summary" label="输出摘要" min-width="200" show-overflow-tooltip />
          <el-table-column label="操作" width="100" fixed="right" align="center">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="viewDetail(row)">查看详情</el-button>
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

    <!-- ========== Detail Dialog ========== -->
    <el-dialog
      v-model="detailVisible"
      title="采集结果详情"
      width="600px"
      destroy-on-close
    >
      <el-descriptions :column="2" border v-if="currentRow">
        <el-descriptions-item label="资产名">{{ currentRow.asset_name }}</el-descriptions-item>
        <el-descriptions-item label="采集器类型">{{ currentRow.collector_type }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTagType(currentRow.status)" size="small">
            {{ statusLabel(currentRow.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="耗时">
          {{ currentRow.duration != null ? formatDuration(currentRow.duration) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="开始时间" :span="2">{{ formatTime(currentRow.started_at) }}</el-descriptions-item>
        <el-descriptions-item label="输出摘要" :span="2">{{ currentRow.output_summary || '-' }}</el-descriptions-item>
        <el-descriptions-item label="错误信息" :span="2" v-if="currentRow.error_message">
          <span class="text-danger">{{ currentRow.error_message }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="原始数据" :span="2">
          <pre class="raw-data-pre">{{ formatRawData(currentRow.raw_data) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, RefreshLeft } from '@element-plus/icons-vue'
import { monitoringService } from '@/shared/api'

// ── State ──────────────────────────────────────────────────────────
const loading = ref(false)
const tableData = ref<any[]>([])
const detailVisible = ref(false)
const currentRow = ref<any>(null)

const filters = reactive({
  keyword: '',
  status: '',
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

function formatDuration(ms: number | null | undefined): string {
  if (ms == null) return '-'
  if (ms < 1000) return `${ms}ms`
  const seconds = Math.floor(ms / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainSeconds = seconds % 60
  return `${minutes}m${remainSeconds}s`
}

function statusTagType(status: string): '' | 'success' | 'danger' | 'warning' | 'info' {
  const map: Record<string, '' | 'success' | 'danger' | 'warning' | 'info'> = {
    success: 'success',
    failed: 'danger',
    timeout: 'warning',
  }
  return map[status] || 'info'
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    success: '成功',
    failed: '失败',
    timeout: '超时',
  }
  return map[status] || status
}

function formatRawData(raw: any): string {
  if (!raw) return '-'
  try {
    return typeof raw === 'string' ? raw : JSON.stringify(raw, null, 2)
  } catch {
    return String(raw)
  }
}

// ── Data Loading ────────────────────────────────────────────────────
async function loadData() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.status) params.status = filters.status

    const { data } = await monitoringService.collectionResults(params)
    if (data.code === 0) {
      tableData.value = data.data?.items || data.data?.list || []
      pagination.total = data.data?.total || 0
    }
  } catch {
    ElMessage.error('加载采集结果失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  loadData()
}

function resetFilters() {
  filters.keyword = ''
  filters.status = ''
  pagination.page = 1
  loadData()
}

// ── Detail Dialog ───────────────────────────────────────────────────
function viewDetail(row: any) {
  currentRow.value = row
  detailVisible.value = true
}

// ── Lifecycle ───────────────────────────────────────────────────────
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.collection-result-page {
  padding: 20px;
}

.main-card {
  border-radius: 8px;
}

.filter-form {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e6eb;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

.result-table {
  width: 100%;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.raw-data-pre {
  max-height: 200px;
  overflow: auto;
  margin: 0;
  padding: 8px;
  background: #f7f8fa;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
