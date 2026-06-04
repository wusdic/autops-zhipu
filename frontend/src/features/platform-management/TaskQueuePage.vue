<template>
  <div class="page-container">
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">任务队列</div>
        <div class="autops-page-desc">管理后台异步任务的执行状态</div>
      </div>
      <div class="header-actions">
        <el-button @click="loadTasks" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <!-- ── Filters ──────────────────────────────────────── -->
    <div class="filter-bar">
      <el-input
        v-model="keyword"
        placeholder="搜索任务名..."
        clearable
        prefix-icon="Search"
        style="width: 220px"
        @keyup.enter="loadTasks"
      />
      <el-select v-model="filterStatus" placeholder="任务状态" clearable style="width: 130px">
        <el-option label="排队中" value="queued" />
        <el-option label="执行中" value="running" />
        <el-option label="已完成" value="completed" />
        <el-option label="失败" value="failed" />
        <el-option label="已取消" value="cancelled" />
      </el-select>
      <el-select v-model="filterType" placeholder="任务类型" clearable style="width: 130px">
        <el-option label="资产采集" value="collection" />
        <el-option label="数据导入" value="import" />
        <el-option label="数据导出" value="export" />
        <el-option label="备份" value="backup" />
        <el-option label="报告生成" value="report" />
        <el-option label="系统任务" value="system" />
      </el-select>
      <el-button type="primary" @click="loadTasks">查询</el-button>
    </div>

    <!-- ── Summary Cards ─────────────────────────────────── -->
    <el-row :gutter="16" class="summary-row">
      <el-col :span="6" v-for="card in summaryCards" :key="card.label">
        <div class="summary-card" :style="{ borderLeftColor: card.color }">
          <div class="summary-value" :style="{ color: card.color }">{{ card.value }}</div>
          <div class="summary-label">{{ card.label }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- ── Table ────────────────────────────────────────── -->
    <el-table stripe
 :data="tasks"
 v-loading="loading"border
 row-key="id"
 empty-text="暂无任务"
 style="width: 100%"
 >
      <el-table-column prop="name" label="任务名" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="task-name">{{ row.name || row.description }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="task_type" label="类型" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="typeTagMap[row.task_type] ?? 'info'">
            {{ typeLabelMap[row.task_type] ?? row.task_type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag
            :type="statusTagMap[row.status] ?? 'info'"
            size="small"
            effect="dark"
          >
            <el-icon
              v-if="row.status === 'running'"
              class="is-loading"
              style="margin-right: 4px"
            ><Loading /></el-icon>
            {{ statusLabelMap[row.status] ?? row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="progress" label="进度" width="150">
        <template #default="{ row }">
          <el-progress
            v-if="row.status === 'running'"
            :percentage="row.progress ?? 0"
            :stroke-width="14"
            :format="(p: number) => `${p}%`"
          />
          <span v-else class="text-secondary">
            {{ row.status === 'completed' ? '100%' : '-' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="80" align="center">
        <template #default="{ row }">
          <el-tag
            v-if="row.priority !== undefined"
            size="small"
            :type="{ high: 'danger', medium: 'warning', low: 'info' }[row.priority] ?? 'info'"
          >
            {{ { high: '高', medium: '中', low: '低' }[row.priority] ?? row.priority }}
          </el-tag>
          <span v-else class="text-secondary">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="worker" label="执行者" width="110" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="text-secondary">{{ row.worker || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">
          <span class="text-secondary">{{ formatTime(row.created_at) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="started_at" label="开始时间" width="170">
        <template #default="{ row }">
          <span class="text-secondary">{{ formatTime(row.started_at) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="retries" label="重试" width="60" align="center">
        <template #default="{ row }">
          <span>{{ row.retries ?? 0 }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right" align="center">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'failed'"
            plain
            type="warning"
            size="small"
            @click="retryTask(row)"
          >
            重试
          </el-button>
          <el-button
            v-if="row.status === 'queued' || row.status === 'running'"
            plain
            type="danger"
            size="small"
            @click="cancelTask(row)"
          >
            取消
          </el-button>
          <el-button
            plain type="primary"
            size="small"
            @click="viewDetail(row)"
          >
            详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadTasks"
        @size-change="loadTasks"
      />
    </div>

    <!-- ── Detail Dialog ─────────────────────────────────── -->
    <el-dialog
      v-model="detailVisible"
      :title="`任务详情 - ${detailTask?.name ?? ''}`"
      width="600px"
      destroy-on-close
    >
      <el-descriptions :column="2" border size="small" v-if="detailTask">
        <el-descriptions-item label="任务ID">{{ detailTask.id }}</el-descriptions-item>
        <el-descriptions-item label="任务名">{{ detailTask.name }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ detailTask.task_type }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ detailTask.status }}</el-descriptions-item>
        <el-descriptions-item label="优先级">{{ detailTask.priority ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="执行者">{{ detailTask.worker ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="重试次数">{{ detailTask.retries ?? 0 }}</el-descriptions-item>
        <el-descriptions-item label="进度">{{ detailTask.progress ?? 0 }}%</el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">{{ formatTime(detailTask.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ formatTime(detailTask.started_at) }}</el-descriptions-item>
        <el-descriptions-item label="完成时间">{{ formatTime(detailTask.finished_at) }}</el-descriptions-item>
        <el-descriptions-item label="错误信息" :span="2">
          <span class="text-danger">{{ detailTask.error || '-' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="参数" :span="2">
          <pre class="json-pre">{{ formatJson(detailTask.params) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Loading } from '@element-plus/icons-vue'
import { platformService } from '@/shared/api'

// ── Maps ─────────────────────────────────────────────────
const typeLabelMap: Record<string, string> = {
  collection: '资产采集',
  import: '数据导入',
  export: '数据导出',
  backup: '备份',
  report: '报告生成',
  system: '系统任务',
}
const typeTagMap: Record<string, string> = {
  collection: '',
  import: 'success',
  export: 'warning',
  backup: 'primary',
  report: '',
  system: 'info',
}
const statusLabelMap: Record<string, string> = {
  queued: '排队中',
  running: '执行中',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消',
}
const statusTagMap: Record<string, string> = {
  queued: 'info',
  running: 'warning',
  completed: 'success',
  failed: 'danger',
  cancelled: 'info',
}

// ── State ────────────────────────────────────────────────
const loading = ref(false)
const tasks = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const keyword = ref('')
const filterStatus = ref('')
const filterType = ref('')

const detailVisible = ref(false)
const detailTask = ref<any>(null)

// ── Computed ─────────────────────────────────────────────
const summaryCards = computed(() => [
  { label: '排队中', value: tasks.value.filter((t) => t.status === 'queued').length, color: '#86909c' },
  { label: '执行中', value: tasks.value.filter((t) => t.status === 'running').length, color: '#ff7d00' },
  { label: '已完成', value: tasks.value.filter((t) => t.status === 'completed').length, color: '#00b42a' },
  { label: '失败', value: tasks.value.filter((t) => t.status === 'failed').length, color: '#f53f3f' },
])

// ── Helpers ──────────────────────────────────────────────
function formatTime(val: string | undefined): string {
  if (!val) return '-'
  try {
    return new Date(val).toLocaleString('zh-CN')
  } catch {
    return val
  }
}

function formatJson(obj: any): string {
  if (!obj) return '-'
  try {
    return typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2)
  } catch {
    return '-'
  }
}

// ── Data Loading ─────────────────────────────────────────
async function loadTasks() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize.value,
    }
    if (keyword.value) params.keyword = keyword.value
    if (filterStatus.value) params.status = filterStatus.value
    if (filterType.value) params.task_type = filterType.value

    const res = await platformService.taskQueue(params)
    const data = res.data?.data ?? res.data
    if (Array.isArray(data)) {
      tasks.value = data
      total.value = data.length
    } else {
      tasks.value = data?.items ?? data?.list ?? []
      total.value = data?.total ?? tasks.value.length
    }
  } catch (err: any) {
    ElMessage.error(err.message || '加载任务列表失败')
  } finally {
    loading.value = false
  }
}

// ── Actions ──────────────────────────────────────────────
async function retryTask(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定重试任务「${row.name || row.id}」吗？`,
      '重试确认',
      { confirmButtonText: '重试', cancelButtonText: '取消', type: 'warning' },
    )
    // Trigger retry via API — re-posting with same params
    await platformService.taskQueue({ action: 'retry', task_id: row.id })
    ElMessage.success('任务已重新提交')
    loadTasks()
  } catch {
    // cancelled
  }
}

async function cancelTask(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定取消任务「${row.name || row.id}」吗？`,
      '取消确认',
      { confirmButtonText: '取消任务', cancelButtonText: '返回', type: 'warning' },
    )
    await platformService.taskQueue({ action: 'cancel', task_id: row.id })
    ElMessage.success('任务已取消')
    loadTasks()
  } catch {
    // cancelled
  }
}

function viewDetail(row: any) {
  detailTask.value = row
  detailVisible.value = true
}

// ── Init ─────────────────────────────────────────────────
onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.autops-page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.summary-row {
  margin-bottom: 16px;
}
.summary-card {
  background: #fff;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  padding: 16px;
  border-left: 3px solid #86909c;
}
.summary-value {
  font-size: 28px;
  font-weight: 700;
}
.summary-label {
  font-size: 13px;
  color: #86909c;
  margin-top: 4px;
}

.task-name {
  font-weight: 500;
}
.text-secondary {
  color: #86909c;
  font-size: 12px;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.json-pre {
  font-size: 12px;
  background: #f7f8fa;
  padding: 8px;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}
</style>
