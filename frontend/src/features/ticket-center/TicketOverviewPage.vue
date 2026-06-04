<template>
  <div class="page-container">
    <div class="autops-page-header">
      <div class="autops-page-title">工单总览</div>
    </div>

    <!-- SLA 看板 -->
    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="6" v-for="card in statCards" :key="card.label">
        <el-card shadow="hover" v-loading="statsLoading">
          <el-statistic :title="card.label" :value="card.value" />
        </el-card>
      </el-col>
    </el-row>

    <!-- SLA 临近到期 -->
    <el-card v-if="slaWarnings.length" style="margin-bottom: 16px">
      <template #header>
        <div style="display:flex;align-items:center;gap:8px">
          <el-icon color="#ff7d00"><Warning /></el-icon>
          <span>SLA 临近到期</span>
        </div>
      </template>
      <el-table stripe :data="slaWarnings"size="small">
        <el-table-column prop="title" label="工单标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="priorityType(row.priority)">{{ row.priority }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="assignee_name" label="处理人" width="100" />
        <el-table-column label="SLA剩余" width="120">
          <template #default="{ row }">
            <span style="color:#ff7d00;font-weight:bold">{{ row.sla_remaining ?? '即将到期' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button plain type="primary" size="small" @click="router.push('/tickets/' + row.id)">处理</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 状态分布 -->
    <el-card style="margin-bottom: 16px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>工单状态分布</span>
          <el-button-group>
            <el-button :type="timeView === 'day' ? 'primary' : ''" size="small" @click="timeView = 'day'">今日</el-button>
            <el-button :type="timeView === 'week' ? 'primary' : ''" size="small" @click="timeView = 'week'">本周</el-button>
            <el-button :type="timeView === 'month' ? 'primary' : ''" size="small" @click="timeView = 'month'">本月</el-button>
          </el-button-group>
        </div>
      </template>
      <el-row :gutter="24">
        <el-col :span="6" v-for="item in statusDistribution" :key="item.status">
          <div style="text-align:center;padding:20px 0">
            <div style="font-size:32px;font-weight:bold" :style="{color: item.color}">{{ item.count }}</div>
            <div style="margin-top:8px;color:#666">{{ item.label }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 我的待办 -->
    <el-card style="margin-bottom: 16px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>我的待办工单</span>
          <el-button type="primary" size="small" @click="router.push('/tickets/create')">新建工单</el-button>
        </div>
      </template>
      <el-table stripe :data="myTickets" v-loading="myLoading">
        <el-table-column prop="title" label="工单标题" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="router.push('/tickets/' + row.id)">{{ row.title }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }"><el-tag size="small">{{ row.type || '-' }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="priorityType(row.priority)">{{ row.priority || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 最近更新 -->
    <el-card>
      <template #header><span>最近更新</span></template>
      <el-table stripe :data="recentTickets" v-loading="recentLoading">
        <el-table-column prop="title" label="工单标题" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="router.push('/tickets/' + row.id)">{{ row.title }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }"><el-tag size="small">{{ row.type || '-' }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="assignee_name" label="处理人" width="100" />
        <el-table-column prop="updated_at" label="更新时间" width="170">
          <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Warning } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()
const statsLoading = ref(false)
const myLoading = ref(false)
const recentLoading = ref(false)
const timeView = ref('week')

const stats = ref<Record<string, any>>({})
const myTickets = ref<any[]>([])
const recentTickets = ref<any[]>([])

const statCards = computed(() => [
  { label: '工单总数', value: stats.value.total ?? 0 },
  { label: '待处理', value: stats.value.open_count ?? stats.value.open ?? 0 },
  { label: '处理中', value: stats.value.in_progress_count ?? stats.value.in_progress ?? 0 },
  { label: '已关闭', value: stats.value.closed_count ?? stats.value.closed ?? 0 },
])

const statusDistribution = computed(() => [
  { status: 'open', label: '待处理', count: stats.value.open_count ?? stats.value.open ?? 0, color: '#ff7d00' },
  { status: 'in_progress', label: '处理中', count: stats.value.in_progress_count ?? stats.value.in_progress ?? 0, color: '#165dff' },
  { status: 'resolved', label: '已解决', count: stats.value.resolved_count ?? stats.value.resolved ?? 0, color: '#00b42a' },
  { status: 'closed', label: '已关闭', count: stats.value.closed_count ?? stats.value.closed ?? 0, color: '#86909c' },
])

const slaWarnings = computed(() => {
  return myTickets.value.filter((t: any) => t.sla_remaining && t.status !== 'closed' && t.status !== 'resolved').slice(0, 5)
})

function priorityType(p: string) {
  return { critical: 'danger', high: 'danger', medium: 'warning', low: 'info' }[p] || 'info'
}
function statusType(s: string) {
  return { open: 'warning', in_progress: '', pending: 'info', resolved: 'success', closed: 'success', cancelled: 'info' }[s] || 'info'
}
function statusLabel(s: string) {
  return { open: '待处理', in_progress: '处理中', pending: '待分配', resolved: '已解决', closed: '已关闭', cancelled: '已取消' }[s] || s || '-'
}
function formatTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

async function fetchStats() {
  statsLoading.value = true
  try {
    const res = await client.get(API.TICKET_STATS)
    stats.value = res.data?.data ?? res.data ?? {}
  } catch {} finally { statsLoading.value = false }
}

async function fetchMyTickets() {
  myLoading.value = true
  try {
    const res = await client.get(API.TICKETS, { params: { page_size: 20, status: 'open,in_progress' } })
    const d = res.data?.data ?? res.data
    myTickets.value = d?.items ?? d?.results ?? (Array.isArray(d) ? d : [])
  } catch {} finally { myLoading.value = false }
}

async function fetchRecent() {
  recentLoading.value = true
  try {
    const res = await client.get(API.TICKETS, { params: { page: 1, page_size: 10 } })
    const d = res.data?.data ?? res.data
    recentTickets.value = d?.items ?? d?.results ?? (Array.isArray(d) ? d : [])
  } catch {} finally { recentLoading.value = false }
}

onMounted(() => { fetchStats(); fetchMyTickets(); fetchRecent() })
</script>
