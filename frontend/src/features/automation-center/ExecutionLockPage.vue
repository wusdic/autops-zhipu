<template>
  <div class="autops-page-container">
    <PageHeader title="执行锁管理" desc="查看和管理自动化执行锁定记录" />

    <!-- 搜索筛选区 -->
    <el-card class="filter-card" shadow="never">
      <el-form :model="queryParams" inline @submit.prevent="handleSearch">
        <el-form-item label="执行ID">
          <el-input
            v-model="queryParams.execution_id"
            placeholder="输入执行ID"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="目标资源">
          <el-input
            v-model="queryParams.target_id"
            placeholder="资源名称"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="全部" clearable style="width: 140px">
            <el-option label="待执行" value="pending" />
            <el-option label="已完成" value="completed" />
            <el-option label="运行中" value="running" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计概览 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover" class="autops-metric-card">
          <div class="stat-content">
            <div class="stat-label">执行总数</div>
            <div class="stat-value primary">{{ total }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="autops-metric-card">
          <div class="stat-content">
            <div class="stat-label">已完成</div>
            <div class="stat-value success">{{ completedCount }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="autops-metric-card">
          <div class="stat-content">
            <div class="stat-label">运行中/待执行</div>
            <div class="stat-value warning">{{ runningCount }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="autops-metric-card">
          <div class="stat-content">
            <div class="stat-label">失败数</div>
            <div class="stat-value danger">{{ failedCount }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 执行锁列表表格 -->
    <el-card class="table-card" shadow="never">
      <template #header>
        <div class="autops-card-header">
          <span>执行记录列表</span>
          <el-button type="danger" plain :icon="Unlock" :disabled="!selectedRows.length" @click="handleBatchRelease">
            批量释放 ({{ selectedRows.length }})
          </el-button>
        </div>
      </template>

      <el-table stripe
        v-loading="loading"
        :data="lockList"
        border
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" align="center" />

        <el-table-column prop="id" label="执行ID" width="160" align="center">
          <template #default="{ row }">
            <el-tooltip :content="row.id || ''" placement="top">
              <el-button type="primary" plain @click="handleViewExecution(row)">
                {{ truncateLockId(row.id) }}
              </el-button>
            </el-tooltip>
          </template>
        </el-table-column>

        <el-table-column prop="execution_type" label="执行类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="(execTypeTagType(row.execution_type)) as TagType">
              {{ execTypeLabel(row.execution_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="target_id" label="目标资源" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="resource-cell">
              <el-icon><Lock /></el-icon>
              <span>{{ row.target_id || '-' }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="trigger_source" label="触发来源" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ triggerLabel(row.trigger_source) }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="(statusTagType(row.status)) as TagType" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="risk_level" label="风险等级" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.risk_level === 'high' ? 'danger' : row.risk_level === 'medium' ? 'warning' : 'info'" size="small">
              {{ riskLabel(row.risk_level) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180" align="center">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column prop="updated_at" label="更新时间" width="180" align="center">
          <template #default="{ row }">
            {{ formatTime(row.updated_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" plain size="small" @click="handleViewDetail(row)">详情</el-button>
            <el-popconfirm
              title="确定释放该锁吗？释放后相关执行将被中断。"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="handleRelease(row)"
            >
              <template #reference>
                <el-button type="danger" plain size="small">释放</el-button>
              </template>
            </el-popconfirm>
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
          @size-change="fetchLockList"
          @current-change="fetchLockList"
        />
      </div>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="执行详情" width="600px" destroy-on-close>
      <el-descriptions :column="2" border v-if="currentLock">
        <el-descriptions-item label="执行ID" :span="2">{{ currentLock.id }}</el-descriptions-item>
        <el-descriptions-item label="执行类型">
          <el-tag size="small">{{ execTypeLabel(currentLock.execution_type) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="(statusTagType(currentLock.status)) as TagType" size="small">{{ statusLabel(currentLock.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="目标资源" :span="2">{{ currentLock.target_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="触发来源">{{ triggerLabel(currentLock.trigger_source) }}</el-descriptions-item>
        <el-descriptions-item label="风险等级">{{ riskLabel(currentLock.risk_level) }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(currentLock.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatTime(currentLock.updated_at) }}</el-descriptions-item>
        <el-descriptions-item v-if="currentLock.started_at" label="开始时间">{{ formatTime(currentLock.started_at) }}</el-descriptions-item>
        <el-descriptions-item v-if="currentLock.completed_at" label="完成时间">{{ formatTime(currentLock.completed_at) }}</el-descriptions-item>
        <el-descriptions-item v-if="currentLock.error_message" label="错误信息" :span="2">{{ currentLock.error_message }}</el-descriptions-item>
        <el-descriptions-item v-if="currentLock.result" label="执行结果" :span="2">{{ currentLock.result }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { Search, Refresh, Unlock, Lock } from '@element-plus/icons-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import { ElMessage } from 'element-plus'
import { API } from '@/shared/api/routes'
import { taskStatusLabel, taskStatusTag, riskLabel as riskLabelFn } from '@/shared/utils/labels'
import client from '@/shared/api/client'
import type { AxiosResponse } from 'axios'

// ---------- 类型定义 ----------
interface LockEntry {
  id: string
  execution_type?: string
  target_id?: string
  asset_ids?: string
  parameters?: string
  status?: string
  trigger_source?: string
  trigger_source_id?: string
  policy_execution_id?: string
  is_dry_run?: boolean
  risk_level?: string
  approved_by?: string
  approved_at?: string
  started_at?: string
  completed_at?: string
  result?: string
  error_message?: string
  created_at?: string
  updated_at?: string
  [key: string]: unknown
}

interface QueryParams {
  execution_id: string
  target_id: string
  status: string
  page: number
  pageSize: number
}

// ---------- 状态 ----------
const loading = ref(false)
const lockList = ref<LockEntry[]>([])
const total = ref(0)
const selectedRows = ref<LockEntry[]>([])
const detailVisible = ref(false)
const currentLock = ref<LockEntry | null>(null)
let refreshTimer: ReturnType<typeof setInterval> | null = null

const queryParams = reactive<QueryParams>({
  execution_id: '',
  target_id: '',
  status: '',
  page: 1,
  pageSize: 20,
})

// ---------- 计算属性 ----------
const completedCount = computed(() => lockList.value.filter(r => r.status === 'completed').length)
const runningCount = computed(() => lockList.value.filter(r => r.status === 'running' || r.status === 'pending').length)
const failedCount = computed(() => lockList.value.filter(r => r.status === 'failed').length)

// ---------- 工具函数 ----------
function truncateLockId(id: string | undefined): string {
  if (!id) return '-'
  var s = String(id)
  return s.length > 16 ? s.slice(0, 8) + '...' + s.slice(-4) : s
}

const formatTime = (ts?: string): string => {
  if (!ts) return '-'
  var d = new Date(ts)
  if (isNaN(d.getTime())) return ts
  return d.toLocaleString('zh-CN', { hour12: false })
}

function execTypeLabel(t: string | undefined): string {
  var map: Record<string, string> = { manual: '手动', script: '脚本', playbook: 'Playbook', policy: '策略' }
  return map[t || ''] || t || '-'
}

function execTypeTagType(t: string | undefined): TagType {
  var map: Record<string, string> = { manual: 'primary', script: 'success', playbook: 'warning', policy: 'info' }
  return (map[t || ''] || 'info') as TagType
}

function triggerLabel(t: string | undefined): string {
  var map: Record<string, string> = { manual: '手动', policy: '策略', schedule: '定时', alert: '告警', api: 'API' }
  return map[t || ''] || t || '-'
}

const statusLabel = (s: string | undefined): string => taskStatusLabel(s || '')
const statusTagType = (s: string | undefined): TagType => taskStatusTag(s || '') as TagType
const riskLabel = (r: string | undefined): string => riskLabelFn(r || '')

// ---------- 数据请求 ----------
var buildParams = (): Record<string, unknown> => {
  var params: Record<string, unknown> = {
    page: queryParams.page,
    page_size: queryParams.pageSize,
  }
  if (queryParams.execution_id) params.id = queryParams.execution_id
  if (queryParams.target_id) params.target_id = queryParams.target_id
  if (queryParams.status) params.status = queryParams.status
  return params
}

var fetchLockList = async () => {
  loading.value = true
  try {
    var res: AxiosResponse = await client.get(API.EXECUTIONS, { params: buildParams() })
    var rawData = res.data
    var payload = rawData?.data ?? rawData
    // API returns items[] in data.data
    lockList.value = payload?.items ?? payload?.results ?? payload?.list ?? []
    total.value = payload?.total ?? payload?.count ?? 0
  } catch (err: unknown) {
    var msg = err instanceof Error ? err.message : '获取执行列表失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

// ---------- 事件处理 ----------
var handleSearch = () => {
  queryParams.page = 1
  fetchLockList()
}

var handleReset = () => {
  queryParams.execution_id = ''
  queryParams.target_id = ''
  queryParams.status = ''
  queryParams.page = 1
  queryParams.pageSize = 20
  fetchLockList()
}

var handleSelectionChange = (rows: LockEntry[]) => {
  selectedRows.value = rows
}

var handleViewExecution = (row: any) => {
}

var handleViewDetail = (row: any) => {
  currentLock.value = row
  detailVisible.value = true
}

var handleRelease = async (row: any) => {
  try {
    await client.post(API.EXECUTION_CANCEL(row.id))
    ElMessage.success('执行已取消/释放')
    fetchLockList()
  } catch {
    ElMessage.error('操作失败')
  }
}

var handleBatchRelease = async () => {
  if (!selectedRows.value.length) return
  try {
    for (var i = 0; i < selectedRows.value.length; i++) {
      await client.post(API.EXECUTION_CANCEL(selectedRows.value[i].id))
    }
    ElMessage.success('成功释放 ' + selectedRows.value.length + ' 个执行')
    selectedRows.value = []
    fetchLockList()
  } catch {
    ElMessage.error('批量释放失败')
  }
}

// ---------- 生命周期 ----------
onMounted(() => {
  fetchLockList()
  refreshTimer = setInterval(fetchLockList, 30000)
})

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped lang="scss">
.execution-lock-page {
  padding: var(--autops-space-lg);

  .filter-card {
    margin-bottom: var(--autops-space-lg);
  }

  .stat-row {
    margin-bottom: var(--autops-space-lg);
  }

  .table-card {
    
    .resource-cell {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .pagination-wrapper {
      display: flex;
      justify-content: flex-end;
      margin-top: var(--autops-space-lg);
    }
  }

  .text-danger {
    color: var(--autops-danger);
    font-weight: 600;
  }
}
</style>
