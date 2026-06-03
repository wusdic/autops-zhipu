<template>
  <div class="page-container">
    <!-- 页面头部 -->
    <div class="autops-page-header">
      <div class="autops-page-title">报表总览</div>
      <div class="autops-page-desc">查看各类报表的生成状态和统计数据</div>
    </div>
    <div style="display: flex; justify-content: flex-end; margin-bottom: 16px">
      <el-button type="primary" @click="router.push('/report-audit/generate')">
        <el-icon><Plus /></el-icon>
        生成报告
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

    <!-- 最近报告任务 -->
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">最近报告任务</span>
          <el-button text type="primary" @click="router.push('/report-audit/tasks')">
            查看全部 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>
      <el-table stripe
 :data="recentTasks"
 v-loading="tasksLoading"empty-text="暂无报告任务"
 style="width: 100%"
 >
        <el-table-column prop="title" label="报告名" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="router.push(`/report-audit/tasks/${row.id}`)">
              {{ row.title || row.name || '-' }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="typeTagType(row.type)" size="small" effect="light">
              {{ typeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small" effect="light">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="generated_at" label="生成时间" width="170">
          <template #default="{ row }">
            <span class="text-muted">{{ formatTime(row.generated_at || row.created_at || row.finished_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时" width="100" align="center">
          <template #default="{ row }">
            <span>{{ formatDuration(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'completed' || row.status === 'success'"
              text
              type="primary"
              size="small"
              @click="handlePreview(row)"
            >
              预览
            </el-button>
            <el-button
              v-if="row.status === 'completed' || row.status === 'success'"
              text
              type="success"
              size="small"
              @click="handleDownload(row)"
            >
              下载
            </el-button>
            <el-button
              v-if="row.status === 'failed'"
              text
              type="warning"
              size="small"
              @click="handleRetry(row)"
            >
              重试
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
  Document,
  Tickets,
  FolderOpened,
  Loading,
  DataAnalysis,
  List,
  Clock,
  CircleCheck,
  Search,
} from '@element-plus/icons-vue'
import { reportService } from '@/shared/api'

const router = useRouter()

// ── 统计卡片 ──
const statsLoading = ref(false)
const statCards = reactive([
  {
    key: 'templates',
    label: '报告模板',
    value: 0,
    icon: Document,
    bg: '#e8f3ff',
    color: '#165dff',
    route: '/report-audit/templates',
  },
  {
    key: 'tasks',
    label: '报告任务',
    value: 0,
    icon: Tickets,
    bg: '#fff7e8',
    color: '#ff7d00',
    route: '/report-audit/tasks',
  },
  {
    key: 'archived',
    label: '已归档',
    value: 0,
    icon: FolderOpened,
    bg: '#e8ffea',
    color: '#00b42a',
    route: '/report-audit/archive',
  },
  {
    key: 'generating',
    label: '生成中',
    value: 0,
    icon: Loading,
    bg: '#f0e8ff',
    color: '#722ed1',
    route: '/report-audit/tasks?status=generating',
  },
])

// ── 最近报告任务 ──
const tasksLoading = ref(false)
const recentTasks = ref<any[]>([])

// ── 快速导航 ──
const quickLinks = [
  {
    label: '报告模板',
    desc: '管理和配置报告模板',
    icon: Document,
    color: '#165dff',
    route: '/report-audit/templates',
  },
  {
    label: '报告任务',
    desc: '查看所有生成任务',
    icon: List,
    color: '#ff7d00',
    route: '/report-audit/tasks',
  },
  {
    label: '报告归档',
    desc: '浏览已归档的报告',
    icon: FolderOpened,
    color: '#00b42a',
    route: '/report-audit/archive',
  },
  {
    label: '审计查询',
    desc: '查询审计相关记录',
    icon: Search,
    color: '#722ed1',
    route: '/report-audit/audit-query',
  },
]

// ── 类型映射 ──
const typeMap: Record<string, { type: '' | 'success' | 'warning' | 'danger' | 'info'; label: string }> = {
  inspection: { type: 'primary', label: '巡检报告' },
  asset: { type: 'success', label: '资产台账' },
  sla: { type: 'warning', label: 'SLA报告' },
  audit: { type: 'danger', label: '审计报告' },
  operation: { type: 'info', label: '运维报告' },
  custom: { type: 'info', label: '自定义报告' },
  daily: { type: '', label: '日报' },
  weekly: { type: 'warning', label: '周报' },
  monthly: { type: 'success', label: '月报' },
}

function typeTagType(t: string) {
  return typeMap[t]?.type ?? 'info'
}

function typeLabel(t: string) {
  return typeMap[t]?.label ?? t ?? '-'
}

// ── 状态映射 ──
const statusMap: Record<string, { type: '' | 'success' | 'warning' | 'danger' | 'info'; label: string }> = {
  pending: { type: 'info', label: '待生成' },
  queued: { type: 'info', label: '队列中' },
  generating: { type: 'warning', label: '生成中' },
  running: { type: 'warning', label: '生成中' },
  in_progress: { type: 'warning', label: '生成中' },
  completed: { type: 'success', label: '已完成' },
  success: { type: 'success', label: '已完成' },
  failed: { type: 'danger', label: '生成失败' },
  error: { type: 'danger', label: '生成失败' },
  archived: { type: 'success', label: '已归档' },
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

function formatDuration(row: any): string {
  if (row.duration !== undefined && row.duration !== null) {
    const sec = Number(row.duration)
    if (isNaN(sec)) return row.duration
    if (sec < 60) return `${sec}s`
    if (sec < 3600) return `${Math.floor(sec / 60)}m ${sec % 60}s`
    return `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m`
  }
  // 尝试从 started_at / finished_at 计算
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

// ── 操作处理 ──
function handlePreview(row: any) {
  router.push(`/report-audit/tasks/${row.id}`)
}

async function handleDownload(row: any) {
  try {
    const res = await reportService.download(row.id)
    const blob = new Blob([res.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${row.title || row.name || 'report'}.pdf`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载已开始')
  } catch (err: any) {
    console.error('下载报告失败:', err)
    ElMessage.error('下载报告失败')
  }
}

async function handleRetry(row: any) {
  try {
    await ElMessageBox.confirm(
      `确认重新生成报告「${row.title || row.name || row.id}」？`,
      '重新生成',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' },
    )
    await reportService.generate({ template_id: row.template_id, title: row.title || row.name })
    ElMessage.success('已重新提交生成任务')
    fetchRecentTasks()
    fetchStats()
  } catch (err: any) {
    if (err !== 'cancel') {
      console.error('重新生成失败:', err)
      ElMessage.error('重新生成失败')
    }
  }
}

// ── 数据获取 ──
async function fetchStats() {
  statsLoading.value = true
  try {
    // 并行请求获取各计数
    const [templatesRes, tasksRes, overviewRes] = await Promise.allSettled([
      reportService.listTemplates({ page: 1, page_size: 1 }),
      reportService.listTasks({ page: 1, page_size: 1 }),
      reportService.overview(),
    ])

    // 解析模板总数
    if (templatesRes.status === 'fulfilled') {
      const data = templatesRes.value?.data
      statCards[0].value = data?.total ?? data?.count ?? (data?.items?.length ?? 0)
    }

    // 解析任务总数
    if (tasksRes.status === 'fulfilled') {
      const data = tasksRes.value?.data
      const total = data?.total ?? data?.count ?? 0
      statCards[1].value = total
    }

    // 解析 overview 统计（补充完整数据）
    // /api/v1/report/stats returns: { templates, tasks: {...}, archives: {...} }
    if (overviewRes.status === 'fulfilled') {
      const raw = overviewRes.value?.data
      const wrapper = raw?.data ?? raw ?? {}
      const data = wrapper.data ?? wrapper
      // templates is a number
      if (data.templates !== undefined) statCards[0].value = data.templates
      // tasks is an object with total
      if (data.tasks && data.tasks.total !== undefined) statCards[1].value = data.tasks.total
      // archives is an object with total
      if (data.archives && data.archives.total !== undefined) statCards[2].value = data.archives.total
      // generating/running count
      if (data.tasks && data.tasks.running !== undefined) statCards[3].value = data.tasks.running
      else if (data.tasks && data.tasks.pending !== undefined) statCards[3].value = data.tasks.pending
    }
  } catch (err: any) {
    console.error('获取报表统计数据失败:', err)
    ElMessage.error('获取统计数据失败')
  } finally {
    statsLoading.value = false
  }
}

async function fetchRecentTasks() {
  tasksLoading.value = true
  try {
    const res = await reportService.listTasks({ page: 1, page_size: 10 })
    const data = res?.data
    if (Array.isArray(data?.items)) {
      recentTasks.value = data.items
    } else if (Array.isArray(data?.results)) {
      recentTasks.value = data.results
    } else if (Array.isArray(data)) {
      recentTasks.value = data
    } else if (data?.data && Array.isArray(data.data)) {
      recentTasks.value = data.data
    } else if (data?.records && Array.isArray(data.records)) {
      recentTasks.value = data.records
    } else {
      recentTasks.value = []
    }
  } catch (err: any) {
    console.error('获取最近报告任务失败:', err)
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
