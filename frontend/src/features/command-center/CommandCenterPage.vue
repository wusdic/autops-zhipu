<template>
  <div class="command-center">
    <!-- ─── 统计卡片行 ─── -->
    <el-row :gutter="16" class="metric-row">
      <el-col :xs="12" :sm="8" :md="4">
        <div class="autops-metric-card" @click="navigateTo('/alerts?severity=critical')">
          <div class="metric-icon" style="background: #ffece8; color: #f53f3f">
            <el-icon size="20"><AlarmClock /></el-icon>
          </div>
          <div class="metric-label">严重告警</div>
          <div class="metric-value" style="color: #f53f3f">{{ stats.criticalAlerts }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <div class="autops-metric-card" @click="navigateTo('/alerts')">
          <div class="metric-icon" style="background: #fff7e8; color: #ff7d00">
            <el-icon size="20"><Warning /></el-icon>
          </div>
          <div class="metric-label">活跃告警</div>
          <div class="metric-value" style="color: #ff7d00">{{ stats.activeAlerts }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <div class="autops-metric-card" @click="navigateTo('/assets')">
          <div class="metric-icon" style="background: #e8f3ff; color: #165dff">
            <el-icon size="20"><Box /></el-icon>
          </div>
          <div class="metric-label">资产总数</div>
          <div class="metric-value">{{ stats.totalAssets }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <div class="autops-metric-card" @click="navigateTo('/executions')">
          <div class="metric-icon" style="background: #e8f3ff; color: #165dff">
            <el-icon size="20"><VideoPlay /></el-icon>
          </div>
          <div class="metric-label">执行中任务</div>
          <div class="metric-value">{{ stats.runningExecutions }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <div class="autops-metric-card" @click="navigateTo('/events')">
          <div class="metric-icon" style="background: #f2f3f5; color: #86909c">
            <el-icon size="20"><Bell /></el-icon>
          </div>
          <div class="metric-label">今日事件</div>
          <div class="metric-value">{{ stats.todayEvents }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <div class="autops-metric-card" @click="navigateTo('/executions?status=awaiting_approval')">
          <div class="metric-icon" style="background: #fff7e8; color: #ff7d00">
            <el-icon size="20"><Clock /></el-icon>
          </div>
          <div class="metric-label">待审批</div>
          <div class="metric-value" style="color: #ff7d00">{{ stats.pendingApprovals }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- ─── 内容区: 左大右小 ─── -->
    <el-row :gutter="16" style="margin-top: 16px">
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
            <el-button text type="primary" @click="navigateTo('/alerts')">
              查看全部 →
            </el-button>
          </div>
          <div class="autops-card-body" style="padding: 0">
            <el-table
              :data="recentAlerts"
              stripe
              size="default"
              :max-height="300"
              @row-click="(row: any) => navigateTo(`/alerts/${row.id}`)"
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
                  <span class="autops-status-tag" :class="`status-${row.status}`">
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
                <span :class="`health-dot health-dot-${item.key}`"></span>
                <span class="font-14">{{ item.label }}</span>
                <span class="font-12 text-tertiary" style="margin-left: auto">{{ item.count }}</span>
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
                <div class="font-20" :style="{ color: execStats.successRate >= 95 ? '#00b42a' : execStats.successRate >= 80 ? '#ff7d00' : '#f53f3f' }">
                  {{ execStats.successRate }}%
                </div>
              </div>
              <div class="exec-stat-item">
                <div class="font-12 text-tertiary mb-xs">今日执行</div>
                <div class="font-20">{{ execStats.todayCount }}</div>
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
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'

const router = useRouter()

// ─── Stats ───
const stats = reactive({
  criticalAlerts: 0,
  activeAlerts: 0,
  totalAssets: 0,
  runningExecutions: 0,
  todayEvents: 0,
  pendingApprovals: 0,
})

const recentAlerts = ref<any[]>([])
const trendRange = ref('24h')
const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const execStats = reactive({
  successRate: 0,
  todayCount: 0,
})

const healthData = ref([
  { key: 'healthy', label: '健康', count: 0, percent: 0, color: '#00b42a' },
  { key: 'warning', label: '告警', count: 0, percent: 0, color: '#ff7d00' },
  { key: 'critical', label: '故障', count: 0, percent: 0, color: '#f53f3f' },
  { key: 'unknown', label: '未知', count: 0, percent: 0, color: '#86909c' },
])

// ─── API ───
async function fetchDashboard() {
  try {
    const token = localStorage.getItem('autops_token')
    if (!token) return
    const H = { Authorization: `Bearer ${token}` }

    // 并发请求
    const [alertsRes, assetsRes, execRes] = await Promise.all([
      fetch('/api/v1/alerts?page_size=5', { headers: H }),
      fetch('/api/v1/assets?page_size=1', { headers: H }),
      fetch('/api/v1/executions?page_size=1', { headers: H }),
    ])

    if (alertsRes.ok) {
      const d = await alertsRes.json()
      const items = d?.data?.items || []
      recentAlerts.value = items
      const all = d?.data?.total || 0
      stats.activeAlerts = items.filter((a: any) => a.status === 'active').length
      stats.criticalAlerts = items.filter((a: any) => a.severity === 'critical').length
    }

    if (assetsRes.ok) {
      const d = await assetsRes.json()
      stats.totalAssets = d?.data?.total || 0
      // Health distribution
      const allItems = d?.data?.items || []
      healthData.value[0].count = allItems.filter((a: any) => a.health_status === 'healthy').length
      healthData.value[1].count = allItems.filter((a: any) => a.health_status === 'warning').length
      healthData.value[2].count = allItems.filter((a: any) => a.health_status === 'critical').length
      healthData.value[3].count = allItems.filter((a: any) => !['healthy','warning','critical'].includes(a.health_status)).length
      const total = healthData.value.reduce((s, h) => s + h.count, 0)
      healthData.value.forEach(h => {
        h.percent = total > 0 ? Math.round(h.count / total * 100) : 0
      })
    }

    if (execRes.ok) {
      const d = await execRes.json()
      stats.runningExecutions = (d?.data?.items || []).filter((e: any) =>
        ['pending', 'approved', 'running', 'dry_running'].includes(e.status)
      ).length
      stats.pendingApprovals = (d?.data?.items || []).filter((e: any) =>
        e.status === 'awaiting_approval'
      ).length
    }
  } catch (e) {
    console.error('Dashboard fetch error:', e)
  }
}

// ─── Chart ───
function initChart() {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)

  const hours = trendRange.value === '24h' ? 24 : 7
  const xData: string[] = []
  const yData: number[] = []
  if (trendRange.value === '24h') {
    for (let i = hours - 1; i >= 0; i--) {
      const d = new Date(Date.now() - i * 3600000)
      xData.push(`${d.getHours()}:00`)
      yData.push(Math.round(92 + Math.random() * 7))
    }
  } else {
    for (let i = hours - 1; i >= 0; i--) {
      const d = new Date(Date.now() - i * 86400000)
      xData.push(`${d.getMonth()+1}/${d.getDate()}`)
      yData.push(Math.round(90 + Math.random() * 9))
    }
  }

  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 16, bottom: 30 },
    xAxis: {
      type: 'category',
      data: xData,
      axisLabel: { color: '#86909c', fontSize: 11 },
      axisLine: { lineStyle: { color: '#e5e6eb' } },
    },
    yAxis: {
      type: 'value',
      min: 80,
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
    if (diff < 3600) return `${Math.floor(diff/60)}分钟前`
    if (diff < 86400) return `${Math.floor(diff/3600)}小时前`
    return d.toLocaleDateString('zh-CN')
  } catch { return t }
}

// ─── Lifecycle ───
let resizeHandler: () => void

onMounted(async () => {
  await fetchDashboard()
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

.health-dot-healthy { background: #00b42a; }
.health-dot-warning { background: #ff7d00; }
.health-dot-critical { background: #f53f3f; }
.health-dot-unknown { background: #86909c; }

/* 执行统计 */
.exec-stats {
  display: flex;
  gap: 24px;
}

.exec-stat-item {
  flex: 1;
  text-align: center;
  padding: 12px;
  background: #f7f8fa;
  border-radius: 8px;
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
  padding: 16px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: #f7f8fa;
}

.quick-action-btn:hover {
  background: #e8f3ff;
  transform: translateY(-2px);
}

.quick-action-btn span {
  font-size: 12px;
  color: #4e5969;
}

.autops-status-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  line-height: 20px;
}
.status-failed { background: #ffece8; color: #f53f3f; }
.status-warning { background: #fff7e8; color: #ff7d00; }
.status-info { background: #f2f3f5; color: #86909c; }
.status-active { background: #ffece8; color: #f53f3f; }
.status-acknowledged { background: #fff7e8; color: #ff7d00; }
.status-resolved { background: #e8ffea; color: #00b42a; }
.status-suppressed { background: #f2f3f5; color: #86909c; }
</style>
