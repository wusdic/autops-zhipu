<template>
  <div class="rollback-center-page">
    <!-- 搜索筛选区 -->
    <el-card class="filter-card" shadow="never">
      <el-form :model="queryParams" inline @submit.prevent="handleSearch">
        <el-form-item label="执行名">
          <el-input
            v-model="queryParams.name"
            placeholder="搜索执行名称"
            clearable
            style="width: 220px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="原始状态">
          <el-select v-model="queryParams.original_status" placeholder="全部状态" clearable style="width: 140px">
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
            <el-option label="部分成功" value="partial" />
          </el-select>
        </el-form-item>

        <el-form-item label="可回滚">
          <el-select v-model="queryParams.rollback_available" placeholder="全部" clearable style="width: 120px">
            <el-option label="可回滚" value="true" />
            <el-option label="不可回滚" value="false" />
          </el-select>
        </el-form-item>

        <el-form-item label="时间范围">
          <el-date-picker
            v-model="queryParams.dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 380px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 概览统计 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">总执行数</div>
            <div class="stat-value">{{ total }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">可回滚</div>
            <div class="stat-value success">{{ rollbackAvailableCount }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">已回滚</div>
            <div class="stat-value warning">{{ rolledBackCount }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">回滚中</div>
            <div class="stat-value primary">{{ rollingBackCount }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 回滚列表表格 -->
    <el-card class="table-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>回滚中心</span>
          <el-button type="success" :icon="Refresh" @click="fetchRollbackList">刷新</el-button>
        </div>
      </template>

      <el-table stripe
 v-loading="loading"
 :data="executionList"border
 style="width: 100%"
 row-key="id"
 :row-class-name="rowClassName"
 >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-content">
              <el-descriptions :column="3" border size="small">
                <el-descriptions-item label="执行ID">{{ row.id }}</el-descriptions-item>
                <el-descriptions-item label="创建者">{{ row.created_by || '-' }}</el-descriptions-item>
                <el-descriptions-item label=" playbook">{{ row.playbook?.name || '-' }}</el-descriptions-item>
                <el-descriptions-item label="目标主机" :span="3">
                  <el-tag
                    v-for="(host, idx) in (row.targets || [])"
                    :key="idx"
                    size="small"
                    style="margin-right: 4px"
                  >
                    {{ host }}
                  </el-tag>
                  <span v-if="!row.targets?.length">-</span>
                </el-descriptions-item>
                <el-descriptions-item v-if="row.rollback_info" label="回滚信息" :span="3">
                  {{ row.rollback_info }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="name" label="执行名" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="execution-name">{{ row.name || row.playbook?.name || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="original_status" label="原始状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="rollback_status" label="回滚状态" width="140" align="center">
          <template #default="{ row }">
            <template v-if="row.rollback_status">
              <el-tag :type="rollbackStatusType(row.rollback_status)" size="small" effect="dark">
                {{ rollbackStatusLabel(row.rollback_status) }}
              </el-tag>
            </template>
            <template v-else>
              <span class="text-muted">未回滚</span>
            </template>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="执行时间" width="170" align="center">
          <template #default="{ row }">
            {{ formatTime(row.created_at || row.started_at) }}
          </template>
        </el-table-column>

        <el-table-column prop="rollback_at" label="回滚时间" width="170" align="center">
          <template #default="{ row }">
            {{ row.rollback_at ? formatTime(row.rollback_at) : '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="duration" label="执行耗时" width="110" align="center">
          <template #default="{ row }">
            {{ row.duration ? `${row.duration}s` : '-' }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click="handleViewDetail(row)"
            >
              详情
            </el-button>
            <el-button
              v-if="row.rollback_available && !row.rollback_status"
              type="warning"
              link
              size="small"
              @click="handleRollback(row)"
            >
              回滚
            </el-button>
            <el-button
              v-if="row.rollback_status === 'running'"
              type="danger"
              link
              size="small"
              @click="handleCancelRollback(row)"
            >
              取消
            </el-button>
            <el-button
              v-if="row.rollback_status === 'completed'"
              type="info"
              link
              size="small"
              @click="handleRollbackLog(row)"
            >
              日志
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="fetchRollbackList"
          @current-change="fetchRollbackList"
        />
      </div>
    </el-card>

    <!-- 回滚确认弹窗 -->
    <el-dialog v-model="rollbackConfirmVisible" title="回滚确认" width="600px" destroy-on-close>
      <el-alert
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      >
        <template #title>
          确定要回滚执行 <strong>{{ rollbackTarget?.name }}</strong> 吗？此操作将尝试恢复到执行前的状态。
        </template>
      </el-alert>
      <el-form :model="rollbackForm" label-width="80px">
        <el-form-item label="回滚原因">
          <el-input
            v-model="rollbackForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入回滚原因（选填）"
          />
        </el-form-item>
        <el-form-item label="强制回滚">
          <el-switch v-model="rollbackForm.force" />
          <span class="form-tip">忽略部分检查强制执行回滚</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rollbackConfirmVisible = false">取消</el-button>
        <el-button type="warning" :loading="rollbackLoading" @click="confirmRollback">确认回滚</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="执行详情" width="780px" destroy-on-close>
      <el-descriptions v-if="currentExecution" :column="2" border>
        <el-descriptions-item label="执行名">{{ currentExecution.name }}</el-descriptions-item>
        <el-descriptions-item label="执行ID">{{ currentExecution.id }}</el-descriptions-item>
        <el-descriptions-item label="原始状态">
          <el-tag :type="statusTagType(currentExecution.status)" size="small">
            {{ statusLabel(currentExecution.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="回滚状态">
          <template v-if="currentExecution.rollback_status">
            <el-tag :type="rollbackStatusType(currentExecution.rollback_status)" size="small">
              {{ rollbackStatusLabel(currentExecution.rollback_status) }}
            </el-tag>
          </template>
          <span v-else class="text-muted">未回滚</span>
        </el-descriptions-item>
        <el-descriptions-item label="执行时间">{{ formatTime(currentExecution.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="回滚时间">{{ currentExecution.rollback_at ? formatTime(currentExecution.rollback_at) : '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建者">{{ currentExecution.created_by || '-' }}</el-descriptions-item>
        <el-descriptions-item label="耗时">{{ currentExecution.duration ? `${currentExecution.duration}s` : '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { API } from '@/shared/api/routes'
import client from '@/shared/api/client'
import type { AxiosResponse } from 'axios'

// ---------- 类型定义 ----------
interface ExecutionEntry {
  id: string | number
  name?: string
  status: string
  rollback_status?: string
  rollback_available?: boolean
  rollback_at?: string
  created_at?: string
  started_at?: string
  duration?: number
  created_by?: string
  playbook?: { name: string }
  targets?: string[]
  rollback_info?: string
  [key: string]: unknown
}

interface QueryParams {
  name: string
  original_status: string
  rollback_available: string
  dateRange: string[] | null
  page: number
  pageSize: number
}

// ---------- 状态 ----------
const loading = ref(false)
const executionList = ref<ExecutionEntry[]>([])
const total = ref(0)
const detailVisible = ref(false)
const currentExecution = ref<ExecutionEntry | null>(null)
const rollbackConfirmVisible = ref(false)
const rollbackLoading = ref(false)
const rollbackTarget = ref<ExecutionEntry | null>(null)

const rollbackForm = reactive({
  reason: '',
  force: false,
})

const queryParams = reactive<QueryParams>({
  name: '',
  original_status: '',
  rollback_available: '',
  dateRange: null,
  page: 1,
  pageSize: 20,
})

// ---------- 计算属性 ----------
const rollbackAvailableCount = computed(() => executionList.value.filter(e => e.rollback_available && !e.rollback_status).length)
const rolledBackCount = computed(() => executionList.value.filter(e => e.rollback_status === 'completed').length)
const rollingBackCount = computed(() => executionList.value.filter(e => e.rollback_status === 'running').length)

// ---------- 工具函数 ----------
const formatTime = (ts?: string): string => {
  if (!ts) return '-'
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ts
  return d.toLocaleString('zh-CN', { hour12: false })
}

const statusTagType = (status?: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    success: 'success',
    failed: 'danger',
    partial: 'warning',
    running: '',
    pending: 'info',
  }
  return map[status || ''] || 'info'
}

const statusLabel = (status?: string): string => {
  const map: Record<string, string> = {
    success: '成功',
    failed: '失败',
    partial: '部分成功',
    running: '运行中',
    pending: '待执行',
  }
  return map[status || ''] || status || '-'
}

const rollbackStatusType = (status?: string): 'success' | 'warning' | 'danger' | 'info' => {
  const map: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    completed: 'success',
    running: 'warning',
    failed: 'danger',
    cancelled: 'info',
  }
  return map[status || ''] || 'info'
}

const rollbackStatusLabel = (status?: string): string => {
  const map: Record<string, string> = {
    completed: '已回滚',
    running: '回滚中',
    failed: '回滚失败',
    cancelled: '已取消',
  }
  return map[status || ''] || status || '-'
}

const rowClassName = ({ row }: { row: ExecutionEntry }): string => {
  if (row.rollback_status === 'running') return 'row-rolling-back'
  if (row.rollback_status === 'completed') return 'row-rolled-back'
  return ''
}

// ---------- 数据请求 ----------
const buildParams = (): Record<string, unknown> => {
  const params: Record<string, unknown> = {
    page: queryParams.page,
    page_size: queryParams.pageSize,
    has_rollback: true,
  }
  if (queryParams.name) params.name = queryParams.name
  if (queryParams.original_status) params.status = queryParams.original_status
  if (queryParams.rollback_available) params.rollback_available = queryParams.rollback_available
  if (queryParams.dateRange && queryParams.dateRange.length === 2) {
    params.start_time = queryParams.dateRange[0]
    params.end_time = queryParams.dateRange[1]
  }
  return params
}

const fetchRollbackList = async () => {
  loading.value = true
  try {
    const res: AxiosResponse = await client.get(API.EXECUTIONS, { params: buildParams() })
    const data = res.data?.data ?? res.data
    executionList.value = data?.items ?? data?.results ?? data?.list ?? []
    total.value = data?.total ?? data?.count ?? 0
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '获取回滚列表失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

// ---------- 事件处理 ----------
const handleSearch = () => {
  queryParams.page = 1
  fetchRollbackList()
}

const handleReset = () => {
  queryParams.name = ''
  queryParams.original_status = ''
  queryParams.rollback_available = ''
  queryParams.dateRange = null
  queryParams.page = 1
  queryParams.pageSize = 20
  fetchRollbackList()
}

const handleViewDetail = (row: ExecutionEntry) => {
  currentExecution.value = row
  detailVisible.value = true
}

const handleRollback = (row: ExecutionEntry) => {
  rollbackTarget.value = row
  rollbackForm.reason = ''
  rollbackForm.force = false
  rollbackConfirmVisible.value = true
}

const confirmRollback = async () => {
  if (!rollbackTarget.value) return
  rollbackLoading.value = true
  try {
    const id = rollbackTarget.value.id
    await client.post(API.EXECUTION_ROLLBACK(id), {
      reason: rollbackForm.reason,
      force: rollbackForm.force,
    })
    ElMessage.success('回滚已启动')
    rollbackConfirmVisible.value = false
    fetchRollbackList()
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '回滚失败'
    ElMessage.error(msg)
  } finally {
    rollbackLoading.value = false
  }
}

const handleCancelRollback = async (row: ExecutionEntry) => {
  try {
    await ElMessageBox.confirm('确定取消回滚操作吗？', '取消确认', {
      type: 'warning',
    })
    await client.post(`${API.EXECUTIONS}${row.id}/cancel-rollback/`)
    ElMessage.success('回滚已取消')
    fetchRollbackList()
  } catch {
    // User cancelled
  }
}

const handleRollbackLog = (row: ExecutionEntry) => {
  // Could navigate to log page or open log dialog
  console.log('View rollback log for:', row.id)
}

// ---------- 生命周期 ----------
onMounted(() => {
  fetchRollbackList()
})
</script>

<style scoped lang="scss">
.rollback-center-page {
  padding: 16px;

  .filter-card {
    margin-bottom: 16px;
  }

  .stat-row {
    margin-bottom: 16px;

    
          &.primary { color: #165dff; }
        }
      }
    }
  }

  .table-card {
    
    .expand-content {
      padding: 12px 20px;
    }

    .pagination-wrapper {
      display: flex;
      justify-content: flex-end;
      margin-top: 16px;
    }
  }

  .execution-name {
    font-weight: 500;
  }

  .text-muted {
    color: #c9cdd4;
    font-size: 13px;
  }

  .form-tip {
    margin-left: 8px;
    color: #86909c;
    font-size: 12px;
  }

  :deep(.row-rolling-back) {
    background-color: #fdf6ec !important;
  }

  :deep(.row-rolled-back) {
    background-color: #f0f9eb !important;
  }
}
</style>
