<template>
  <div class="page-container">
    <!-- 页面头部 -->
    <div class="autops-page-header">
      <div class="autops-page-title">巡检总览</div>
      <div class="autops-page-desc">管理和配置巡检模板、计划与任务</div>
    </div>

    <div style="display: flex; justify-content: flex-end; margin-bottom: 16px;">
      <el-button type="primary" @click="router.push('/inspection/templates')">
        <el-icon><Plus /></el-icon>
        创建模板
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
            <el-statistic :title="stat.label" :value="stat.value" class="stat-body">
              <template #suffix v-if="stat.suffix">{{ stat.suffix }}</template>
            </el-statistic>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近巡检任务 -->
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">最近巡检任务</span>
          <el-button plain type="primary" @click="router.push('/inspection/tasks')">
            查看全部 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>
      <el-table stripe
 :data="recentTasks"
 v-loading="tasksLoading"
52| empty-text="暂无巡检任务"
 style="width: 100%"
 >
        <el-table-column prop="name" label="任务名称" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="router.push('/inspection/' + row.id)">
              {{ row.name || row.template_name || '-' }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small" effect="light">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="asset_names" label="巡检资产" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ formatAssets(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="170">
          <template #default="{ row }">
            <span class="text-muted">{{ formatTime(row.started_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时" width="100" align="center">
          <template #default="{ row }">
            <span>{{ formatDuration(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button plain type="primary" size="small" @click="router.push('/inspection/' + row.id)">
              详情
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
import { ElMessage } from 'element-plus'
import {
  Plus,
  ArrowRight,
  Document,
  Calendar,
  List,
  DataAnalysis,
  Tickets,
} from '@element-plus/icons-vue'
import { inspectionService } from '@/shared/api'

const router = useRouter()

// ── 统计卡片 ──
const statsLoading = ref(false)
const statCards = reactive([
  {
    key: 'templates',
    label: '模板数',
    value: 0,
    icon: Document,
    bg: '#e8f3ff',
    color: '#165dff',
    route: '/inspection/templates',
  },
  {
    key: 'plans',
    label: '计划数',
    value: 0,
    icon: Calendar,
    bg: '#fff7e8',
    color: '#ff7d00',
    route: '/inspection/plans',
  },
  {
    key: 'tasks',
    label: '任务数',
    value: 0,
    icon: List,
    bg: '#e8ffea',
    color: '#00b42a',
    route: '/inspection/tasks',
  },
  {
    key: 'completion_rate',
    label: '完成率',
    value: 0,
    suffix: '%',
    icon: DataAnalysis,
    bg: '#f0e8ff',
    color: '#722ed1',
    route: '/inspection/results',
  },
])

// ── 最近任务 ──
const tasksLoading = ref(false)
const recentTasks = ref<any[]>([])

// ── 快速导航 ──
const quickLinks = [
  {
    label: '巡检模板',
    desc: '管理和配置巡检模板',
    icon: Document,
    color: '#165dff',
    route: '/inspection/templates',
  },
  {
    label: '巡检计划',
    desc: '创建定时巡检计划',
    icon: Calendar,
    color: '#ff7d00',
    route: '/inspection/plans',
  },
  {
    label: '巡检任务',
    desc: '查看所有巡检任务',
    icon: List,
    color: '#00b42a',
    route: '/inspection/tasks',
  },
  {
    label: '巡检报告',
    desc: '查看巡检结果和报告',
    icon: Tickets,
    color: '#722ed1',
    route: '/inspection/reports',
  },
]

// ── 状态映射 ──
const statusMap: Record<string, { type: '' | 'success' | 'warning' | 'danger' | 'info'; label: string }> = {
  completed: { type: 'success', label: '已完成' },
  success: { type: 'success', label: '已完成' },
  failed: { type: 'danger', label: '失败' },
  running: { type: 'warning', label: '执行中' },
  pending: { type: 'info', label: '待执行' },
  cancelled: { type: 'info', label: '已取消' },
  timeout: { type: 'danger', label: '超时' },
}

function statusType(status: string) {
  return statusMap[status]?.type ?? 'info'
}

function statusLabel(status: string) {
  return statusMap[status]?.label ?? status
}

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

function formatAssets(row: any): string {
  if (row.asset_names && Array.isArray(row.asset_names)) {
    return row.asset_names.join(', ') || '-'
  }
  if (row.asset_name) return row.asset_name
  if (row.asset_count !== undefined) return row.asset_count + ' 个资产'
  return '-'
}

function formatDuration(row: any): string {
  if (row.duration !== undefined && row.duration !== null) {
    const sec = Number(row.duration)
    if (isNaN(sec)) return row.duration
    if (sec < 60) return sec + 's'
    if (sec < 3600) return Math.floor(sec / 60) + 'm ' + sec % 60 + 's'
    return Math.floor(sec / 3600) + 'h ' + Math.floor((sec % 3600) / 60) + 'm'
  }
  // 尝试从 started_at / finished_at 计算
  if (row.started_at && row.finished_at) {
    const diff = new Date(row.finished_at).getTime() - new Date(row.started_at).getTime()
    if (diff > 0) {
      const sec = Math.round(diff / 1000)
      if (sec < 60) return sec + 's'
      if (sec < 3600) return Math.floor(sec / 60) + 'm ' + sec % 60 + 's'
      return Math.floor(sec / 3600) + 'h ' + Math.floor((sec % 3600) / 60) + 'm'
    }
  }
  return '-'
}

// ── 数据获取 ──
async function fetchStats() {
  statsLoading.value = true
  try {
    // 并行请求获取各计数
    const [templatesRes, plansRes, tasksRes] = await Promise.allSettled([
      inspectionService.listTemplates({ page: 1, page_size: 1 }),
      inspectionService.listPlans({ page: 1, page_size: 1 }),
      inspectionService.listTasks({ page: 1, page_size: 1 }),
    ])

    // 解析模板总数
    if (templatesRes.status === 'fulfilled') {
      const data = templatesRes.value?.data
      statCards[0].value = data?.total ?? data?.count ?? (data?.items?.length ?? 0)
    }

    // 解析计划总数
    if (plansRes.status === 'fulfilled') {
      const data = plansRes.value?.data
      statCards[1].value = data?.total ?? data?.count ?? (data?.items?.length ?? 0)
    }

    // 解析任务总数 & 完成率
    if (tasksRes.status === 'fulfilled') {
      const data = tasksRes.value?.data
      const total = data?.total ?? data?.count ?? 0
      statCards[2].value = total

      // 尝试从 overview 获取完成率
      if (data?.completion_rate !== undefined) {
        statCards[3].value = Number(data.completion_rate)
      } else if (data?.stats?.completion_rate !== undefined) {
        statCards[3].value = Number(data.stats.completion_rate)
      }
    }

    // 尝试获取 overview 统计（补充完成率等）
    try {
      const overviewRes = await inspectionService.overview()
      // /api/v1/inspection/stats returns: { tasks: {...}, templates: {...}, plans: {...}, results: {...} }
      const raw = overviewRes?.data
      const od = raw?.data ?? raw ?? {}
      if (od.templates) statCards[0].value = od.templates.total ?? statCards[0].value
      if (od.plans) statCards[1].value = od.plans.total ?? statCards[1].value
      if (od.tasks) {
        statCards[2].value = od.tasks.total ?? statCards[2].value
        // Compute completion rate from tasks
        var taskTotal = od.tasks.total ?? 0
        var taskCompleted = od.tasks.completed ?? 0
        if (taskTotal > 0) {
          statCards[3].value = Math.round((taskCompleted / taskTotal) * 100)
        }
      }
    } catch {
      // overview 接口可选，忽略错误
    }
  } catch (err: any) {
    console.error('获取巡检统计数据失败:', err)
    ElMessage.error('获取统计数据失败')
  } finally {
    statsLoading.value = false
  }
}

async function fetchRecentTasks() {
  tasksLoading.value = true
  try {
    const res = await inspectionService.listTasks({ page: 1, page_size: 10 })
    const data = res?.data
    if (Array.isArray(data?.items)) {
      recentTasks.value = data.items
    } else if (Array.isArray(data?.results)) {
      recentTasks.value = data.results
    } else if (Array.isArray(data)) {
      recentTasks.value = data
    } else if (data?.data && Array.isArray(data.data)) {
      recentTasks.value = data.data
    } else {
      recentTasks.value = []
    }
  } catch (err: any) {
    console.error('获取最近巡检任务失败:', err)
    ElMessage.error('获取最近任务失败')
  } finally {
    tasksLoading.value = false
  }
}

// ── 生命周期 ──
onMounted(() => {
  fetchStats()
  fetchRecentTasks()
})
</script>

<style scoped>


.stat-row {
  margin-bottom: 16px;
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
