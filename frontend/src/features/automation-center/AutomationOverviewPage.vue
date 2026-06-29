<template>
  <div class="autops-page-container">
    <PageHeader title="自动化总览" desc="管理自动化脚本、Playbook 与执行记录">
      <template #actions>
        <el-button type="primary" @click="router.push('/scripts')"><el-icon><Plus /></el-icon>创建脚本</el-button>
      </template>
    </PageHeader>

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
          <div class="metric-value">{{ stat.value }}<span v-if="stat.suffix" class="metric-suffix">{{ stat.suffix }}</span></div>
        </div>
      </el-col>
    </el-row>

    <!-- 最近执行记录 -->
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span class="autops-card-title">最近执行记录</span>
          <el-button plain type="primary" @click="router.push('/executions')">
            查看全部 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>
      <el-table stripe
 :data="recentExecutions"
 v-loading="executionsLoading"
 empty-text="暂无执行记录"
 style="width: 100%"
 >
        <el-table-column prop="name" label="执行名称" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="router.push('/executions/' + row.id)">
              {{ row.name || row.playbook_name || row.script_name || '-' }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="(statusType(row.status)) as TagType" size="small" effect="light">
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
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button plain type="primary" size="small" @click="router.push('/executions/' + row.id)">
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
import type { TagType } from '@/shared/types'
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
import PageHeader from '@/shared/components/PageHeader.vue'
import { execStatusTag, execStatusLabel } from '@/shared/utils/labels'

const router = useRouter()

// ── 统计卡片 ──
const statsLoading = ref(false)
const statCards = reactive([
  {
    key: 'scripts',
    label: '脚本数',
    value: 0,
    icon: Document,
    bgClass: 'bg-brand',
    route: '/scripts',
  },
  {
    key: 'playbooks',
    label: 'Playbook数',
    value: 0,
    icon: VideoPlay,
    bgClass: 'bg-warning',
    route: '/playbooks',
  },
  {
    key: 'executions',
    label: '执行数',
    value: 0,
    icon: List,
    bgClass: 'bg-success',
    route: '/executions',
  },
  {
    key: 'success_rate',
    label: '成功率',
    value: 0,
    suffix: '%',
    icon: CircleCheck,
    bgClass: 'bg-purple',
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
// 执行状态统一取自 labels.ts
const statusType = (status: string): TagType => execStatusTag(status) as TagType
const statusLabel = (status: string): string => execStatusLabel(status)

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
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes())
  } catch {
    return val
  }
}

function formatDuration(row: any): string {
  if (row.duration !== undefined && row.duration !== null) {
    const sec = Number(row.duration)
    if (isNaN(sec)) return row.duration
    if (sec < 60) return sec + 's'
    if (sec < 3600) return Math.floor(sec / 60) + 'm ' + sec % 60 + 's'
    return Math.floor(sec / 3600) + 'h ' + Math.floor((sec % 3600) / 60) + 'm'
  }
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
      // /api/v1/automation/stats returns: { total, completed, failed, pending_approval, running, rolling_back, success_rate }
      const raw = overviewRes?.data
      const od = raw?.data ?? raw ?? {}
      // execution total and success_rate from stats endpoint
      if (od.total !== undefined) statCards[2].value = od.total ?? statCards[2].value
      if (od.success_rate !== undefined) statCards[3].value = Number(od.success_rate)
      // These fields are not returned by the stats endpoint,
      // so we rely on the list endpoints above for script/playbook counts
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
    // Backend wraps: { code: 0, data: { items: [...], total, ... } }
    const raw = res?.data ?? {}
    const data = raw.data ?? raw
    if (Array.isArray(data?.items)) {
      recentExecutions.value = data.items
    } else if (Array.isArray(data?.results)) {
      recentExecutions.value = data.results
    } else if (Array.isArray(data)) {
      recentExecutions.value = data
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
