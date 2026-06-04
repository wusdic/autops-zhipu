<template>
  <div class="execution-lock-page">
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

        <el-form-item label="锁定资源">
          <el-input
            v-model="queryParams.lock_resource"
            placeholder="资源名称"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="持有者">
          <el-input
            v-model="queryParams.owner"
            placeholder="持有者"
            clearable
            style="width: 180px"
            @keyup.enter="handleSearch"
          />
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
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">活跃锁总数</div>
            <div class="stat-value primary">{{ total }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">锁超时数</div>
            <div class="stat-value warning">{{ expiredCount }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">长时间持有</div>
            <div class="stat-value danger">{{ longHeldCount }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">正常运行</div>
            <div class="stat-value success">{{ total - expiredCount - longHeldCount }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 锁列表表格 -->
    <el-card class="table-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>执行锁列表</span>
          <el-button type="danger" plain :icon="Unlock" :disabled="!selectedRows.length" @click="handleBatchRelease">
            批量释放 ({{ selectedRows.length }})
          </el-button>
        </div>
      </template>

      <el-table stripe
 v-loading="loading"
 :data="lockList"border
 style="width: 100%"
 @selection-change="handleSelectionChange"
 >
        <el-table-column type="selection" width="50" align="center" />

        <el-table-column prop="id" label="执行ID" width="160" align="center">
          <template #default="{ row }">
            <el-tooltip :content="row.id || row.execution_id || ''" placement="top">
              <el-button type="primary" plain @click="handleViewExecution(row)">
                {{ truncateLockId(row.id || row.execution_id) }}
              </el-button>
            </el-tooltip>
          </template>
        </el-table-column>

        <el-table-column prop="lock_resource" label="锁定资源" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="resource-cell">
              <el-icon><Lock /></el-icon>
              <span>{{ row.lock_resource || row.resource }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="lock_type" label="锁类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.lock_type === 'exclusive' ? 'danger' : 'warning'">
              {{ row.lock_type === 'exclusive' ? '排他锁' : row.lock_type === 'shared' ? '共享锁' : row.lock_type || '-' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="locked_at" label="锁定时间" width="180" align="center">
          <template #default="{ row }">
            {{ formatTime(row.locked_at || row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column prop="duration" label="持有时长" width="120" align="center">
          <template #default="{ row }">
            <span :class="{ 'text-danger': isLongHeld(row) }">
              {{ calcDuration(row.locked_at || row.created_at) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="owner" label="持有者" width="150" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.owner || row.holder || row.created_by || '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              :type="isExpired(row) ? 'danger' : isLongHeld(row) ? 'warning' : 'success'"
              size="small"
            >
              {{ isExpired(row) ? '超时' : isLongHeld(row) ? '长时间' : '正常' }}
            </el-tag>
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
    <el-dialog v-model="detailVisible" title="锁详情" width="600px" destroy-on-close>
      <el-descriptions :column="2" border v-if="currentLock">
        <el-descriptions-item label="执行ID">{{ currentLock.id || currentLock.execution_id }}</el-descriptions-item>
        <el-descriptions-item label="锁类型">
          <el-tag size="small">{{ currentLock.lock_type || '-' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="锁定资源" :span="2">{{ currentLock.lock_resource || currentLock.resource }}</el-descriptions-item>
        <el-descriptions-item label="锁定时间">{{ formatTime(currentLock.locked_at || currentLock.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="持有时长">{{ calcDuration(currentLock.locked_at || currentLock.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="持有者">{{ currentLock.owner || currentLock.holder || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="isExpired(currentLock) ? 'danger' : 'success'" size="small">
            {{ isExpired(currentLock) ? '超时' : '正常' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item v-if="currentLock.description" label="描述" :span="2">
          {{ currentLock.description }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { Search, Refresh, Unlock, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { API } from '@/shared/api/routes'
import client from '@/shared/api/client'
import type { AxiosResponse } from 'axios'

// ---------- 类型定义 ----------
interface LockEntry {
  id: string | number
  execution_id?: string
  lock_resource?: string
  resource?: string
  lock_type?: string
  locked_at?: string
  created_at?: string
  owner?: string
  holder?: string
  created_by?: string
  description?: string
  ttl?: number
  [key: string]: unknown
}

interface QueryParams {
  execution_id: string
  lock_resource: string
  owner: string
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
  lock_resource: '',
  owner: '',
  page: 1,
  pageSize: 20,
})

// ---------- 计算属性 ----------
const expiredCount = computed(() => lockList.value.filter(isExpired).length)
const longHeldCount = computed(() => lockList.value.filter(isLongHeld).length)

// ---------- 工具函数 ----------
function truncateLockId(id: string | number | undefined): string {
  if (!id) return '-'
  var s = String(id)
  return s.length > 16 ? s.slice(0, 8) + '...' + s.slice(-4) : s
}

const formatTime = (ts?: string): string => {
  if (!ts) return '-'
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ts
  return d.toLocaleString('zh-CN', { hour12: false })
}

const calcDuration = (ts?: string): string => {
  if (!ts) return '-'
  const start = new Date(ts).getTime()
  if (isNaN(start)) return '-'
  const diff = Date.now() - start
  if (diff < 0) return '-'
  const hours = Math.floor(diff / 3600000)
  const minutes = Math.floor((diff % 3600000) / 60000)
  if (hours > 0) return `${hours}时${minutes}分`
  return `${minutes}分`
}

const isExpired = (row: LockEntry): boolean => {
  if (!row.ttl) return false
  const lockedAt = new Date(row.locked_at || row.created_at || '').getTime()
  return !isNaN(lockedAt) && Date.now() - lockedAt > row.ttl * 1000
}

const isLongHeld = (row: LockEntry): boolean => {
  const lockedAt = new Date(row.locked_at || row.created_at || '').getTime()
  return !isNaN(lockedAt) && Date.now() - lockedAt > 3600000 // > 1h
}

// ---------- 数据请求 ----------
const buildParams = (): Record<string, unknown> => {
  const params: Record<string, unknown> = {
    status: 'running',
    page: queryParams.page,
    page_size: queryParams.pageSize,
    has_lock: true,
  }
  if (queryParams.execution_id) params.execution_id = queryParams.execution_id
  if (queryParams.lock_resource) params.lock_resource = queryParams.lock_resource
  if (queryParams.owner) params.owner = queryParams.owner
  return params
}

const fetchLockList = async () => {
  loading.value = true
  try {
    const res: AxiosResponse = await client.get(API.EXECUTIONS, { params: buildParams() })
    const data = res.data?.data ?? res.data
    lockList.value = data?.items ?? data?.results ?? data?.list ?? []
    total.value = data?.total ?? data?.count ?? 0
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '获取锁列表失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

// ---------- 事件处理 ----------
const handleSearch = () => {
  queryParams.page = 1
  fetchLockList()
}

const handleReset = () => {
  queryParams.execution_id = ''
  queryParams.lock_resource = ''
  queryParams.owner = ''
  queryParams.page = 1
  queryParams.pageSize = 20
  fetchLockList()
}

const handleSelectionChange = (rows: LockEntry[]) => {
  selectedRows.value = rows
}

const handleViewExecution = (row: LockEntry) => {
  // Navigate to execution detail if router available
  console.log('View execution:', row.id || row.execution_id)
}

const handleViewDetail = (row: LockEntry) => {
  currentLock.value = row
  detailVisible.value = true
}

const handleRelease = async (row: LockEntry) => {
  try {
    const id = row.id || row.execution_id
    await client.post(`${API.EXECUTIONS}${id}/unlock/`)
    ElMessage.success('锁释放成功')
    fetchLockList()
  } catch {
    ElMessage.error('锁释放失败')
  }
}

const handleBatchRelease = async () => {
  if (!selectedRows.value.length) return
  try {
    const ids = selectedRows.value.map(r => r.id || r.execution_id)
    await client.post(`${API.EXECUTIONS}batch-unlock/`, { ids })
    ElMessage.success(`成功释放 ${ids.length} 个锁`)
    selectedRows.value = []
    fetchLockList()
  } catch {
    ElMessage.error('批量释放失败')
  }
}

// ---------- 生命周期 ----------
onMounted(() => {
  fetchLockList()
  // Auto refresh every 30 seconds
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
  padding: 16px;

  .filter-card {
    margin-bottom: 16px;
  }

  .stat-row {
    margin-bottom: 16px;
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
      margin-top: 16px;
    }
  }

  .text-danger {
    color: #f53f3f;
    font-weight: 600;
  }
}
</style>
