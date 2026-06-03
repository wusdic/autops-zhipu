<template>
  <div class="page-container">
    <div class="autops-page-header">
      <h2>工单统计报告</h2>
      <el-button type="primary" @click="fetchData" :icon="Refresh">刷新</el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="6">
        <el-card shadow="hover" v-loading="statsLoading">
          <el-statistic title="工单总数" :value="stats.total" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" v-loading="statsLoading">
          <el-statistic title="待处理" :value="stats.open" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" v-loading="statsLoading">
          <el-statistic title="已关闭" :value="stats.closed" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" v-loading="statsLoading">
          <el-statistic title="平均解决时长" :value="stats.avgResolutionHours ?? 0" suffix="小时" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 工单列表 -->
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>工单明细</span>
          <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期"
            end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width: 300px"
            @change="fetchTickets" />
        </div>
      </template>
      <el-table :data="tickets" v-loading="loading" stripe>
        <el-table-column prop="title" label="工单标题" min-width="180" show-overflow-tooltip />
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.type || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="priorityType(row.priority)">{{ row.priority || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="assignee_name" label="处理人" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="resolved_at" label="解决时间" width="170">
          <template #default="{ row }">{{ formatTime(row.resolved_at) }}</template>
        </el-table-column>
        <el-table-column label="耗时" width="100">
          <template #default="{ row }">
            <span v-if="row.resolved_at && row.created_at">{{ calcDuration(row.created_at, row.resolved_at) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
      <div style="display:flex;justify-content:flex-end;margin-top:16px">
        <el-pagination v-model:current-page="page" v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]" :total="total" layout="total, sizes, prev, pager, next"
          @size-change="fetchTickets" @current-change="fetchTickets" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const loading = ref(false)
const statsLoading = ref(false)
const stats = ref<Record<string, any>>({ total: 0, open: 0, closed: 0, avgResolutionHours: 0 })
const tickets = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const dateRange = ref<string[] | null>(null)

function statusType(s: string) {
  const map: Record<string, string> = { open: 'warning', in_progress: '', pending: 'info', resolved: 'success', closed: 'success', cancelled: 'info' }
  return map[s] || 'info'
}
function statusLabel(s: string) {
  const map: Record<string, string> = { open: '待处理', in_progress: '处理中', pending: '待分配', resolved: '已解决', closed: '已关闭', cancelled: '已取消' }
  return map[s] || s || '-'
}
function priorityType(p: string) {
  const map: Record<string, string> = { critical: 'danger', high: 'danger', medium: 'warning', low: 'info' }
  return map[p] || 'info'
}
function formatTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}
function calcDuration(start: string, end: string) {
  const ms = new Date(end).getTime() - new Date(start).getTime()
  const hours = Math.floor(ms / 3600000)
  const mins = Math.floor((ms % 3600000) / 60000)
  return hours > 0 ? `${hours}时${mins}分` : `${mins}分`
}

async function fetchStats() {
  statsLoading.value = true
  try {
    const res = await client.get(API.TICKET_STATS)
    const d = res.data?.data ?? res.data
    stats.value = { total: d.total ?? 0, open: d.open_count ?? d.open ?? 0, closed: d.closed_count ?? d.closed ?? 0, avgResolutionHours: d.avg_resolution_hours ?? d.avgResolutionHours ?? 0 }
  } catch { stats.value = { total: 0, open: 0, closed: 0, avgResolutionHours: 0 } }
  finally { statsLoading.value = false }
}

async function fetchTickets() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: pageSize.value }
    if (dateRange.value?.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await client.get(API.TICKETS, { params })
    const d = res.data?.data ?? res.data
    tickets.value = d?.items ?? d?.results ?? d?.list ?? (Array.isArray(d) ? d : [])
    total.value = d?.total ?? tickets.value.length
  } catch (e: any) { ElMessage.error('获取工单数据失败') }
  finally { loading.value = false }
}

function fetchData() { fetchStats(); fetchTickets() }
onMounted(fetchData)
</script>
