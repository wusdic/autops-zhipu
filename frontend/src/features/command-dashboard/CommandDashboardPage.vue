<template>
  <div class="autops-page-container">
    <!-- 页面头部 -->
    <div class="autops-page-header">
      <div class="autops-page-title">指挥中心</div>
      <div class="autops-page-desc">全局态势感知与运维指挥总览</div>
    </div>

    <!-- ─── 第一行：核心态势指标（V3 M1-RQ-001） ─── -->
    <el-row :gutter="16" class="metric-row">
      <el-col :xs="12" :sm="8" :md="4">
        <div class="autops-metric-card is-clickable" @click="navigateTo('/alerts?severity=critical')">
          <div class="metric-icon bg-danger">
            <el-icon size="20"><AlarmClock /></el-icon>
          </div>
          <div class="metric-label">严重告警</div>
          <div class="metric-value text-danger">{{ stats.criticalAlerts }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <div class="autops-metric-card is-clickable" @click="navigateTo('/response/anomalies')">
          <div class="metric-icon bg-warning">
            <el-icon size="20"><Warning /></el-icon>
          </div>
          <div class="metric-label">待处理异常</div>
          <div class="metric-value text-warning">{{ stats.pendingAnomalies }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <div class="autops-metric-card is-clickable" @click="navigateTo('/assets')">
          <div class="metric-icon bg-brand">
            <el-icon size="20"><Box /></el-icon>
          </div>
          <div class="metric-label">资产总数</div>
          <div class="metric-value">{{ stats.totalAssets }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <div class="autops-metric-card is-clickable" @click="navigateTo('/inspection/tasks')">
          <div class="metric-icon bg-success">
            <el-icon size="20"><CircleCheck /></el-icon>
          </div>
          <div class="metric-label">巡检成功率</div>
          <div class="metric-value">{{ stats.inspectionSuccessRate }}%</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <div class="autops-metric-card is-clickable" @click="navigateTo('/automation/executions')">
          <div class="metric-icon bg-brand">
            <el-icon size="20"><VideoPlay /></el-icon>
          </div>
          <div class="metric-label">自动处置率</div>
          <div class="metric-value">{{ stats.autoRemediationRate }}%</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <div class="autops-metric-card is-clickable" @click="navigateTo('/automation/approvals')">
          <div class="metric-icon bg-warning">
            <el-icon size="20"><Clock /></el-icon>
          </div>
          <div class="metric-label">待审批</div>
          <div class="metric-value text-warning">{{ stats.pendingApprovals }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- ─── 第二行：V3五条主线卡片（M1-RQ-002~008） ─── -->
    <el-row :gutter="16" class="mt-lg">
      <!-- M1-RQ-002 资产发现卡片 -->
      <el-col :xs="12" :sm="8" :md="6">
        <div class="autops-card v3-card" @click="navigateTo('/resource-center/discovery')">
          <div class="autops-card-header">
            <div class="autops-card-title"><el-icon><Search /></el-icon> 资产发现</div>
          </div>
          <div class="autops-card-body v3-card-body">
            <div class="autops-metric-card autops-metric-card-num autops-metric-card-label"><span >{{ discoveryStats.todayFound }}</span><span >今日发现</span></div>
            <div class="autops-metric-card autops-metric-card-num text-warning autops-metric-card-label"><span >{{ discoveryStats.pendingConfirm }}</span><span >待确认</span></div>
            <div class="autops-metric-card autops-metric-card-num text-success autops-metric-card-label"><span >{{ discoveryStats.managed }}</span><span >已纳管</span></div>
          </div>
        </div>
      </el-col>
      <!-- M1-RQ-003 巡检实况卡片 -->
      <el-col :xs="12" :sm="8" :md="6">
        <div class="autops-card v3-card" @click="navigateTo('/inspection/tasks')">
          <div class="autops-card-header">
            <div class="autops-card-title"><el-icon><CircleCheck /></el-icon> 巡检实况</div>
          </div>
          <div class="autops-card-body v3-card-body">
            <div class="autops-metric-card autops-metric-card-num text-primary autops-metric-card-label"><span >{{ inspectionStats.running }}</span><span >正在巡检</span></div>
            <div class="autops-metric-card autops-metric-card-num text-danger autops-metric-card-label"><span >{{ inspectionStats.failed }}</span><span >巡检失败</span></div>
            <div class="autops-metric-card autops-metric-card-num text-warning autops-metric-card-label"><span >{{ inspectionStats.abnormalItems }}</span><span >异常巡检项</span></div>
          </div>
        </div>
      </el-col>
      <!-- M1-RQ-005 自动处置卡片 -->
      <el-col :xs="12" :sm="8" :md="6">
        <div class="autops-card v3-card" @click="navigateTo('/automation/executions')">
          <div class="autops-card-header">
            <div class="autops-card-title"><el-icon><VideoPlay /></el-icon> 自动处置</div>
          </div>
          <div class="autops-card-body v3-card-body">
            <div class="autops-metric-card autops-metric-card-num text-success autops-metric-card-label"><span >{{ remediationStats.autoHandled }}</span><span >自动处理</span></div>
            <div class="autops-metric-card autops-metric-card-num text-warning autops-metric-card-label"><span >{{ remediationStats.rollbackCount }}</span><span >回滚</span></div>
            <div class="autops-metric-card autops-metric-card-num autops-metric-card-label"><span >{{ remediationStats.successRate }}%</span><span >成功率</span></div>
          </div>
        </div>
      </el-col>
      <!-- M1-RQ-007 报告任务卡片 -->
      <el-col :xs="12" :sm="8" :md="6">
        <div class="autops-card v3-card" @click="navigateTo('/report-audit/tasks')">
          <div class="autops-card-header">
            <div class="autops-card-title"><el-icon><Document /></el-icon> 报告任务</div>
          </div>
          <div class="autops-card-body v3-card-body">
            <div class="autops-metric-card autops-metric-card-num text-primary autops-metric-card-label"><span >{{ reportStats.generating }}</span><span >生成中</span></div>
            <div class="autops-metric-card autops-metric-card-num text-success autops-metric-card-label"><span >{{ reportStats.completed }}</span><span >已完成</span></div>
            <div class="autops-metric-card autops-metric-card-num text-danger autops-metric-card-label"><span >{{ reportStats.failed }}</span><span >失败</span></div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- ─── 内容区: 左大右小 ─── -->
    <el-row :gutter="16" class="mt-lg">
      <!-- 左栏：告警趋势 + 最近告警 -->
      <el-col :xs="24" :lg="16">
        <!-- 告警趋势 -->
        <div class="autops-card mb-lg">
          <div class="autops-card-header">
            <div class="autops-card-title">
              <el-icon><TrendCharts /></el-icon>
              采集成功率趋势
            </div>
            <el-radio-group v-model="trendRange" size="small">
              <el-radio-button value="24h">24小时</el-radio-button>
              <el-radio-button value="7d">7天</el-radio-button>
            </el-radio-group>
          </div>
          <div class="autops-card-body">
            <div ref="chartRef" style="height: 240px"></div>
          </div>
        </div>

        <!-- 最近告警 -->
        <div class="autops-card">
          <div class="autops-card-header">
            <div class="autops-card-title">
              <el-icon><AlarmClock /></el-icon>
              最近告警
            </div>
            <el-button plain type="primary" @click="navigateTo('/alerts')">
              查看全部 →
            </el-button>
          </div>
          <div class="autops-card-body p-0">
            <el-table stripe
 :data="recentAlerts"size="default"
 :max-height="300"
 @row-click="(row: any) => navigateTo('/alerts/' + row.id)"
              style="cursor: pointer"
              empty-text="暂无告警"
            >
              <el-table-column prop="severity" label="级别" width="80">
                <template #default="{ row }">
                  <span class="autops-status-tag" :class="getSeverityClass(row.severity)">
                    {{ row.severity }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="title" label="告警标题" min-width="200" show-overflow-tooltip />
              <el-table-column prop="asset_name" label="资产" width="140" show-overflow-tooltip />
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <span class="autops-status-tag" :class="'status-' + row.status">
                    {{ getStatusText(row.status) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="时间" width="160">
                <template #default="{ row }">
                  <span class="text-tertiary font-12">{{ formatTime(row.created_at) }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>

      <!-- 右栏：资产健康 + 执行统计 + 快捷操作 -->
      <el-col :xs="24" :lg="8">
        <!-- 资产健康概览 -->
        <div class="autops-card mb-lg">
          <div class="autops-card-header">
            <div class="autops-card-title">
              <el-icon><DataAnalysis /></el-icon>
              资产健康概览
            </div>
          </div>
          <div class="autops-card-body">
            <div v-for="item in healthData" :key="item.label" class="health-bar-item">
              <div class="health-bar-label">
                <span :class="'health-dot health-dot-' + item.key"></span>
                <span class="font-14">{{ item.label }}</span>
                <span class="font-12 text-tertiary ml-auto" >{{ item.count }}</span>
              </div>
              <el-progress
                :percentage="item.percent"
                :color="item.color"
                :show-text="false"
                :stroke-width="6"
              />
            </div>
          </div>
        </div>

        <!-- 自动化执行统计 -->
        <div class="autops-card mb-lg">
          <div class="autops-card-header">
            <div class="autops-card-title">
              <el-icon><VideoPlay /></el-icon>
              自动化执行统计
            </div>
          </div>
          <div class="autops-card-body">
            <div class="exec-stats">
              <div class="exec-stat-item">
                <div class="font-12 text-tertiary mb-xs">成功率</div>
                <div class="font-20" :class="remediationStats.successRate >= 95 ? 'text-success' : remediationStats.successRate >= 80 ? 'text-warning' : 'text-danger'">
                  {{ remediationStats.successRate }}%
                </div>
              </div>
              <div class="exec-stat-item">
                <div class="font-12 text-tertiary mb-xs">今日执行</div>
                <div class="font-20">{{ todaySummary.autoRemediations + todaySummary.manualApprovals }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 快捷操作 -->
        <div class="autops-card">
          <div class="autops-card-header">
            <div class="autops-card-title">
              <el-icon><Star /></el-icon>
              快捷操作
            </div>
          </div>
          <div class="autops-card-body">
            <div class="quick-actions">
              <div class="quick-action-btn" @click="navigateTo('/assets')">
                <el-icon size="20" color="#165dff"><Box /></el-icon>
                <span>资产管理</span>
              </div>
              <div class="quick-action-btn" @click="navigateTo('/alerts')">
                <el-icon size="20" color="#f53f3f"><AlarmClock /></el-icon>
                <span>告警处理</span>
              </div>
              <div class="quick-action-btn" @click="navigateTo('/tickets')">
                <el-icon size="20" color="#ff7d00"><Tickets /></el-icon>
                <span>工单中心</span>
              </div>
              <div class="quick-action-btn" @click="navigateTo('/knowledge')">
                <el-icon size="20" color="#00b42a"><Collection /></el-icon>
                <span>知识库</span>
              </div>
              <div class="quick-action-btn" @click="navigateTo('/incident')">
                <el-icon size="20" color="#86909c"><Warning /></el-icon>
                <span>应急响应</span>
              </div>
              <div class="quick-action-btn" @click="navigateTo('/inspection/overview')">
                <el-icon size="20" color="#00b42a"><CircleCheck /></el-icon>
                <span>巡检中心</span>
              </div>
              <div class="quick-action-btn" @click="navigateTo('/report-audit/overview')">
                <el-icon size="20" color="#722ed1"><Document /></el-icon>
                <span>报表审计</span>
              </div>
            </div>
          </div>
        </div>

        <!-- M1-RQ-006 待我处理 -->
        <div class="autops-card mt-lg">
          <div class="autops-card-header">
            <div class="autops-card-title"><el-icon><Bell /></el-icon> 待我处理</div>
            <el-button plain type="primary" size="small" @click="navigateTo('/automation/approvals')">全部 →</el-button>
          </div>
          <div class="autops-card-body p-0">
            <el-table stripe :data="pendingTasks"size="small" :max-height="200" empty-text="暂无待办">
              <el-table-column prop="type" label="类型" width="90">
                <template #default="{ row }">
                  <el-tag size="small" :type="(pendingTypeTag(row.type)) as TagType">{{ row.type }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="title" label="内容" min-width="180" show-overflow-tooltip />
              <el-table-column prop="priority" label="优先级" width="70">
                <template #default="{ row }">
                  <span :class="'priority-' + row.priority">{{ row.priority }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="时间" width="100">
                <template #default="{ row }"><span class="text-tertiary font-12">{{ formatTime(row.created_at) }}</span></template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <!-- M1-RQ-008 平台健康卡片 -->
        <div class="autops-card mt-lg">
          <div class="autops-card-header">
            <div class="autops-card-title"><el-icon><Monitor /></el-icon> 平台健康</div>
          </div>
          <div class="autops-card-body" v-loading="platformHealthLoading">
            <div class="platform-health-grid">
              <div v-for="comp in platformHealth" :key="comp.name" class="health-item">
                <span class="health-dot" :class="'health-dot-' + comp.status"></span>
                <span class="font-12">{{ comp.name }}</span>
                <span class="font-12 text-tertiary ml-auto" >{{ comp.latency }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- M1-RQ-010 今日摘要 -->
        <div class="autops-card mt-lg">
          <div class="autops-card-header">
            <div class="autops-card-title"><el-icon><Calendar /></el-icon> 今日摘要</div>
          </div>
          <div class="autops-card-body">
            <div class="today-summary">
              <div class="summary-item summary-label summary-val"><span >新增资产</span><span >{{ todaySummary.newAssets }}</span></div>
              <div class="summary-item summary-label summary-val"><span >完成巡检</span><span >{{ todaySummary.inspections }}</span></div>
              <div class="summary-item summary-label summary-val text-warning"><span >发现异常</span><span >{{ todaySummary.anomalies }}</span></div>
              <div class="summary-item summary-label summary-val text-success"><span >自动处置</span><span >{{ todaySummary.autoRemediations }}</span></div>
              <div class="summary-item summary-label summary-val"><span >人工审批</span><span >{{ todaySummary.manualApprovals }}</span></div>
              <div class="summary-item summary-label summary-val"><span >生成报告</span><span >{{ todaySummary.reports }}</span></div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()

// ─── Stats（V3 M1态势总览） ───
const stats = reactive({
  criticalAlerts: 0,
  pendingAnomalies: 0,
  totalAssets: 0,
  inspectionSuccessRate: 0,
  autoRemediationRate: 0,
  pendingApprovals: 0,
})

// M1-RQ-002 资产发现
const discoveryStats = reactive({ todayFound: 0, pendingConfirm: 0, managed: 0 })
// M1-RQ-003 巡检实况
const inspectionStats = reactive({ running: 0, failed: 0, abnormalItems: 0 })
// M1-RQ-005 自动处置
const remediationStats = reactive({ autoHandled: 0, rollbackCount: 0, successRate: 0 })
// M1-RQ-007 报告任务
const reportStats = reactive({ generating: 0, completed: 0, failed: 0 })
// M1-RQ-006 待我处理
const pendingTasks = ref<any[]>([])
// M1-RQ-008 平台健康
const platformHealth = ref<{ name: string; status: string; latency: string }[]>([])
const platformHealthLoading = ref(false)

async function fetchPlatformHealth() {
  platformHealthLoading.value = true
  try {
    const res = await api.get('/api/v1/dashboard/platform-health')
    const d = res.data?.data ?? res.data
    if (d?.components) {
      const nameMap: Record<string, string> = {
        database: 'DB', redis: 'Redis', api_server: 'API',
        worker: 'Worker', scheduler: 'Scheduler', websocket: 'WebSocket',
      }
      platformHealth.value = Object.entries(d.components).map(([key, val]: [string, any]) => ({
        name: nameMap[key] || key,
        status: (val.status === 'ok' || val.status === 'healthy') ? 'healthy' : (val.status === 'degraded' ? 'warning' : 'unhealthy'),
        latency: val.message || '',
      }))
    }
  } catch {
    platformHealth.value = [{ name: 'API', status: 'unhealthy', latency: '无法连接' }]
  } finally {
    platformHealthLoading.value = false
  }
}
// M1-RQ-010 今日摘要
const todaySummary = reactive({
  newAssets: 0, inspections: 0, anomalies: 0,
  autoRemediations: 0, manualApprovals: 0, reports: 0,
})

const recentAlerts = ref<any[]>([])
const trendRange = ref('24h')
const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const execStats = reactive({
  successRate: 0,
  todayCount: 0,
})

// 删除旧的execStats（数据已整合到remediationStats/todaySummary）
void execStats

const healthData = ref([
  { key: 'healthy', label: '健康', count: 0, percent: 0, color: '#00b42a' },
  { key: 'warning', label: '告警', count: 0, percent: 0, color: '#ff7d00' },
  { key: 'critical', label: '故障', count: 0, percent: 0, color: '#f53f3f' },
  { key: 'unknown', label: '未知', count: 0, percent: 0, color: '#86909c' },
])

// ─── API ───
const chartRawData = ref<{ time: string; success: number; total: number }[]>([])
let allJobs: any[] = []

async function fetchDashboard() {
  try {
    // 并发请求（使用统一api client + routes常量）
    const [alertsRes, assetsRes, execRes, eventsRes, jobsRes] = await Promise.all([
      api.get(API.ALERTS, { params: { page_size: 5 } }),
      api.get(API.ASSETS, { params: { page_size: 100 } }),
      api.get(API.EXECUTIONS, { params: { page_size: 100 } }),
      api.get(API.EVENTS, { params: { page_size: 1 } }),
      api.get(API.COLLECTION_JOBS, { params: { page_size: 100 } }),
    ])

    const alertsData = alertsRes.data
    if (alertsData?.code === 0) {
      const items = alertsData.data?.items || []
      recentAlerts.value = items
      stats.criticalAlerts = items.filter((a: any) => a.severity === 'critical').length
    }

    const assetsData = assetsRes.data
    if (assetsData?.code === 0) {
      stats.totalAssets = assetsData.data?.total || 0
      const allItems = assetsData.data?.items || []
      // 资产发现统计
      const todayStart = new Date(); todayStart.setHours(0,0,0,0)
      const todayAssets = allItems.filter((a: any) => new Date(a.created_at) >= todayStart)
      discoveryStats.todayFound = todayAssets.length
      discoveryStats.pendingConfirm = allItems.filter((a: any) => a.reachability === 'unknown').length
      discoveryStats.managed = allItems.filter((a: any) => a.reachability === 'reachable').length
      todaySummary.newAssets = todayAssets.length
      healthData.value[0].count = allItems.filter((a: any) => a.health_status === 'healthy').length
      healthData.value[1].count = allItems.filter((a: any) => a.health_status === 'warning').length
      healthData.value[2].count = allItems.filter((a: any) => a.health_status === 'critical').length
      healthData.value[3].count = allItems.filter((a: any) => !['healthy','warning','critical'].includes(a.health_status)).length
      const total = healthData.value.reduce((s, h) => s + h.count, 0)
      healthData.value.forEach(h => {
        h.percent = total > 0 ? Math.round(h.count / total * 100) : 0
      })
    }

    const execData = execRes.data
    if (execData?.code === 0) {
      const items = execData.data?.items || []
      stats.pendingApprovals = items.filter((e: any) =>
        e.status === 'awaiting_approval'
      ).length
      const todayStart2 = new Date(); todayStart2.setHours(0,0,0,0)
      const todayItems = items.filter((e: any) => new Date(e.created_at) >= todayStart2)
      const finished = todayItems.filter((e: any) => ['success', 'failed', 'cancelled'].includes(e.status))
      const successCount = todayItems.filter((e: any) => e.status === 'success').length
      // 自动处置统计
      remediationStats.autoHandled = todayItems.filter((e: any) => e.status === 'success' && e.triggered_by === 'auto').length
      remediationStats.rollbackCount = todayItems.filter((e: any) => e.status === 'rolled_back').length
      remediationStats.successRate = finished.length > 0 ? Math.round(successCount / finished.length * 100) : 0
      stats.autoRemediationRate = remediationStats.successRate
      todaySummary.autoRemediations = remediationStats.autoHandled
      todaySummary.manualApprovals = todayItems.filter((e: any) => e.triggered_by === 'manual').length
      // 待我处理列表
      pendingTasks.value = items
        .filter((e: any) => ['awaiting_approval', 'pending'].includes(e.status))
        .slice(0, 5)
        .map((e: any) => ({
          type: '执行审批',
          title: e.execution_type || '执行任务 #' + e.id?.slice(0,8),
          priority: e.risk_level || 'medium',
          created_at: e.created_at,
        }))
    }

    const eventsData = eventsRes.data
    if (eventsData?.code === 0) {
      stats.pendingAnomalies = eventsData.data?.total || 0
      todaySummary.anomalies = eventsData.data?.total || 0
    }

    // Collection jobs → success rate trend
    const jobsData = jobsRes.data
    if (jobsData?.code === 0) {
      const jobs = jobsData.data?.items || []
      allJobs = jobs
      computeTrendData(jobs)
    }
  } catch (e) {
    console.error('Dashboard fetch error:', e)
  }
}

function computeTrendData(jobs: any[]) {
  const is24h = trendRange.value === '24h'
  const buckets = is24h ? 24 : 7
  const bucketMs = is24h ? 3600000 : 86400000
  const now = Date.now()

  const bucketMap: Record<string, { success: number; total: number }> = {}
  for (let i = buckets - 1; i >= 0; i--) {
    const bucketStart = now - i * bucketMs
    const d = new Date(bucketStart)
    const label = is24h ? d.getHours() + ':00' : d.getMonth()+1 + '/' + d.getDate()
    bucketMap[label] = { success: 0, total: 0 }
  }

  for (const job of jobs) {
    const ts = job.last_run_at || job.updated_at || job.created_at
    if (!ts) continue
    const t = new Date(ts).getTime()
    const age = now - t
    if (age > buckets * bucketMs) continue

    const d = new Date(t)
    const label = is24h ? d.getHours() + ':00' : d.getMonth()+1 + '/' + d.getDate()
    if (bucketMap[label]) {
      bucketMap[label].total++
      if (job.status === 'completed') bucketMap[label].success++
    }
  }

  chartRawData.value = Object.entries(bucketMap).map(([time, v]) => ({
    time,
    success: v.total > 0 ? Math.round(v.success / v.total * 100) : 0,
    total: v.total,
  }))
}

// ─── Chart ───
function initChart() {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  renderChart()
}

function renderChart() {
  if (!chartInstance) return

  const xData = chartRawData.value.map(d => d.time)
  const yData = chartRawData.value.map(d => d.success)

  // If no real data at all, show empty state
  const hasData = chartRawData.value.some(d => d.total > 0)

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const idx = params[0]?.dataIndex
        if (idx == null || idx >= chartRawData.value.length) return ''
        const d = chartRawData.value[idx]
        return d.time + '<br/>成功率: ' + (d.total > 0 ? d.success + '%' : '无数据') + '<br/>任务数: ' + d.total
      },
    },
    grid: { left: 40, right: 20, top: 16, bottom: 30 },
    xAxis: {
      type: 'category',
      data: xData,
      axisLabel: { color: '#86909c', fontSize: 11 },
      axisLine: { lineStyle: { color: '#e5e6eb' } },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { color: '#86909c', fontSize: 11, formatter: '{value}%' },
      splitLine: { lineStyle: { color: '#f2f3f5' } },
    },
    series: [{
      data: yData,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      lineStyle: { color: '#165dff', width: 2 },
      itemStyle: { color: '#165dff' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(22,93,255,0.2)' },
          { offset: 1, color: 'rgba(22,93,255,0)' },
        ]),
      },
    }],
    graphic: hasData ? [] : [{
      type: 'text',
      left: 'center',
      top: 'middle',
      style: {
        text: '暂无采集数据',
        fontSize: 14,
        fill: '#c9cdd4',
      },
    }],
  })
}

// ─── Helpers ───
function navigateTo(path: string) {
  router.push(path).catch(() => {})
}

function getSeverityClass(severity: string): string {
  const map: Record<string, string> = {
    critical: 'status-failed',
    high: 'status-warning',
    medium: 'status-info',
    low: 'status-info',
    info: 'status-info',
  }
  return map[severity] || 'status-info'
}

function getStatusText(status: string): string {
  const map: Record<string, string> = {
    active: '活跃',
    acknowledged: '已确认',
    resolved: '已恢复',
    suppressed: '已抑制',
  }
  return map[status] || status
}

function formatTime(t: string): string {
  if (!t) return ''
  try {
    const d = new Date(t)
    const now = new Date()
    const diff = (now.getTime() - d.getTime()) / 1000
    if (diff < 60) return '刚刚'
    if (diff < 3600) return Math.floor(diff/60) + '分钟前'
    if (diff < 86400) return Math.floor(diff/3600) + '小时前'
    return d.toLocaleDateString('zh-CN')
  } catch { return t }
}

function pendingTypeTag(type: string): TagType {
  const map: Record<string, string> = {
    '执行审批': 'warning',
    '待确认资产': 'info',
    '待处理异常': 'danger',
    '待审核报告': 'primary',
  }
  return (map[type] || 'info') as TagType
}

// ─── Lifecycle ───
let resizeHandler: () => void

watch(trendRange, () => {
  if (allJobs.length > 0) {
    computeTrendData(allJobs)
    renderChart()
  }
})

onMounted(async () => {
  await fetchDashboard()
  fetchPlatformHealth()
  await nextTick()
  initChart()
  resizeHandler = () => chartInstance?.resize()
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  chartInstance?.dispose()
  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
})
</script>

<style scoped>
.command-center {
  width: 100%;
}

.metric-row {
  margin-bottom: 0;
}

/* 健康进度条 */
.health-bar-item {
  margin-bottom: 14px;
}

.health-bar-item:last-child {
  margin-bottom: 0;
}

.health-bar-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.health-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.health-dot-healthy { background: var(--autops-success); }
.health-dot-warning { background: var(--autops-warning); }
.health-dot-critical { background: var(--autops-danger); }
.health-dot-unknown { background: var(--autops-info); }

/* 执行统计 */
.exec-stats {
  display: flex;
  gap: 24px;
}

.exec-stat-item {
  flex: 1;
  text-align: center;
  padding: var(--autops-space-md);
  background: var(--autops-bg-2);
  border-radius: var(--autops-radius-md);
}

/* 快捷操作 */
.quick-actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.quick-action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: var(--autops-space-lg) 8px;
  border-radius: var(--autops-radius-md);
  cursor: pointer;
  transition: all 0.2s;
  background: var(--autops-bg-2);
}

.quick-action-btn:hover {
  background: var(--autops-primary-light-5);
  transform: translateY(-2px);
}

.quick-action-btn span {
  font-size: var(--autops-font-12);
  color: var(--autops-text-2);
}

.autops-status-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: var(--autops-radius-sm);
  font-size: var(--autops-font-12);
  font-weight: 500;
  line-height: 20px;
}
.status-failed { background: var(--autops-danger-light); color: var(--autops-danger); }
.status-warning { background: var(--autops-warning-light); color: var(--autops-warning); }
.status-info { background: var(--autops-bg-3); color: var(--autops-info); }
.status-active { background: var(--autops-danger-light); color: var(--autops-danger); }
.status-acknowledged { background: var(--autops-warning-light); color: var(--autops-warning); }
.status-resolved { background: var(--autops-success-light); color: var(--autops-success); }
.status-suppressed { background: var(--autops-bg-3); color: var(--autops-info); }

/* V3 主线卡片 */
.autops-card { cursor: pointer; transition: all 0.2s; }
.autops-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.autops-card-body { display: flex; justify-content: space-around; padding: var(--autops-space-lg) 8px !important; }
.autops-metric-card { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.autops-metric-card-num { font-size: 22px; font-weight: 600; line-height: 1.2; }
.autops-metric-card-label { font-size: var(--autops-font-12); color: var(--autops-info); }
.text-tertiary { color: var(--autops-info); }
.font-12 { font-size: var(--autops-font-12); }

/* 平台健康 */
.platform-health-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.health-item { display: flex; align-items: center; gap: 6px; padding: 6px 0; }
.health-dot-healthy { background: var(--autops-success); }
.health-dot-warning { background: var(--autops-warning); }
.health-dot-error { background: var(--autops-danger); }
.health-dot-offline { background: var(--autops-text-4); }

/* 今日摘要 */
.today-summary { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
.summary-item { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: var(--autops-space-sm); background: var(--autops-bg-2); border-radius: 6px; }
.summary-label { font-size: var(--autops-font-12); color: var(--autops-info); }
.summary-val { font-size: 18px; font-weight: 600; }

/* 优先级 */
.priority-high { color: var(--autops-danger); font-weight: 500; }
.priority-medium { color: var(--autops-warning); font-weight: 500; }
.priority-low { color: var(--autops-success); font-weight: 500; }
</style>
