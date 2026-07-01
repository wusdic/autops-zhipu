<template>
  <div class="autops-page-container">
    <PageHeader title="工单报告" desc="工单处理统计与报表导出">
      <template #actions>
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" @change="fetchData" />
        <el-button type="primary" @click="generateReport" :loading="generating">
          <el-icon><Document /></el-icon> 生成报表
        </el-button>
        <el-button @click="exportData"><el-icon><Download /></el-icon> 导出</el-button>
      </template>
    </PageHeader>

    <!-- 概要统计 -->
    <el-row :gutter="16" class="mb-lg">
      <el-col :xs="12" :sm="6" v-for="stat in summaryStats" :key="stat.label">
        <div class="autops-metric-card">
          <div class="metric-icon" :class="stat.bg"><el-icon size="20"><component :is="stat.icon" /></el-icon></div>
          <div class="metric-label">{{ stat.label }}</div>
          <div class="metric-value">{{ stat.value }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 按类型分布 -->
    <el-row :gutter="16" class="mb-lg">
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
    <div class="autops-card mb-lg">
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
            <div class="trend-bar" :style="{ height: barHeight(d.created) + 'px', background: '#165dff' }" :title="'新建: ' + d.created"></div>
            <div class="trend-bar" :style="{ height: barHeight(d.resolved) + 'px', background: '#00b42a' }" :title="'解决: ' + d.resolved"></div>
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
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, markRaw } from 'vue'
import { Document, Download, Tickets, CircleCheckFilled, Loading, WarningFilled } from '@element-plus/icons-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import { ElMessage } from 'element-plus'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

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
    { label: '工单总数', value: total, icon: markRaw(Tickets), bg: 'bg-brand' },
    { label: '已解决', value: resolved, icon: markRaw(CircleCheckFilled), bg: 'bg-success' },
    { label: '处理中', value: pending, icon: markRaw(Loading), bg: 'bg-warning' },
    { label: '超时工单', value: overdue, icon: markRaw(WarningFilled), bg: 'bg-danger' },
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
  // 真实数据：达标=未超时(sla_breached=false)，超时=sla_breached=true
  const levels = ['紧急', '高', '中', '低']
  return levels.map(level => {
    const matching = tickets.value.filter(t => (t.priority || '').includes(level) || (t.severity || '').includes(level))
    const total = matching.length
    const breached = matching.filter(t => t.sla_breached).length
    const met = total - breached
    return { level, total, met, breached, rate: total > 0 ? Math.round(met / total * 100) : 100 }
  })
})

const handlerRanking = computed(() => {
  // 真实数据：按处理人聚合已解决工单数与平均处理时长；无满意度数据来源，故不再展示
  const handlerMap: Record<string, { resolved: number; hours: number; hoursCnt: number }> = {}
  tickets.value.filter(t => t.handler && (t.status === 'resolved' || t.status === 'closed')).forEach(t => {
    if (!handlerMap[t.handler]) handlerMap[t.handler] = { resolved: 0, hours: 0, hoursCnt: 0 }
    handlerMap[t.handler].resolved++
    if (t.resolve_hours != null) { handlerMap[t.handler].hours += t.resolve_hours; handlerMap[t.handler].hoursCnt++ }
  })
  return Object.entries(handlerMap)
    .map(([handler, data]) => ({
      handler,
      resolved: data.resolved,
      avg_hours: data.hoursCnt ? (data.hours / data.hoursCnt).toFixed(1) : '-',
    }))
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
        // 处理时长：优先后端字段，否则用 已解决时间-创建时间 计算（小时）；都没有则 null
        resolve_hours: t.resolve_hours
          ?? ((t.resolved_at && t.created_at)
            ? Math.round((new Date(t.resolved_at).getTime() - new Date(t.created_at).getTime()) / 3600000)
            : null),
        sla_breached: t.sla_breached || false,
      }))
      fetchTrend()
    }
  } catch (e) {
    console.error('Fetch ticket report error:', e)
  }
}

function fetchTrend() {
  // 真实趋势：按工单 created_at / (resolved_at|已解决状态的 updated_at) 的日期聚合
  const days = trendPeriod.value === '7d' ? 7 : 30
  const now = new Date()
  const createdBy: Record<string, number> = {}
  const resolvedBy: Record<string, number> = {}
  tickets.value.forEach(t => {
    if (t.created_at) {
      const d = String(t.created_at).slice(0, 10)
      createdBy[d] = (createdBy[d] || 0) + 1
    }
    const rt = t.resolved_at || (['resolved', 'closed'].includes(t.status) ? t.updated_at : null)
    if (rt) {
      const d = String(rt).slice(0, 10)
      resolvedBy[d] = (resolvedBy[d] || 0) + 1
    }
  })
  trendData.value = Array.from({ length: days }, (_, i) => {
    const d = new Date(now.getTime() - (days - 1 - i) * 86400000).toISOString().slice(0, 10)
    return { date: d, created: createdBy[d] || 0, resolved: resolvedBy[d] || 0 }
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

async function exportData() {
  try {
    await api.post(API.EXPORTS, { name: '工单报表', export_type: 'ticket_report', format: 'csv' })
    ElMessage.success('导出任务已提交，请到「导出中心」下载')
  } catch (e: any) {
    ElMessage.error(e.message || '导出失败')
  }
}

onMounted(() => { fetchData(); fetchTrend() })
</script>

<style scoped>
.trend-bars { display: flex; align-items: flex-end; gap: 4px; height: 200px; padding: 0 8px; }
.trend-bar-group { flex: 1; display: flex; gap: 2px; align-items: flex-end; flex-direction: column; position: relative; justify-content: flex-end; align-items: center; }
.trend-bar { width: 16px; border-radius: 3px 3px 0 0; min-height: 2px; }
.trend-label { font-size: 10px; color: var(--autops-info); position: absolute; bottom: -18px; white-space: nowrap; }
</style>
