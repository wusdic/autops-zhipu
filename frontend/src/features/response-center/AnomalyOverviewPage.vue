<template>
  <div class="autops-page-container">
    <!-- 页面头部（嵌入到异常中心页时由宿主统一展示，隐藏自身） -->
    <div class="autops-page-header autops-page-header--between" v-if="!embedded">
      <div>
        <div class="autops-page-title">异常总览</div>
        <div class="autops-page-desc">监控和处理系统异常事件</div>
      </div>
      <div class="autops-header-actions">
        <el-button type="primary" @click="router.push('/anomaly/list')"><el-icon><Plus /></el-icon>异常列表</el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="metric-row">
      <el-col :span="6" v-for="stat in statCards" :key="stat.key">
        <div
          class="autops-metric-card"
          :class="{ 'is-clickable': stat.route }"
          v-loading="statsLoading"
          @click="stat.route && router.push(stat.route)"
        >
          <div class="metric-icon" :class="stat.bgClass">
            <el-icon :size="20"><component :is="stat.icon" /></el-icon>
          </div>
          <div class="metric-label">{{ stat.label }}</div>
          <div class="metric-value">{{ stat.value }}<span v-if="(stat as any).suffix" class="metric-suffix">{{ (stat as any).suffix }}</span></div>
        </div>
      </el-col>
    </el-row>

    <!-- 最近异常列表 -->
    <el-card class="main-card">
      <template #header>
        <div class="autops-card-header">
          <span class="autops-card-title">最近异常</span>
          <el-button plain type="primary" @click="router.push('/response/anomaly-list')">
            查看全部 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>
      <el-table stripe
 :data="recentAnomalies"
 v-loading="anomaliesLoading"empty-text="暂无异常记录"
 style="width: 100%"
 >
        <el-table-column prop="title" label="异常标题" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="router.push('/response/anomaly-list/' + row.id)">
              {{ row.title || row.name || '-' }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重度" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="(severityType(row.severity)) as TagType" size="small" effect="light">
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
            <el-tag :type="(statusType(row.status)) as TagType" size="small" effect="light">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="discovered_at" label="发现时间" width="170">
          <template #default="{ row }">
            <span class="text-muted">{{ formatTime(row.discovered_at || row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button plain type="primary" size="small" @click="router.push('/response/anomaly-list/' + row.id)">
              详情
            </el-button>
            <el-button
              v-if="row.status === 'pending' || row.status === 'open'"
              plain
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
import type { TagType } from '@/shared/types'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

defineProps<{ embedded?: boolean }>()
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
import {
  severityTagType, severityLabel as severityLabelFn, anomalyStatusTag, anomalyStatusLabel,
} from '@/shared/utils/labels'

const router = useRouter()

// ── 统计卡片 ──
const statsLoading = ref(false)
const statCards = reactive([
  {
    key: 'total',
    label: '异常总数',
    value: 0,
    icon: Warning,
    bgClass: 'bg-danger',
    route: '/response/anomaly-list',
  },
  {
    key: 'pending',
    label: '待处理',
    value: 0,
    icon: Clock,
    bgClass: 'bg-warning',
    route: '/response/anomaly-list?status=pending',
  },
  {
    key: 'acknowledged',
    label: '已确认',
    value: 0,
    icon: CircleCheck,
    bgClass: 'bg-success',
    route: '/response/anomaly-list?status=acknowledged',
  },
  {
    key: 'closed',
    label: '已关闭',
    value: 0,
    icon: CloseBold,
    bgClass: 'bg-brand',
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

// 严重度/异常状态统一取自 labels.ts
const severityType = (severity: string): TagType => severityTagType(severity) as TagType
const severityLabel = (severity: string): string => severityLabelFn(severity)
const statusType = (status: string): TagType => anomalyStatusTag(status) as TagType
const statusLabel = (status: string): string => anomalyStatusLabel(status)

// ── 格式化工具 ──
function formatTime(val: string | null | undefined): string {
  if (!val) return '-'
  try {
    const d = new Date(val)
    if (isNaN(d.getTime())) return val
    const pad = (n: number) => String(n).padStart(2, '0')
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes())
  } catch {
    return val
  }
}

// ── 确认异常 ──
async function handleAcknowledge(row: any) {
  try {
    await ElMessageBox.confirm(
      '确认处理异常「' + row.title || row.name || row.id + '」？',
      '确认异常',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' },
    )
    await anomalyService.acknowledge(row.id)
    ElMessage.success('已确认该异常')
    fetchRecentAnomalies()
    fetchStats()
  } catch (err: any) {
    if (err !== 'cancel' && err?.action !== 'cancel' && err?.message !== 'cancel') {
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
.main-card {
  margin-bottom: var(--autops-space-lg);
}
.text-muted {
  color: var(--autops-info);
  font-size: var(--autops-font-13);
}

/* 快速导航 */
.quick-links-row {
  margin-bottom: var(--autops-space-lg);
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
  padding: var(--autops-space-xs) 0;
}

.quick-link-text {
  flex: 1;
}

.quick-link-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--autops-text-1);
  margin-bottom: 2px;
}

.quick-link-desc {
  font-size: var(--autops-font-12);
  color: var(--autops-info);
}
</style>
