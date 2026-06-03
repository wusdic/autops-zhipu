<template>
  <div class="page-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>自动化总览</h2>
      <el-button type="primary" @click="router.push('/scripts')">
        <el-icon><Plus /></el-icon>
        创建脚本
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

    <!-- 最近执行记录 -->
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">最近执行记录</span>
          <el-button text type="primary" @click="router.push('/executions')">
            查看全部 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>
      <el-table
        :data="recentExecutions"
        v-loading="executionsLoading"
        stripe
        empty-text="暂无执行记录"
        style="width: 100%"
      >
        <el-table-column prop="name" label="执行名称" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="router.push(`/executions/${row.id}`)">
              {{ row.name || row.playbook_name || row.script_name || '-' }}
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
        <el-table-column prop="trigger_type" label="触发方式" width="110" align="center">
          <template #default="{ row }">
            <span>{{ triggerLabel(row.trigger_type || row.trigger) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="170">
          <template #default="{ row }">
            <span class="text-muted">{{ formatTime(row.started_at || row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时" width="100" align="center">
          <template #default="{ row }">
            <span>{{ formatDuration(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="router.push(`/executions/${row.id}`)">
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
  VideoPlay,
  List,
  CircleCheck,
  Checked,
  Stamp,
} from '@element-plus/icons-vue'
import { automationService } from '@/shared/api'

const router = useRouter()

// ── 统计卡片 ──
const statsLoading = ref(false)
const statCards = reactive([
  {
    key: 'scripts',
    label: '脚本数',
    value: 0,
    icon: Document,
    bg: '#e8f3ff',
    color: '#165dff',
    route: '/scripts',
  },
  {
    key: 'playbooks',
    label: 'Playbook数',
    value: 0,
    icon: VideoPlay,
    bg: '#fff7e8',
    color: '#ff7d00',
    route: '/playbooks',
  },
  {
    key: 'executions',
    label: '执行数',
    value: 0,
    icon: List,
    bg: '#e8ffea',
    color: '#00b42a',
    route: '/executions',
  },
  {
    key: 'success_rate',
    label: '成功率',
    value: 0,
    suffix: '%',
    icon: CircleCheck,
    bg: '#f0e8ff',
    color: '#722ed1',
    route: '/executions',
  },
])

// ── 最近执行记录 ──
const executionsLoading = ref(false)
const recentExecutions = ref<any[]>([])

// ── 快速导航 ──
const quickLinks = [
  {
    label: '脚本库',
    desc: '管理自动化脚本',
    icon: Document,
    color: '#165dff',
    route: '/scripts',
  },
  {
    label: 'Playbook',
    desc: '编排自动化剧本',
    icon: VideoPlay,
    color: '#ff7d00',
    route: '/playbooks',
  },
  {
    label: '执行历史',
    desc: '查看所有执行记录',
    icon: List,
    color: '#00b42a',
    route: '/executions',
  },
  {
    label: '审批中心',
    desc: '处理待审批任务',
    icon: Stamp,
    color: '#722ed1',
    route: '/approvals',
  },
]

// ── 状态映射 ──
const statusMap: Record<string, { type: '' | 'success' | 'warning' | 'danger' | 'info'; label: string }> = {
  completed: { type: 'success', label: '已完成' },
  success: { type: 'success', label: '成功' },
  failed: { type: 'danger', label: '失败' },
  running: { type: 'warning', label: '执行中' },
  pending: { type: 'info', label: '待执行' },
  cancelled: { type: 'info', label: '已取消' },
  timeout: { type: 'danger', label: '超时' },
  paused: { type: 'warning', label: '已暂停' },
  waiting_approval: { type: 'warning', label: '待审批' },
  rolled_back: { type: 'info', label: '已回滚' },
}

function statusType(status: string) {
  return statusMap[status]?.type ?? 'info'
}

function statusLabel(status: string) {
  return statusMap[status]?.label ?? status
}

// ── 触发方式映射 ──
const triggerMap: Record<string, string> = {
  manual: '手动触发',
  auto: '自动触发',
  schedule: '定时触发',
  alert: '告警触发',
  event: '事件触发',
  policy: '策略触发',
  api: 'API 触发',
}

function triggerLabel(trigger: string | undefined): string {
  if (!trigger) return '-'
  return triggerMap[trigger] ?? trigger
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

function formatDuration(row: any): string {
  if (row.duration !== undefined && row.duration !== null) {
    const sec = Number(row.duration)
    if (isNaN(sec)) return row.duration
    if (sec < 60) return `${sec}s`
    if (sec < 3600) return `${Math.floor(sec / 60)}m ${sec % 60}s`
    return `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m`
  }
  if (row.started_at && row.finished_at) {
    const diff = new Date(row.finished_at).getTime() - new Date(row.started_at).getTime()
    if (diff > 0) {
      const sec = Math.round(diff / 1000)
      if (sec < 60) return `${sec}s`
      if (sec < 3600) return `${Math.floor(sec / 60)}m ${sec % 60}s`
      return `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m`
    }
  }
  return '-'
}

// ── 数据获取 ──
async function fetchStats() {
  statsLoading.value = true
  try {
    // 并行请求获取各计数
    const [scriptsRes, playbooksRes, executionsRes] = await Promise.allSettled([
      automationService.listScripts({ page: 1, page_size: 1 }),
      automationService.listPlaybooks({ page: 1, page_size: 1 }),
      automationService.listExecutions({ page: 1, page_size: 1 }),
    ])

    // 解析脚本总数
    if (scriptsRes.status === 'fulfilled') {
      const data = scriptsRes.value?.data
      statCards[0].value = data?.total ?? data?.count ?? (data?.items?.length ?? 0)
    }

    // 解析 Playbook 总数
    if (playbooksRes.status === 'fulfilled') {
      const data = playbooksRes.value?.data
      statCards[1].value = data?.total ?? data?.count ?? (data?.items?.length ?? 0)
    }

    // 解析执行总数 & 成功率
    if (executionsRes.status === 'fulfilled') {
      const data = executionsRes.value?.data
      statCards[2].value = data?.total ?? data?.count ?? 0

      if (data?.success_rate !== undefined) {
        statCards[3].value = Number(data.success_rate)
      } else if (data?.stats?.success_rate !== undefined) {
        statCards[3].value = Number(data.stats.success_rate)
      }
    }

    // 尝试获取 overview 统计（补充成功率等）
    try {
      const overviewRes = await automationService.overview()
      const od = overviewRes?.data
      if (od) {
        if (od.script_count !== undefined) statCards[0].value = od.script_count
        else if (od.scripts_count !== undefined) statCards[0].value = od.scripts_count

        if (od.playbook_count !== undefined) statCards[1].value = od.playbook_count
        else if (od.playbooks_count !== undefined) statCards[1].value = od.playbooks_count

        if (od.execution_count !== undefined) statCards[2].value = od.execution_count
        else if (od.executions_count !== undefined) statCards[2].value = od.executions_count

        if (od.success_rate !== undefined) statCards[3].value = Number(od.success_rate)
      }
    } catch {
      // overview 接口可选，忽略错误
    }
  } catch (err: any) {
    console.error('获取自动化统计数据失败:', err)
    ElMessage.error('获取统计数据失败')
  } finally {
    statsLoading.value = false
  }
}

async function fetchRecentExecutions() {
  executionsLoading.value = true
  try {
    const res = await automationService.listExecutions({ page: 1, page_size: 10 })
    const data = res?.data
    if (Array.isArray(data?.items)) {
      recentExecutions.value = data.items
    } else if (Array.isArray(data?.results)) {
      recentExecutions.value = data.results
    } else if (Array.isArray(data)) {
      recentExecutions.value = data
    } else if (data?.data && Array.isArray(data.data)) {
      recentExecutions.value = data.data
    } else {
      recentExecutions.value = []
    }
  } catch (err: any) {
    console.error('获取最近执行记录失败:', err)
    ElMessage.error('获取执行记录失败')
  } finally {
    executionsLoading.value = false
  }
}

// ── 生命周期 ──
onMounted(() => {
  fetchStats()
  fetchRecentExecutions()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
  background: #f7f8fa;
  min-height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1d2129;
  margin: 0;
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
