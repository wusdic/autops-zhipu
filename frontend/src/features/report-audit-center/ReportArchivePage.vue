<template>
  <div class="report-archive-page">
    <!-- Page Header -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">报表归档</div>
        <div class="autops-page-desc">历史报表存储、下载与管理</div>
      </div>
    </div>

    <!-- Main Card -->
    <div class="autops-card main-card">
      <div class="autops-card-header">
        <span class="autops-card-title">归档列表</span>
        <div class="card-header__actions">
          <el-button :icon="Refresh" circle size="small" @click="loadArchive" />
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
          <el-form-item label="类型">
            <el-select v-model="filters.type" placeholder="全部类型" clearable style="width: 150px">
              <el-option label="巡检报告" value="inspection" />
              <el-option label="异常报告" value="anomaly" />
              <el-option label="自动化报告" value="automation" />
              <el-option label="资产报告" value="asset" />
              <el-option label="合规报告" value="compliance" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
            <el-button :icon="RefreshLeft" @click="resetFilters">重置</el-button>
          </el-form-item>
        </el-form>

        <!-- Table -->
        <el-table stripe
 :data="archiveList"
 v-loading="loading"border
 row-key="id"
 class="archive-table"
 >
          <el-table-column prop="title" label="报告名" min-width="200" show-overflow-tooltip />
          <el-table-column prop="type" label="类型" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="(typeTagType(row.type)) as TagType" size="small">{{ typeLabel(row.type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="generated_at" label="生成时间" width="170">
            <template #default="{ row }">{{ formatTime(row.generated_at) }}</template>
          </el-table-column>
          <el-table-column prop="archived_at" label="归档时间" width="170">
            <template #default="{ row }">{{ formatTime(row.archived_at) }}</template>
          </el-table-column>
          <el-table-column prop="file_size" label="文件大小" width="100" align="center">
            <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right" align="center">
            <template #default="{ row }">
              <el-button type="primary" plain @click="viewArchive(row)">查看</el-button>
              <el-button size="small" plain @click="downloadArchive(row)">下载</el-button>
              <el-button type="danger" plain @click="deleteArchive(row)">删除</el-button>
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
            @change="loadArchive"
          />
        </div>
      </div>
    </div>

    <!-- Archive Detail Dialog -->
    <el-dialog
      v-model="detailVisible"
      title="归档详情"
      width="600px"
      destroy-on-close
    >
      <el-descriptions v-if="archiveDetail" :column="2" border size="small">
        <el-descriptions-item label="报告名" :span="2">{{ archiveDetail.title || '-' }}</el-descriptions-item>
        <el-descriptions-item label="类型">
          <el-tag :type="(typeTagType(archiveDetail.type)) as TagType" size="small">{{ typeLabel(archiveDetail.type) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="文件大小">{{ formatSize(archiveDetail.file_size) }}</el-descriptions-item>
        <el-descriptions-item label="生成时间" :span="2">{{ formatTime(archiveDetail.generated_at) }}</el-descriptions-item>
        <el-descriptions-item label="归档时间" :span="2">{{ formatTime(archiveDetail.archived_at) }}</el-descriptions-item>
        <el-descriptions-item label="输出格式">{{ archiveDetail.format || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建人">{{ archiveDetail.created_by || '-' }}</el-descriptions-item>
        <el-descriptions-item v-if="archiveDetail.description" label="描述" :span="2">
          {{ archiveDetail.description }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="downloadArchive(archiveDetail)">下载</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, RefreshLeft } from '@element-plus/icons-vue'
import { reportService } from '@/shared/api'

// ── State ──────────────────────────────────────────────────────────
const loading = ref(false)
const archiveList = ref<any[]>([])
const detailVisible = ref(false)
const archiveDetail = ref<any>(null)

const filters = reactive({
  keyword: '',
  type: '',
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
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds())
}

function formatSize(bytes: number | null | undefined): string {
  if (!bytes && bytes !== 0) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}

function typeLabel(t: string): string {
  const map: Record<string, string> = {
    inspection: '巡检报告', anomaly: '异常报告', automation: '自动化报告',
    asset: '资产报告', compliance: '合规报告',
  }
  return map[t] || t || '-'
}

function typeTagType(t: string): TagType {
  const map: Record<string, string> = {
    inspection: 'primary', anomaly: 'danger', automation: 'warning', asset: 'success', compliance: 'info',
  }
  return (map[t] || 'info') as TagType
}

// ── Data Loading ───────────────────────────────────────────────────
async function loadArchive() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.type) params.type = filters.type

    const { data } = await reportService.listArchive(params)
    if (data.code === 0) {
      archiveList.value = data.data?.items || data.data?.list || []
      pagination.total = data.data?.total || 0
    }
  } catch (err: any) {
    ElMessage.error(err.message || '加载归档列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  loadArchive()
}

function resetFilters() {
  filters.keyword = ''
  filters.type = ''
  pagination.page = 1
  loadArchive()
}

// ── Actions ────────────────────────────────────────────────────────
async function viewArchive(row: any) {
  try {
    const { data } = await reportService.getArchiveDetail(row.id)
    if (data.code === 0) {
      archiveDetail.value = data.data || row
    } else {
      archiveDetail.value = row
    }
  } catch {
    archiveDetail.value = row
  }
  detailVisible.value = true
}

async function downloadArchive(row: any) {
  try {
    const { data } = await reportService.download(row.id)
    if (data instanceof Blob) {
      const url = URL.createObjectURL(data)
      const link = document.createElement('a')
      link.href = url
      const ext = row.format || 'pdf'
      link.download = row.title || 'report' + '.' + ext
      link.click()
      URL.revokeObjectURL(url)
      ElMessage.success('下载成功')
    }
  } catch (err: any) {
    ElMessage.error(err.message || '下载失败')
  }
}

async function deleteArchive(row: any) {
  try {
    await ElMessageBox.confirm(
      '确认删除归档报表「' + row.title + '」？此操作不可恢复。',
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
    // Re-use download endpoint pattern; use archive detail delete via API
    const { data } = await reportService.getArchiveDetail(row.id)
    // The API may support DELETE on archive detail
    const { data: delData } = await reportService.listArchive({ id: row.id, action: 'delete' })
    if (delData?.code === 0) {
      ElMessage.success('归档已删除')
      loadArchive()
    }
  } catch (err: any) {
    // If the above approach fails, try via task delete
    try {
      const client = (await import('@/shared/api/client')).default
      const { API } = await import('@/shared/api/routes')
      const { data } = await client.delete(API.REPORT.ARCHIVE_DETAIL(row.id))
      if (data.code === 0) {
        ElMessage.success('归档已删除')
        loadArchive()
      } else {
        ElMessage.error(data.message || '删除失败')
      }
    } catch {
      ElMessage.error('删除失败')
    }
  }
}

// ── Lifecycle ──────────────────────────────────────────────────────
onMounted(() => {
  loadArchive()
})
</script>

<style scoped>
.report-archive-page {
  padding: var(--autops-space-xl);
}

.main-card {
  border-radius: var(--autops-radius-md);
}
.filter-form {
  margin-bottom: var(--autops-space-lg);
  padding-bottom: 16px;
  border-bottom: 1px solid var(--autops-bg-4);
}

.filter-form :deep(.el-form-item) {
  margin-bottom: var(--autops-space-md);
}

.archive-table {
  width: 100%;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--autops-space-lg);
}
</style>
