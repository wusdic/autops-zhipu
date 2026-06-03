<template>
  <div class="page-container">
    <div class="autops-page-header">
      <h2>运维总览报告</h2>
      <div>
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期"
          end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width: 300px;margin-right:12px" />
        <el-button type="primary" @click="fetchData" :icon="Refresh">刷新</el-button>
      </div>
    </div>

    <!-- 总览统计 -->
    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="4" v-for="card in summaryCards" :key="card.label">
        <el-card shadow="hover" v-loading="loading">
          <el-statistic :title="card.label" :value="card.value" :suffix="card.suffix" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 资产概况 -->
    <el-card style="margin-bottom: 16px">
      <template #header><span>资产概况</span></template>
      <el-table :data="assetStats" v-loading="loading" stripe size="small">
        <el-table-column prop="type" label="资产类型" />
        <el-table-column prop="total" label="总数" width="80" />
        <el-table-column prop="online" label="在线" width="80" />
        <el-table-column prop="offline" label="离线" width="80" />
        <el-table-column prop="alerting" label="告警中" width="80" />
      </el-table>
    </el-card>

    <!-- 告警概况 -->
    <el-card style="margin-bottom: 16px">
      <template #header><span>告警概况</span></template>
      <el-table :data="alertList" v-loading="loading" stripe size="small">
        <el-table-column prop="title" label="告警标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="severity" label="严重度" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="severityType(row.severity)">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="alertStatusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="触发时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 执行概况 -->
    <el-card style="margin-bottom: 16px">
      <template #header><span>自动化执行概况</span></template>
      <el-table :data="execList" v-loading="loading" stripe size="small">
        <el-table-column prop="name" label="执行名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="execStatusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="trigger_type" label="触发方式" width="100" />
        <el-table-column prop="started_at" label="开始时间" width="170">
          <template #default="{ row }">{{ formatTime(row.started_at) }}</template>
        </el-table-column>
        <el-table-column prop="finished_at" label="结束时间" width="170">
          <template #default="{ row }">{{ formatTime(row.finished_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 工单概况 -->
    <el-card>
      <template #header><span>工单概况</span></template>
      <el-table :data="ticketList" v-loading="loading" stripe size="small">
        <el-table-column prop="title" label="工单标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const loading = ref(false)
const dateRange = ref<string[] | null>(null)
const dashboardData = ref<Record<string, any>>({})
const alertList = ref<any[]>([])
const execList = ref<any[]>([])
const ticketList = ref<any[]>([])

const summaryCards = computed(() => [
  { label: '资产总数', value: dashboardData.value.assets?.total ?? 0 },
  { label: '活跃告警', value: dashboardData.value.alerts?.active ?? dashboardData.value.alerts?.total ?? 0 },
  { label: '异常数', value: dashboardData.value.anomalies?.total ?? 0 },
  { label: '执行次数', value: dashboardData.value.automation?.total ?? 0 },
  { label: '工单数', value: dashboardData.value.tickets?.total ?? 0 },
  { label: '巡检完成率', value: dashboardData.value.inspection?.completion_rate ?? 0, suffix: '%' },
])

const assetStats = computed(() => {
  const types = dashboardData.value.assets?.by_type ?? {}
  return Object.entries(types).map(([type, info]: [string, any]) => ({
    type,
    total: info.total ?? info ?? 0,
    online: info.online ?? 0,
    offline: info.offline ?? 0,
    alerting: info.alerting ?? 0,
  }))
})

function severityType(s: string) {
  return { critical: 'danger', high: 'danger', warning: 'warning', info: 'info' }[s] || 'info'
}
function alertStatusType(s: string) {
  return { active: 'danger', acknowledged: 'warning', resolved: 'success' }[s] || 'info'
}
function execStatusType(s: string) {
  return { completed: 'success', success: 'success', running: 'warning', failed: 'danger', pending: 'info' }[s] || 'info'
}
function formatTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

async function fetchData() {
  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (dateRange.value?.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const [dashRes, alertRes, execRes, ticketRes] = await Promise.allSettled([
      client.get(API.DASHBOARD.STATS, { params }),
      client.get(API.ALERTS, { params: { page_size: 10, ...params } }),
      client.get(API.EXECUTIONS, { params: { page_size: 10, ...params } }),
      client.get(API.TICKETS, { params: { page_size: 10, ...params } }),
    ])
    if (dashRes.status === 'fulfilled') {
      dashboardData.value = dashRes.value.data?.data ?? dashRes.value.data
    }
    if (alertRes.status === 'fulfilled') {
      const d = alertRes.value.data?.data ?? alertRes.value.data
      alertList.value = d?.items ?? d?.results ?? (Array.isArray(d) ? d : [])
    }
    if (execRes.status === 'fulfilled') {
      const d = execRes.value.data?.data ?? execRes.value.data
      execList.value = d?.items ?? d?.results ?? (Array.isArray(d) ? d : [])
    }
    if (ticketRes.status === 'fulfilled') {
      const d = ticketRes.value.data?.data ?? ticketRes.value.data
      ticketList.value = d?.items ?? d?.results ?? (Array.isArray(d) ? d : [])
    }
  } catch (e: any) { ElMessage.error('获取报告数据失败') }
  finally { loading.value = false }
}

onMounted(fetchData)
</script>
