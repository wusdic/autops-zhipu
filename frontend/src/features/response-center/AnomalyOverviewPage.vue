<template>
  <div class="page-container">
    <!-- 页面头部 -->
    <div class="autops-page-header">
      <div class="autops-page-title">异常总览</div>
      <el-button type="primary" @click="router.push('/response/anomaly-list')">
        <el-icon><Plus /></el-icon>
        异常列表
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6" v-for="stat in statCards" :key="stat.key">
        <el-card
          shadow="hover"
          class="stat-card"
          :class="{ 'stat-card-clickable': stat.route }"
          v-loading="statsLoading"
          @click="stat.route && router.push(stat.route)"
        >
          <div class="stat-card-inner">
            <div class="stat-icon-wrap" :style="{ background: stat.bg, color: stat.color }">
              <el-icon :size="24"><component :is="stat.icon" /></el-icon>
            </div>
            <el-statistic :title="stat.label" :value="stat.value" class="stat-body" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近异常列表 -->
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">最近异常</span>
          <el-button text type="primary" @click="router.push('/response/anomaly-list')">
            查看全部 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>
      <el-table
        :data="recentAnomalies"
        v-loading="anomaliesLoading"
        stripe
        empty-text="暂无异常记录"
        style="width: 100%"
      >
        <el-table-column prop="title" label="异常标题" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="router.push(`/response/anomaly-list/${row.id}`)">
              {{ row.title || row.name || '-' }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重度" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="severityType(row.severity)" size="small" effect="light">
              {{ severityLabel(row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="asset" label="资产" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ row.asset_name || row.asset || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small" effect="light">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="discovered_at" label="发现时间" width="170">
          <template #default="{ row }">
            <span class="text-muted">{{ formatTime(row.discovered_at || row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="router.push(`/response/anomaly-list/${row.id}`)">
              详情
            </el-button>
            <el-button
              v-if="row.status === 'pending' || row.status === 'open'"
              text
              type="success"
              size="small"
              @click="handleAcknowledge(row)"
            >
              确认
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 快速导航 -->
    <el-row :gutter="16" class="quick-links-row">
      <el-col :span="6" v-for="link in quickLinks" :key="link.label">
        <el-card
          shadow="hover"
          class="quick-link-card"
          @click="router.push(link.route)"
        >
          <div class="quick-link-inner">
            <el-icon :size="32" :color="link.color"><component :is="link.icon" /></el-icon>
            <div class="quick-link-text">
              <div class="quick-link-label">{{ link.label }}</div>
              <div class="quick-link-desc">{{ link.desc }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  ArrowRight,
  Warning,
  CircleCheck,
  Clock,
  CloseBold,
  Connection,
  DataAnalysis,
  MagicStick,
  List,
} from '@element-plus/icons-vue'
import { anomalyService } from '@/shared/api'

const router = useRouter()

// ── 统计卡片 ──
const statsLoading = ref(false)
const statCards = reactive([
  {
    key: 'total',
    label: '异常总数',
    value: 0,
    icon: Warning,
    bg: '#ffece8',
    color: '#f53f3f',
    route: '/response/anomaly-list',
  },
  {
    key: 'pending',
    label: '待处理',
    value: 0,
    icon: Clock,
    bg: '#fff7e8',
    color: '#ff7d00',
    route: '/response/anomaly-list?status=pending',
  },
  {
    key: 'acknowledged',
    label: '已确认',
    value: 0,
    icon: CircleCheck,
    bg: '#e8ffea',
    color: '#00b42a',
    route: '/response/anomaly-list?status=acknowledged',
  },
  {
    key: 'closed',
    label: '已关闭',
    value: 0,
    icon: CloseBold,
    bg: '#e8f3ff',
    color: '#165dff',
    route: '/response/anomaly-list?status=closed',
  },
])

// ── 最近异常 ──
const anomaliesLoading = ref(false)
const recentAnomalies = ref<any[]>([])

// ── 快速导航 ──
const quickLinks = [
  {
    label: '异常列表',
    desc: '查看和管理所有异常',
    icon: List,
    color: '#f53f3f',
    route: '/response/anomaly-list',
  },
  {
    label: '告警关联',
    desc: '查看告警关联分析',
    icon: Connection,
    color: '#165dff',
    route: '/response/alert-correlation',
  },
  {
    label: '影响分析',
    desc: '分析异常影响范围',
    icon: DataAnalysis,
    color: '#ff7d00',
    route: '/response/impact-analysis',
  },
  {
    label: 'AI 诊断',
    desc: '智能诊断异常根因',
    icon: MagicStick,
    color: '#722ed1',
    route: '/response/ai-diagnosis',
  },
]

// ── 严重度映射 ──
const severityMap: Record<string, { type: '' | 'success' | 'warning' | 'danger' | 'info'; label: string }> = {
  critical: { type: 'danger', label: '严重' },
  high: { type: 'danger', label: '高' },
  major: { type: 'danger', label: '高' },
  medium: { type: 'warning', label: '中' },
  warning: { type: 'warning', label: '中' },
  low: { type: 'info', label: '低' },
  minor: { type: 'info', label: '低' },
  info: { type: 'info', label: '信息' },
}

function severityType(severity: string) {
  return severityMap[severity]?.type ?? 'info'
}

function severityLabel(severity: string) {
  return severityMap[severity]?.label ?? severity ?? '-'
}

// ── 状态映射 ──
const statusMap: Record<string, { type: '' | 'success' | 'warning' | 'danger' | 'info'; label: string }> = {
  open: { type: 'danger', label: '待处理' },
  pending: { type: 'danger', label: '待处理' },
  new: { type: 'danger', label: '待处理' },
  acknowledged: { type: 'warning', label: '已确认' },
  processing: { type: 'warning', label: '处理中' },
  in_progress: { type: 'warning', label: '处理中' },
  resolved: { type: 'success', label: '已解决' },
  closed: { type: 'success', label: '已关闭' },
  escalated: { type: 'danger', label: '已升级' },
  cancelled: { type: 'info', label: '已取消' },
}

function statusType(status: string) {
  return statusMap[status]?.type ?? 'info'
}

function statusLabel(status: string) {
  return statusMap[status]?.label ?? status ?? '-'
}

// ── 格式化工具 ──
function formatTime(val: string | null | undefined): string {
  if (!val) return '-'
  try {
    const d = new Date(val)
    if (isNaN(d.getTime())) return val
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return val
  }
}

// ── 确认异常 ──
async function handleAcknowledge(row: any) {
  try {
    await ElMessageBox.confirm(
      `确认处理异常「${row.title || row.name || row.id}」？`,
      '确认异常',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' },
    )
    await anomalyService.acknowledge(row.id)
    ElMessage.success('已确认该异常')
    fetchRecentAnomalies()
    fetchStats()
  } catch (err: any) {
    if (err !== 'cancel') {
      console.error('确认异常失败:', err)
      ElMessage.error('确认异常失败')
    }
  }
}

// ── 数据获取 ──
async function fetchStats() {
  statsLoading.value = true
  try {
    // 先尝试 stats 接口
    try {
      const statsRes = await anomalyService.stats()
      // /api/v1/anomalies/stats returns: { total, by_status: {...}, by_severity: {...} }
      // Response is wrapped: { code: 0, data: { total, by_status, by_severity } }
      const raw = statsRes?.data ?? {}
      const data = raw.data ?? raw

      if (data.total !== undefined) statCards[0].value = data.total
      else if (data.total_count !== undefined) statCards[0].value = data.total_count

      // by_status is a dict like { "open": 5, "acknowledged": 3, "closed": 10 }
      var byStatus: Record<string, number> = data.by_status ?? {}
      // Map pending/open to card[1]
      statCards[1].value = byStatus['pending'] ?? byStatus['open'] ?? byStatus['new'] ?? 0
      // Map acknowledged/processing to card[2]
      statCards[2].value = byStatus['acknowledged'] ?? byStatus['processing'] ?? byStatus['in_progress'] ?? 0
      // Map closed/resolved to card[3]
      statCards[3].value = byStatus['closed'] ?? byStatus['resolved'] ?? 0
    } catch {
      // stats 接口失败，回退到 list 接口获取总数
      const listRes = await anomalyService.list({ page: 1, page_size: 1 })
      const raw = listRes?.data ?? {}
      const ld = raw.data ?? raw
      statCards[0].value = ld?.total ?? ld?.count ?? (Array.isArray(ld) ? ld.length : 0)
    }
  } catch (err: any) {
    console.error('获取异常统计数据失败:', err)
    ElMessage.error('获取统计数据失败')
  } finally {
    statsLoading.value = false
  }
}

async function fetchRecentAnomalies() {
  anomaliesLoading.value = true
  try {
    const res = await anomalyService.list({ page: 1, page_size: 10 })
    const data = res?.data
    if (Array.isArray(data?.items)) {
      recentAnomalies.value = data.items
    } else if (Array.isArray(data?.results)) {
      recentAnomalies.value = data.results
    } else if (Array.isArray(data)) {
      recentAnomalies.value = data
    } else if (data?.data && Array.isArray(data.data)) {
      recentAnomalies.value = data.data
    } else if (data?.records && Array.isArray(data.records)) {
      recentAnomalies.value = data.records
    } else {
      recentAnomalies.value = []
    }
  } catch (err: any) {
    console.error('获取最近异常失败:', err)
    ElMessage.error('获取最近异常失败')
  } finally {
    anomaliesLoading.value = false
  }
}

// ── 生命周期 ──
onMounted(() => {
  fetchStats()
  fetchRecentAnomalies()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
  background: #f7f8fa;
  min-height: 100%;
}

.stat-row {
  margin-bottom: 16px;
}

.stat-card {
  cursor: default;
  transition: transform 0.2s;
}

.stat-card-clickable {
  cursor: pointer;
}

.stat-card-clickable:hover {
  transform: translateY(-2px);
}

.stat-card-inner {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-body {
  flex: 1;
}

.stat-body :deep(.el-statistic__head) {
  font-size: 13px;
  color: #86909c;
  margin-bottom: 4px;
}

.stat-body :deep(.el-statistic__content) {
  font-size: 24px;
  font-weight: 600;
  color: #1d2129;
}

.main-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

.text-muted {
  color: #86909c;
  font-size: 13px;
}

/* 快速导航 */
.quick-links-row {
  margin-bottom: 16px;
}

.quick-link-card {
  cursor: pointer;
  transition: all 0.2s;
}

.quick-link-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.quick-link-inner {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 4px 0;
}

.quick-link-text {
  flex: 1;
}

.quick-link-label {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 2px;
}

.quick-link-desc {
  font-size: 12px;
  color: #86909c;
}
</style>
