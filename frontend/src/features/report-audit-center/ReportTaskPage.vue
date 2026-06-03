<template>
  <div class="report-task-page">
    <!-- Page Header -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">报表任务</div>
        <div class="autops-page-subtitle">报表生成任务队列、进度跟踪与日志</div>
      </div>
    </div>

    <!-- Main Card -->
    <div class="autops-card main-card">
      <div class="autops-card-header">
        <span class="autops-card-title">任务列表</span>
        <div class="card-header__actions">
          <el-button :icon="Refresh" circle size="small" @click="loadTasks" />
        </div>
      </div>
      <div class="autops-card-body">
        <!-- Filters -->
        <el-form :inline="true" class="autops-toolbar filter-form" @submit.prevent="handleSearch">
          <el-form-item label="状态">
            <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 140px">
              <el-option label="等待中" value="pending" />
              <el-option label="生成中" value="generating" />
              <el-option label="已完成" value="completed" />
              <el-option label="失败" value="failed" />
            </el-select>
          </el-form-item>
          <el-form-item label="关键词">
            <el-input
              v-model="filters.keyword"
              placeholder="搜索报告名"
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

        <!-- Table -->
        <el-table
          :data="tasks"
          v-loading="loading"
          stripe
          border
          row-key="id"
          class="task-table"
        >
          <el-table-column prop="title" label="报告名" min-width="180" show-overflow-tooltip />
          <el-table-column prop="template_name" label="模板" min-width="120" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="progress" label="进度" width="150">
            <template #default="{ row }">
              <el-progress
                :percentage="row.progress || 0"
                :status="progressStatus(row.status)"
                :stroke-width="14"
                :text-inside="true"
              />
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="170">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column prop="completed_at" label="完成时间" width="170">
            <template #default="{ row }">{{ formatTime(row.completed_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right" align="center">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 'completed'"
                size="small"
                type="primary"
                link
                @click="previewTask(row)"
              >预览</el-button>
              <el-button
                v-if="row.status === 'completed'"
                size="small"
                link
                @click="downloadTask(row)"
              >下载</el-button>
              <el-button
                v-if="row.status === 'failed'"
                size="small"
                type="warning"
                link
                @click="retryTask(row)"
              >重试</el-button>
              <el-button
                size="small"
                type="info"
                link
                @click="viewDetail(row)"
              >详情</el-button>
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
            @change="loadTasks"
          />
        </div>
      </div>
    </div>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="detailVisible"
      title="任务详情"
      width="560px"
      destroy-on-close
    >
      <el-descriptions v-if="taskDetail" :column="2" border size="small">
        <el-descriptions-item label="报告名" :span="2">{{ taskDetail.title || '-' }}</el-descriptions-item>
        <el-descriptions-item label="模板">{{ taskDetail.template_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(taskDetail.status)" size="small">{{ statusLabel(taskDetail.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="进度">
          <el-progress
            :percentage="taskDetail.progress || 0"
            :stroke-width="14"
            :text-inside="true"
            style="max-width: 200px"
          />
        </el-descriptions-item>
        <el-descriptions-item label="输出格式">{{ taskDetail.format || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">{{ formatTime(taskDetail.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="完成时间" :span="2">{{ formatTime(taskDetail.completed_at) }}</el-descriptions-item>
        <el-descriptions-item v-if="taskDetail.error_message" label="错误信息" :span="2">
          <span style="color: #f56c6c">{{ taskDetail.error_message }}</span>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, RefreshLeft } from '@element-plus/icons-vue'
import { reportService } from '@/shared/api'

const router = useRouter()

// ── State ──────────────────────────────────────────────────────────
const loading = ref(false)
const tasks = ref<any[]>([])
const detailVisible = ref(false)
const taskDetail = ref<any>(null)

const filters = reactive({
  status: '',
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

function statusType(s: string): string {
  const map: Record<string, string> = {
    pending: 'info', generating: 'warning', completed: 'success', failed: 'danger',
  }
  return map[s] || 'info'
}

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    pending: '等待中', generating: '生成中', completed: '已完成', failed: '失败',
  }
  return map[s] || s || '-'
}

function progressStatus(status: string): '' | 'success' | 'exception' | undefined {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return undefined
}

// ── Data Loading ───────────────────────────────────────────────────
async function loadTasks() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.status) params.status = filters.status
    if (filters.keyword) params.keyword = filters.keyword

    const { data } = await reportService.listTasks(params)
    if (data.code === 0) {
      tasks.value = data.data?.items || data.data?.list || []
      pagination.total = data.data?.total || 0
    }
  } catch (err: any) {
    ElMessage.error(err.message || '加载任务列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  loadTasks()
}

function resetFilters() {
  filters.status = ''
  filters.keyword = ''
  pagination.page = 1
  loadTasks()
}

// ── Actions ────────────────────────────────────────────────────────
async function viewDetail(row: any) {
  try {
    const { data } = await reportService.getTask(row.id)
    if (data.code === 0) {
      taskDetail.value = data.data || row
    } else {
      taskDetail.value = row
    }
  } catch {
    taskDetail.value = row
  }
  detailVisible.value = true
}

function previewTask(row: any) {
  router.push({ name: 'report-preview', query: { taskId: row.id } })
}

async function downloadTask(row: any) {
  try {
    const { data } = await reportService.download(row.id)
    if (data instanceof Blob) {
      const url = URL.createObjectURL(data)
      const link = document.createElement('a')
      link.href = url
      const ext = row.format || 'pdf'
      link.download = `${row.title || 'report'}.${ext}`
      link.click()
      URL.revokeObjectURL(url)
      ElMessage.success('下载成功')
    }
  } catch (err: any) {
    ElMessage.error(err.message || '下载失败')
  }
}

async function retryTask(row: any) {
  try {
    await ElMessageBox.confirm('确认重新生成此报表？', '重试确认', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'info',
    })
    const payload: Record<string, any> = {
      template_id: row.template_id,
      title: row.title,
    }
    const { data } = await reportService.generate(payload)
    if (data.code === 0) {
      ElMessage.success('重试任务已提交')
      loadTasks()
    } else {
      ElMessage.error(data.message || '重试失败')
    }
  } catch {
    // cancelled
  }
}

// ── Auto Refresh ───────────────────────────────────────────────────
let refreshTimer: ReturnType<typeof setInterval> | null = null

// ── Lifecycle ──────────────────────────────────────────────────────
onMounted(() => {
  loadTasks()
  // Auto-refresh every 10s for active tasks
  refreshTimer = setInterval(() => {
    const hasActive = tasks.value.some(t => t.status === 'pending' || t.status === 'generating')
    if (hasActive) loadTasks()
  }, 10_000)
})

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.report-task-page {
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

.task-table {
  width: 100%;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
