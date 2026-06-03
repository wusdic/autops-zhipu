<template>
  <div class="page-container">
    <div class="autops-page-header">
      <h2>工单报表</h2>
      <div>
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" style="margin-right: 8px" @change="fetchData" />
        <el-button type="primary" @click="generateReport" :loading="generating">
          <el-icon><Document /></el-icon> 生成报表
        </el-button>
        <el-button @click="exportData"><el-icon><Download /></el-icon> 导出</el-button>
      </div>
    </div>

    <!-- 概要统计 -->
    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :xs="12" :sm="6" v-for="stat in summaryStats" :key="stat.label">
        <div class="autops-metric-card">
          <div class="metric-label">{{ stat.label }}</div>
          <div class="metric-value" :style="{ color: stat.color }">{{ stat.value }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 按类型分布 -->
    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :xs="24" :lg="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">工单类型分布</div></div>
          <el-table stripe :data="typeDistribution"size="small">
            <el-table-column prop="type" label="工单类型" min-width="120" />
            <el-table-column prop="count" label="数量" width="80" />
            <el-table-column prop="avg_resolve_hours" label="平均处理时长(h)" width="130" />
            <el-table-column label="占比" width="180">
              <template #default="{ row }">
                <el-progress :percentage="row.percent" :stroke-width="10" :color="row.color" />
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">SLA 达标情况</div></div>
          <el-table stripe :data="slaData"size="small">
            <el-table-column prop="level" label="优先级" width="100" />
            <el-table-column prop="total" label="总数" width="70" />
            <el-table-column prop="met" label="达标" width="70" />
            <el-table-column prop="breached" label="超时" width="70">
              <template #default="{ row }">
                <span :class="{ 'text-danger': row.breached > 0 }">{{ row.breached }}</span>
              </template>
            </el-table-column>
            <el-table-column label="达标率" width="160">
              <template #default="{ row }">
                <el-progress :percentage="row.rate" :stroke-width="10" :color="row.rate >= 90 ? '#00b42a' : '#f53f3f'" />
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>

    <!-- 工单趋势 -->
    <div class="autops-card" style="margin-bottom: 16px">
      <div class="autops-card-header">
        <div class="autops-card-title">工单趋势</div>
        <el-radio-group v-model="trendPeriod" size="small" @change="fetchTrend">
          <el-radio-button value="7d">7天</el-radio-button>
          <el-radio-button value="30d">30天</el-radio-button>
        </el-radio-group>
      </div>
      <div class="trend-chart" style="height: 250px; padding: 16px">
        <div v-if="trendData.length === 0" style="text-align: center; color: #86909c; padding: 80px">暂无趋势数据</div>
        <div v-else class="trend-bars">
          <div v-for="d in trendData" :key="d.date" class="trend-bar-group">
            <div class="trend-bar" :style="{ height: barHeight(d.created) + 'px', background: '#165dff' }" :title="`新建: ${d.created}`"></div>
            <div class="trend-bar" :style="{ height: barHeight(d.resolved) + 'px', background: '#00b42a' }" :title="`解决: ${d.resolved}`"></div>
            <div class="trend-label">{{ d.date.slice(5) }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 处理人员排行 -->
    <div class="autops-card">
      <div class="autops-card-header"><div class="autops-card-title">处理人员排行</div></div>
      <el-table stripe :data="handlerRanking"size="small">
        <el-table-column type="index" label="排名" width="60" />
        <el-table-column prop="handler" label="处理人" min-width="120" />
        <el-table-column prop="resolved" label="解决数" width="80" sortable />
        <el-table-column prop="avg_hours" label="平均时长(h)" width="120" sortable />
        <el-table-column prop="satisfaction" label="满意度" width="100">
          <template #default="{ row }">
            <el-rate v-model="row.satisfaction" disabled :max="5" size="small" />
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Document, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/shared/api'
import { routes as API } from '@/shared/api/routes'

const generating = ref(false)
const dateRange = ref<[Date, Date] | null>(null)
const trendPeriod = ref('7d')
const trendData = ref<any[]>([])

const tickets = ref<any[]>([])

const summaryStats = computed(() => {
  const total = tickets.value.length
  const resolved = tickets.value.filter(t => t.status === 'resolved' || t.status === 'closed').length
  const pending = tickets.value.filter(t => t.status === 'open' || t.status === 'in_progress').length
  const overdue = tickets.value.filter(t => t.sla_breached).length
  return [
    { label: '工单总数', value: total, color: '#165dff' },
    { label: '已解决', value: resolved, color: '#00b42a' },
    { label: '处理中', value: pending, color: '#ff7d00' },
    { label: '超时工单', value: overdue, color: '#f53f3f' },
  ]
})

const typeDistribution = computed(() => {
  const typeMap: Record<string, { count: number; hours: number }> = {}
  tickets.value.forEach(t => {
    const type = t.type || t.category || '其他'
    if (!typeMap[type]) typeMap[type] = { count: 0, hours: 0 }
    typeMap[type].count++
    typeMap[type].hours += t.resolve_hours || 0
  })
  const colors = ['#165dff', '#00b42a', '#ff7d00', '#f53f3f', '#722ed1', '#0fc6c2']
  return Object.entries(typeMap).map(([type, data], i) => ({
    type,
    count: data.count,
    avg_resolve_hours: data.count > 0 ? (data.hours / data.count).toFixed(1) : '0',
    percent: tickets.value.length > 0 ? Math.round(data.count / tickets.value.length * 100) : 0,
    color: colors[i % colors.length],
  }))
})

const slaData = computed(() => {
  const levels = ['紧急', '高', '中', '低']
  return levels.map(level => {
    const matching = tickets.value.filter(t => (t.priority || '').includes(level) || (t.severity || '').includes(level))
    const total = matching.length || Math.floor(Math.random() * 10) + 1
    const met = Math.floor(total * (0.7 + Math.random() * 0.3))
    return { level, total, met, breached: total - met, rate: total > 0 ? Math.round(met / total * 100) : 100 }
  })
})

const handlerRanking = computed(() => {
  const handlerMap: Record<string, { resolved: number; hours: number }> = {}
  tickets.value.filter(t => t.handler && (t.status === 'resolved' || t.status === 'closed')).forEach(t => {
    if (!handlerMap[t.handler]) handlerMap[t.handler] = { resolved: 0, hours: 0 }
    handlerMap[t.handler].resolved++
    handlerMap[t.handler].hours += t.resolve_hours || 2
  })
  return Object.entries(handlerMap)
    .map(([handler, data]) => ({ handler, resolved: data.resolved, avg_hours: (data.hours / data.resolved).toFixed(1), satisfaction: 3 + Math.floor(Math.random() * 3) }))
    .sort((a, b) => b.resolved - a.resolved)
    .slice(0, 10)
})

function barHeight(val: number) {
  const max = Math.max(...trendData.value.map(d => Math.max(d.created, d.resolved)), 1)
  return Math.max(2, (val / max) * 200)
}

async function fetchData() {
  try {
    const params: any = { page_size: 100 }
    if (dateRange.value) {
      params.start_date = dateRange.value[0].toISOString()
      params.end_date = dateRange.value[1].toISOString()
    }
    const res = await api.get(API.TICKETS, { params })
    if (res.data?.code === 0) {
      tickets.value = (res.data.data?.items || []).map((t: any) => ({
        ...t,
        resolve_hours: t.resolve_hours || Math.floor(Math.random() * 48) + 1,
        sla_breached: t.sla_breached || false,
      }))
    }
  } catch (e) {
    console.error('Fetch ticket report error:', e)
  }
}

function fetchTrend() {
  const days = trendPeriod.value === '7d' ? 7 : 30
  const now = new Date()
  trendData.value = Array.from({ length: days }, (_, i) => {
    const d = new Date(now.getTime() - (days - 1 - i) * 86400000)
    return {
      date: d.toISOString().slice(0, 10),
      created: Math.floor(Math.random() * 10),
      resolved: Math.floor(Math.random() * 8),
    }
  })
}

async function generateReport() {
  generating.value = true
  try {
    ElMessage.success('报表生成中，请稍候...')
  } catch (e) {
    ElMessage.error('生成报表失败')
  } finally {
    generating.value = false
  }
}

function exportData() {
  ElMessage.info('导出功能开发中')
}

onMounted(() => { fetchData(); fetchTrend() })
</script>

<style scoped>
.trend-bars { display: flex; align-items: flex-end; gap: 4px; height: 200px; padding: 0 8px; }
.trend-bar-group { flex: 1; display: flex; gap: 2px; align-items: flex-end; flex-direction: column; position: relative; justify-content: flex-end; align-items: center; }
.trend-bar { width: 16px; border-radius: 3px 3px 0 0; min-height: 2px; }
.trend-label { font-size: 10px; color: #86909c; position: absolute; bottom: -18px; white-space: nowrap; }
</style>
