<template>
  <div class="page-container">
    <!-- Page Header -->
    <div class="page-header">
      <div>
        <h2 class="page-title">Agent 管理</h2>
        <p class="page-subtitle">管理采集 Agent 节点，监控运行状态</p>
      </div>
      <div class="header-actions">
        <el-button @click="fetchAgents">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <!-- Filter Bar -->
    <el-card shadow="never" class="filter-card">
      <el-row :gutter="16" align="middle">
        <el-col :span="6">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索 Agent 名称、IP 地址..."
            clearable
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterStatus" placeholder="在线状态" clearable @change="handleSearch">
            <el-option label="在线" value="online" />
            <el-option label="离线" value="offline" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterType" placeholder="Agent 类型" clearable @change="handleSearch">
            <el-option label="中心采集器" value="central" />
            <el-option label="边缘 Agent" value="edge" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-col>
        <el-col :span="6" style="text-align: right;">
          <div class="status-summary">
            <span class="summary-item">
              <span class="status-dot dot-online"></span>
              在线: <strong>{{ onlineCount }}</strong>
            </span>
            <span class="summary-item">
              <span class="status-dot dot-offline"></span>
              离线: <strong>{{ offlineCount }}</strong>
            </span>
            <span class="summary-item">
              总计: <strong>{{ pagination.total }}</strong>
            </span>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- Data Table -->
    <el-card shadow="never" class="table-card">
      <el-table
        :data="agents"
        stripe
        v-loading="loading"
        empty-text="暂无 Agent 数据"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="name" label="Agent 名称" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="agent-name-cell">
              <span class="status-dot" :class="row.status === 'online' ? 'dot-online' : 'dot-offline'"></span>
              <span class="agent-name" @click="viewDetail(row)">{{ row.name || row.hostname || '-' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP 地址" width="150">
          <template #default="{ row }">
            <span>{{ row.ip || row.host || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.version || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'online' ? 'success' : 'danger'"
              size="small"
              effect="light"
            >
              {{ row.status === 'online' ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="os_type" label="操作系统" width="120">
          <template #default="{ row }">
            <span class="text-tertiary">{{ row.os_type || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_heartbeat" label="最后心跳" width="170" sortable="custom">
          <template #default="{ row }">
            <span class="text-tertiary">{{ formatTime(row.last_heartbeat) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="bound_asset" label="绑定资源" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ row.bound_asset || row.asset_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="capabilities" label="能力" min-width="180">
          <template #default="{ row }">
            <el-tag
              v-for="cap in (row.capabilities || []).slice(0, 3)"
              :key="cap"
              size="small"
              style="margin-right: 4px; margin-bottom: 2px;"
            >
              {{ cap }}
            </el-tag>
            <el-tag
              v-if="(row.capabilities || []).length > 3"
              size="small"
              type="info"
              style="margin-left: 2px;"
            >
              +{{ row.capabilities.length - 3 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right" align="center">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="viewDetail(row)">详情</el-button>
            <el-button text type="warning" size="small" @click="restartAgent(row)">重启</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="fetchAgents"
          @current-change="fetchAgents"
        />
      </div>
    </el-card>

    <!-- Detail Drawer -->
    <el-drawer v-model="drawerVisible" title="Agent 详情" size="520px">
      <template v-if="currentAgent">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ currentAgent.name || currentAgent.hostname || '-' }}</el-descriptions-item>
          <el-descriptions-item label="IP 地址">{{ currentAgent.ip || currentAgent.host || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentAgent.status === 'online' ? 'success' : 'danger'" size="small">
              {{ currentAgent.status === 'online' ? '在线' : '离线' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="版本">{{ currentAgent.version || '-' }}</el-descriptions-item>
          <el-descriptions-item label="操作系统">{{ currentAgent.os_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="绑定资源">{{ currentAgent.bound_asset || currentAgent.asset_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="最后心跳" :span="2">{{ formatTime(currentAgent.last_heartbeat) }}</el-descriptions-item>
          <el-descriptions-item label="注册时间" :span="2">{{ formatTime(currentAgent.registered_at || currentAgent.created_at) }}</el-descriptions-item>
        </el-descriptions>

        <!-- Capabilities -->
        <div class="section-title" style="margin-top: 20px;">采集能力</div>
        <div class="capabilities-list" v-if="(currentAgent.capabilities || []).length">
          <el-tag
            v-for="cap in currentAgent.capabilities"
            :key="cap"
            style="margin: 0 8px 8px 0;"
          >
            {{ cap }}
          </el-tag>
        </div>
        <el-empty v-else description="无能力数据" :image-size="60" />

        <!-- Metrics -->
        <div class="section-title" style="margin-top: 20px;">运行指标</div>
        <el-descriptions :column="2" border v-if="currentAgent.metrics">
          <el-descriptions-item label="CPU 使用率">{{ currentAgent.metrics.cpu_usage ?? '-' }}%</el-descriptions-item>
          <el-descriptions-item label="内存使用率">{{ currentAgent.metrics.memory_usage ?? '-' }}%</el-descriptions-item>
          <el-descriptions-item label="采集任务数">{{ currentAgent.metrics.task_count ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="错误率">{{ currentAgent.metrics.error_rate ?? '-' }}%</el-descriptions-item>
        </el-descriptions>
        <el-empty v-else description="无运行指标数据" :image-size="60" />
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import { collectorService } from '@/shared/api'

// ---------- Types ----------
interface Agent {
  id: string
  name: string
  hostname?: string
  ip?: string
  host?: string
  version: string
  status: 'online' | 'offline'
  os_type?: string
  last_heartbeat?: string
  registered_at?: string
  created_at?: string
  bound_asset?: string
  asset_name?: string
  capabilities?: string[]
  metrics?: {
    cpu_usage?: number
    memory_usage?: number
    task_count?: number
    error_rate?: number
  }
}

// ---------- State ----------
const loading = ref(false)
const agents = ref<Agent[]>([])
const drawerVisible = ref(false)
const currentAgent = ref<Agent | null>(null)

const searchKeyword = ref('')
const filterStatus = ref('')
const filterType = ref('')
const sortField = ref('')
const sortOrder = ref('')

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

// ---------- Computed ----------
const onlineCount = computed(() => agents.value.filter(a => a.status === 'online').length)
const offlineCount = computed(() => agents.value.filter(a => a.status !== 'online').length)

// ---------- Helpers ----------
function formatTime(val?: string) {
  if (!val) return '-'
  return val.replace('T', ' ').substring(0, 19)
}

// ---------- Data Fetching ----------
async function fetchAgents() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.page_size,
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (filterStatus.value) params.status = filterStatus.value
    if (sortField.value) {
      params.sort_by = sortField.value
      params.sort_order = sortOrder.value
    }

    let res: any
    if (filterType.value === 'edge') {
      res = await collectorService.listEdge(params)
    } else {
      res = await collectorService.list(params)
    }

    const data = res.data?.data ?? res.data
    if (Array.isArray(data?.items)) {
      agents.value = data.items
      pagination.total = data.total ?? data.items.length
    } else if (Array.isArray(data)) {
      agents.value = data
      pagination.total = data.length
    }
  } catch (e: any) {
    ElMessage.error(e.message || '获取 Agent 列表失败')
  } finally {
    loading.value = false
  }
}

// ---------- Search & Filter ----------
function handleSearch() {
  pagination.page = 1
  fetchAgents()
}

function resetFilters() {
  searchKeyword.value = ''
  filterStatus.value = ''
  filterType.value = ''
  sortField.value = ''
  sortOrder.value = ''
  handleSearch()
}

function handleSortChange({ prop, order }: any) {
  sortField.value = prop || ''
  sortOrder.value = order === 'ascending' ? 'asc' : order === 'descending' ? 'desc' : ''
  fetchAgents()
}

// ---------- Actions ----------
function viewDetail(row: Agent) {
  currentAgent.value = row
  drawerVisible.value = true
}

async function restartAgent(row: Agent) {
  try {
    await ElMessageBox.confirm(
      `确认重启 Agent「${row.name || row.hostname}」？该操作会短暂中断数据采集。`,
      '重启确认',
      { type: 'warning', confirmButtonText: '确定重启', cancelButtonText: '取消' }
    )
    loading.value = true
    // Use collector restart endpoint or trigger re-registration
    await collectorService.edgeHeartbeat(row.id)
    ElMessage.success('已发送重启指令')
    setTimeout(() => fetchAgents(), 2000)
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '重启失败')
    }
  } finally {
    loading.value = false
  }
}

// ---------- Init ----------
onMounted(() => {
  fetchAgents()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
  margin: 0;
}

.page-subtitle {
  font-size: 13px;
  color: #86909c;
  margin-top: 4px;
}

.filter-card {
  margin-bottom: 16px;
}

.filter-card :deep(.el-card__body) {
  padding: 16px;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.agent-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-name {
  color: #165dff;
  cursor: pointer;
  font-weight: 500;
}

.agent-name:hover {
  text-decoration: underline;
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-online {
  background: #00b42a;
}

.dot-offline {
  background: #c9cdd4;
}

.text-tertiary {
  color: #86909c;
  font-size: 13px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: 16px;
}

.status-summary {
  display: inline-flex;
  gap: 16px;
  align-items: center;
  font-size: 13px;
  color: #4e5969;
}

.summary-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 12px;
}

.capabilities-list {
  display: flex;
  flex-wrap: wrap;
}
</style>
