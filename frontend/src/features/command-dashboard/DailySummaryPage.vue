<template>
  <div class="p-6">
    <div class="autops-page-header">
      <div class="autops-page-title">今日摘要</div>
      <el-date-picker
        v-model="selectedDate"
        type="date"
        placeholder="选择日期"
        value-format="YYYY-MM-DD"
        style="width: 180px"
        @change="fetchSummary"
      />
    </div>

    <!-- 摘要卡片 -->
    <el-row :gutter="16" class="mb-lg">
      <el-col :xs="12" :sm="6" v-for="card in statCards" :key="card.label">
        <div class="autops-metric-card">
          <div class="metric-icon" :style="{ background: card.bg, color: card.color }">
            <el-icon size="20"><component :is="card.icon" /></el-icon>
          </div>
          <div class="metric-label">{{ card.label }}</div>
          <div class="metric-value" :style="{ color: card.color }">{{ card.value }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <!-- 最近活动时间线 -->
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header">
            <div class="autops-card-title">最近活动</div>
          </div>
          <div class="autops-card-body">
            <el-timeline v-if="recentActivities.length">
              <el-timeline-item
                v-for="(item, idx) in recentActivities"
                :key="idx"
                :timestamp="item.time"
                :type="activityType(item.type)"
                placement="top"
              >
                <div style="font-weight: 500; font-size: 13px">{{ item.summary }}</div>
                <div class="text-tertiary" v-if="item.detail">{{ item.detail }}</div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无活动记录" :image-size="60" />
          </div>
        </div>
      </el-col>

      <!-- 今日告警 -->
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header">
            <div class="autops-card-title">今日告警</div>
            <el-tag type="danger" size="small">{{ alertStats.firing || 0 }} 活跃</el-tag>
          </div>
          <div class="autops-card-body" style="padding: 0">
            <el-table :data="todayAlerts" stripe size="small" v-loading="alertsLoading" empty-text="今日暂无告警" max-height="300">
              <el-table-column prop="created_at" label="时间" width="80">
                <template #default="{ row }">
                  <span class="text-tertiary">{{ formatTime(row.created_at) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="title" label="告警" min-width="180" show-overflow-tooltip />
              <el-table-column prop="severity" label="级别" width="70">
                <template #default="{ row }">
                  <el-tag :type="severityType(row.severity)" size="small">{{ severityLabel(row.severity) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="70">
                <template #default="{ row }">
                  <el-tag :type="alertStatusType(row.status)" size="small">{{ alertStatusLabel(row.status) }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <!-- 今日异常 -->
        <div class="autops-card" style="margin-top: 16px">
          <div class="autops-card-header">
            <div class="autops-card-title">今日异常</div>
          </div>
          <div class="autops-card-body" style="padding: 0">
            <el-table :data="todayAnomalies" stripe size="small" v-loading="anomaliesLoading" empty-text="今日暂无异常" max-height="250">
              <el-table-column prop="created_at" label="时间" width="80">
                <template #default="{ row }">
                  <span class="text-tertiary">{{ formatTime(row.created_at) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="title" label="异常" min-width="180" show-overflow-tooltip />
              <el-table-column prop="severity" label="级别" width="70">
                <template #default="{ row }">
                  <el-tag :type="severityType(row.severity)" size="small">{{ severityLabel(row.severity) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="anomalyStatusType(row.status)" size="small">{{ anomalyStatusLabel(row.status) }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <!-- 今日执行 -->
        <div class="autops-card" style="margin-top: 16px">
          <div class="autops-card-header">
            <div class="autops-card-title">今日自动化执行</div>
          </div>
          <div class="autops-card-body" style="padding: 0">
            <el-table :data="todayExecutions" stripe size="small" v-loading="execLoading" empty-text="今日暂无执行" max-height="250">
              <el-table-column prop="created_at" label="时间" width="80">
                <template #default="{ row }">
                  <span class="text-tertiary">{{ formatTime(row.created_at) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="playbook_name" label="Playbook" min-width="160" show-overflow-tooltip>
                <template #default="{ row }">
                  {{ row.playbook_name || row.name || '-' }}
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="execStatusType(row.status)" size="small">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Warning, CircleCheck, VideoPlay, Document } from '@element-plus/icons-vue'
import { dashboardService, alertService, anomalyService } from '@/shared/api'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const selectedDate = ref(new Date().toISOString().slice(0, 10))
const alertsLoading = ref(false)
const anomaliesLoading = ref(false)
const execLoading = ref(false)

const statCards = reactive([
  { label: '今日告警', value: 0, icon: Warning, bg: '#ffece8', color: '#f53f3f' },
  { label: '今日异常', value: 0, icon: Warning, bg: '#fff7e8', color: '#ff7d00' },
  { label: '自动处置', value: 0, icon: VideoPlay, bg: '#e8f3ff', color: '#165dff' },
  { label: '工单创建', value: 0, icon: Document, bg: '#e8ffea', color: '#00b42a' },
])

const alertStats = reactive({ total: 0, firing: 0, resolved: 0 })
const todayAlerts = ref<any[]>([])
const todayAnomalies = ref<any[]>([])
const todayExecutions = ref<any[]>([])
const recentActivities = ref<any[]>([])

// Helpers
const severityMap: Record<string, string> = { critical: '严重', high: '高', medium: '中', low: '低' }
const severityLabel = (s: string) => severityMap[s] || s
const severityType = (s: string): '' | 'success' | 'warning' | 'danger' | 'info' =>
  ({ critical: 'danger', high: 'warning', medium: '', low: 'info' } as any)[s] || 'info'

const alertStatusLabel = (s: string) => ({ firing: '告警中', resolved: '已恢复', acknowledged: '已确认' } as any)[s] || s
const alertStatusType = (s: string): '' | 'success' | 'warning' | 'danger' | 'info' =>
  ({ firing: 'danger', resolved: 'success', acknowledged: 'warning' } as any)[s] || 'info'

const anomalyStatusLabel = (s: string) => ({ open: '新建', acknowledged: '已确认', assigned: '已分配', closed: '已关闭' } as any)[s] || s
const anomalyStatusType = (s: string): '' | 'success' | 'warning' | 'danger' | 'info' =>
  ({ open: 'danger', acknowledged: 'warning', assigned: '', closed: 'success' } as any)[s] || 'info'

const execStatusType = (s: string): '' | 'success' | 'warning' | 'danger' | 'info' =>
  ({ success: 'success', failed: 'danger', running: 'warning', pending: 'info' } as any)[s] || 'info'

const activityType = (t: string): '' | 'success' | 'warning' | 'danger' | 'info' =>
  ({ alert: 'danger', anomaly: 'warning', execution: '', ticket: 'success' } as any)[t] || 'info'

function formatTime(t: string) {
  if (!t) return '-'
  return t.slice(11, 16) || t
}

// Fetch all summary data
async function fetchSummary() {
  await Promise.allSettled([
    fetchDashboardStats(),
    fetchTodayAlerts(),
    fetchTodayAnomalies(),
    fetchTodayExecutions(),
  ])
}

async function fetchDashboardStats() {
  try {
    const res = await dashboardService.stats()
    const data = res.data?.data || res.data
    if (data) {
      statCards[0].value = data.alerts_today ?? data.alert_count ?? 0
      statCards[1].value = data.anomalies_today ?? data.anomaly_count ?? 0
      statCards[2].value = data.executions_today ?? data.execution_count ?? 0
      statCards[3].value = data.tickets_today ?? data.ticket_count ?? 0
      alertStats.total = data.alerts_today ?? 0
      alertStats.firing = data.alerts_firing ?? data.active_alerts ?? 0
      alertStats.resolved = data.alerts_resolved ?? 0

      // Build activity timeline from stats
      const activities: any[] = []
      if (data.recent_activities) {
        recentActivities.value = data.recent_activities
      }
    }
  } catch (e: any) {
    console.warn('Dashboard stats failed:', e.message)
  }
}

async function fetchTodayAlerts() {
  alertsLoading.value = true
  try {
    const res = await alertService.list({
      page_size: 20,
      start_date: selectedDate.value,
    })
    const data = res.data?.data || res.data
    todayAlerts.value = data?.items || data || []
    alertStats.total = todayAlerts.value.length
    alertStats.firing = todayAlerts.value.filter((a: any) => a.status === 'firing').length

    // Add to activity
    todayAlerts.value.slice(0, 5).forEach((a: any) => {
      recentActivities.value.push({
        time: a.created_at,
        type: 'alert',
        summary: `告警: ${a.title}`,
        detail: a.asset_name ? `资产: ${a.asset_name}` : '',
      })
    })
  } catch {
    todayAlerts.value = []
  } finally {
    alertsLoading.value = false
  }
}

async function fetchTodayAnomalies() {
  anomaliesLoading.value = true
  try {
    const res = await anomalyService.list({
      page_size: 20,
      start_date: selectedDate.value,
    })
    const data = res.data?.data || res.data
    todayAnomalies.value = data?.items || data || []
    statCards[1].value = todayAnomalies.value.length

    todayAnomalies.value.slice(0, 5).forEach((a: any) => {
      recentActivities.value.push({
        time: a.created_at || a.discovered_at,
        type: 'anomaly',
        summary: `异常: ${a.title}`,
        detail: a.asset_name ? `资产: ${a.asset_name}` : '',
      })
    })
  } catch {
    todayAnomalies.value = []
  } finally {
    anomaliesLoading.value = false
  }
}

async function fetchTodayExecutions() {
  execLoading.value = true
  try {
    const res = await client.get(API.EXECUTIONS, {
      params: { page_size: 20, start_date: selectedDate.value },
    })
    const data = res.data?.data || res.data
    todayExecutions.value = data?.items || data || []
    statCards[2].value = todayExecutions.value.length

    todayExecutions.value.slice(0, 5).forEach((e: any) => {
      recentActivities.value.push({
        time: e.created_at,
        type: 'execution',
        summary: `执行: ${e.playbook_name || e.name || '-'}`,
        detail: `状态: ${e.status}`,
      })
    })

    // Sort activities by time
    recentActivities.value.sort((a, b) => (b.time || '').localeCompare(a.time || ''))
  } catch {
    todayExecutions.value = []
  } finally {
    execLoading.value = false
  }
}

onMounted(() => fetchSummary())
</script>

<style scoped>

.mb-lg {
  margin-bottom: 16px;
}
.text-tertiary {
  color: #86909c;
  font-size: 12px;
}
</style>
