<template>
  <div class="inspection-report-page">
    <!-- Page Header -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">巡检报告</div>
        <div class="autops-page-desc">巡检结果汇总报告、下载和归档</div>
      </div>
    </div>

    <!-- Main Card -->
    <div class="autops-card main-card">
      <div class="autops-card-header">
        <span class="autops-card-title">报告列表</span>
        <div class="card-header__actions">
          <el-button :icon="Refresh" circle size="small" @click="loadReports" />
        </div>
      </div>
      <div class="autops-card-body">
        <!-- Filters -->
        <el-form :inline="true" class="autops-toolbar filter-form" @submit.prevent="handleSearch">
          <el-form-item label="关键词">
            <el-input
              v-model="filters.keyword"
              placeholder="搜索报告名"
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

        <!-- Table -->
        <el-table
          :data="reports"
          v-loading="loading"
          stripe
          border
          row-key="id"
          class="report-table"
        >
          <el-table-column prop="title" label="报告名" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="report-name-link" @click="viewReport(row)">{{ row.title || row.name || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="task_name" label="关联任务" min-width="160" show-overflow-tooltip />
          <el-table-column prop="pass_rate" label="合格率" width="100" align="center">
            <template #default="{ row }">
              <el-progress
                type="dashboard"
                :percentage="Number(row.pass_rate || row.compliance_rate || 0)"
                :width="48"
                :color="rateColor(Number(row.pass_rate || row.compliance_rate || 0))"
              />
            </template>
          </el-table-column>
          <el-table-column prop="critical_issues" label="严重问题数" width="110" align="center">
            <template #default="{ row }">
              <span :style="{ color: (row.critical_issues || row.severe_count || 0) > 0 ? '#f56c6c' : '#67c23a', fontWeight: 600 }">
                {{ row.critical_issues || row.severe_count || 0 }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="generated_at" label="生成时间" width="170">
            <template #default="{ row }">{{ formatTime(row.generated_at || row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right" align="center">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="viewReport(row)">查看</el-button>
              <el-button size="small" link @click="downloadReport(row)">下载</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- Pagination -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            background
            @change="loadReports"
          />
        </div>
      </div>
    </div>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="detailVisible"
      :title="detailData?.title || '报告详情'"
      width="680px"
      destroy-on-close
    >
      <el-descriptions v-if="detailData" :column="2" border size="small">
        <el-descriptions-item label="报告名" :span="2">{{ detailData.title || detailData.name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="关联任务">{{ detailData.task_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="合格率">
          <span :style="{ color: rateColor(Number(detailData.pass_rate || 0)) }">
            {{ detailData.pass_rate || 0 }}%
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="严重问题">{{ detailData.critical_issues || detailData.severe_count || 0 }}</el-descriptions-item>
        <el-descriptions-item label="一般问题">{{ detailData.warning_issues || detailData.warning_count || 0 }}</el-descriptions-item>
        <el-descriptions-item label="生成时间" :span="2">{{ formatTime(detailData.generated_at || detailData.created_at) }}</el-descriptions-item>
      </el-descriptions>

      <!-- Check Result Summary -->
      <div v-if="detailData?.items && detailData.items.length" style="margin-top: 16px">
        <h4 style="margin-bottom: 8px; font-size: 14px; color: #303133">检查结果明细</h4>
        <el-table :data="detailData.items" stripe border size="small" max-height="300">
          <el-table-column prop="check_item" label="检查项" min-width="160" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="90" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'pass' ? 'success' : row.status === 'fail' ? 'danger' : 'warning'" size="small">
                {{ row.status === 'pass' ? '通过' : row.status === 'fail' ? '不通过' : '警告' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="severity" label="严重级别" width="100" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.severity" :type="severityType(row.severity)" size="small">{{ row.severity }}</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="detail" label="详情" min-width="200" show-overflow-tooltip />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="downloadReport(detailData)">下载</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, RefreshLeft } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

// ── State ──────────────────────────────────────────────────────────
const loading = ref(false)
const reports = ref<any[]>([])
const detailVisible = ref(false)
const detailData = ref<any>(null)

const filters = reactive({
  keyword: '',
})

const pagination = reactive({
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
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function rateColor(rate: number): string {
  if (rate >= 90) return '#67c23a'
  if (rate >= 70) return '#e6a23c'
  return '#f56c6c'
}

function severityType(severity: string): string {
  const map: Record<string, string> = { critical: 'danger', high: 'warning', medium: '', low: 'info' }
  return map[severity] || 'info'
}

// ── Data Loading ───────────────────────────────────────────────────
async function loadReports() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.keyword) params.keyword = filters.keyword

    const { data } = await client.get(API.INSPECTION.REPORTS, { params })
    if (data.code === 0) {
      reports.value = data.data?.items || data.data?.list || []
      pagination.total = data.data?.total || 0
    }
  } catch (err: any) {
    ElMessage.error(err.message || '加载巡检报告失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  loadReports()
}

function resetFilters() {
  filters.keyword = ''
  pagination.page = 1
  loadReports()
}

// ── Actions ────────────────────────────────────────────────────────
async function viewReport(row: any) {
  try {
    const { data } = await client.get(API.INSPECTION.REPORT_DETAIL(row.id))
    if (data.code === 0) {
      detailData.value = data.data || row
    } else {
      detailData.value = row
    }
  } catch {
    detailData.value = row
  }
  detailVisible.value = true
}

async function downloadReport(row: any) {
  try {
    const { data } = await client.get(API.INSPECTION.REPORT_DETAIL(row.id), {
      params: { download: true },
      responseType: 'blob',
    })
    if (data instanceof Blob) {
      const url = URL.createObjectURL(data)
      const link = document.createElement('a')
      link.href = url
      link.download = `${row.title || row.name || 'inspection-report'}.pdf`
      link.click()
      URL.revokeObjectURL(url)
      ElMessage.success('下载成功')
    } else {
      ElMessage.warning('下载格式异常')
    }
  } catch (err: any) {
    ElMessage.error(err.message || '下载失败')
  }
}

// ── Lifecycle ──────────────────────────────────────────────────────
onMounted(() => {
  loadReports()
})
</script>

<style scoped>
.inspection-report-page {
  padding: 20px;
}

.main-card {
  border-radius: 8px;
}

.card-header__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-form {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

.report-table {
  width: 100%;
}

.report-name-link {
  cursor: pointer;
  color: #409eff;
}

.report-name-link:hover {
  text-decoration: underline;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
