<template>
  <el-popover placement="bottom-end" :width="380" trigger="click" @show="loadTasks">
    <template #reference>
      <el-badge :value="runningCount" :hidden="runningCount === 0" :max="99">
        <el-button :icon="Loading" circle size="small" :loading="loading" />
      </el-badge>
    </template>

    <div class="task-progress-panel">
      <div class="task-header">
        <span class="title">后台任务</span>
        <el-button v-if="tasks.length" link type="primary" size="small" @click="clearCompleted">清除已完成</el-button>
      </div>

      <div class="task-list" v-loading="loading">
        <div v-if="!tasks.length" class="empty-state">
          <el-empty description="暂无后台任务" :image-size="60" />
        </div>
        <div v-for="task in tasks" :key="task.id" class="task-item" @click="handleTaskClick(task)">
          <div class="task-icon">
            <el-icon :size="16" :color="statusColor(task.status)">
              <Loading v-if="task.status === 'running'" />
              <CircleCheck v-else-if="task.status === 'completed'" />
              <CircleClose v-else-if="task.status === 'failed'" />
              <Clock v-else />
            </el-icon>
          </div>
          <div class="task-content">
            <div class="task-title">
              <span>{{ task.title || task.name || task.type }}</span>
              <el-tag :type="statusTagType(task.status)" size="small">{{ statusLabel(task.status) }}</el-tag>
            </div>
            <div v-if="task.progress !== undefined" class="task-progress">
              <el-progress :percentage="task.progress" :status="task.status === 'failed' ? 'exception' : undefined" :stroke-width="4" />
            </div>
            <div class="task-time">{{ formatTime(task.created_at) }}</div>
          </div>
        </div>
      </div>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, CircleCheck, CircleClose, Clock } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'
import { THEME_COLORS } from '@/shared/config'

const router = useRouter()
const loading = ref(false)
const tasks = ref<any[]>([])
let pollTimer: ReturnType<typeof setInterval> | null = null

const runningCount = computed(() => tasks.value.filter(t => t.status === 'running' || t.status === 'pending').length)

function statusColor(status: string) {
  return THEME_COLORS.STATUS[status] || THEME_COLORS.GRAY
}

function statusTagType(status: string) {
  return { running: '', completed: 'success', failed: 'danger', pending: 'warning' }[status] || 'info'
}

function statusLabel(status: string) {
  return { running: '执行中', completed: '已完成', failed: '失败', pending: '等待中', cancelled: '已取消' }[status] || status
}

function formatTime(ts: string) {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return d.toLocaleDateString()
}

async function loadTasks() {
  loading.value = true
  try {
    const res = await api.get(API.EXECUTIONS, { params: { page: 1, page_size: 10 } })
    const data = res.data?.data
    tasks.value = data?.items || data || []
  } catch { tasks.value = [] }
  finally { loading.value = false }
}

function clearCompleted() {
  tasks.value = tasks.value.filter(t => t.status === 'running' || t.status === 'pending')
}

function handleTaskClick(task: any) {
  if (task.id) {
    router.push('/executions/' + task.id).catch(() => {})
  }
}

// Auto-poll every 30s if there are running tasks
function startPoll() {
  pollTimer = setInterval(() => {
    if (runningCount.value > 0) loadTasks()
  }, 30000)
}

onMounted(() => {
  loadTasks()
  startPoll()
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.task-progress-panel { min-height: 100px; }
.task-header {
  display: flex; justify-content: space-between; align-items: center;
  padding-bottom: 8px; border-bottom: 1px solid #f2f3f5; margin-bottom: 8px;
}
.task-header .title { font-size: 14px; font-weight: 600; color: #1d2129; }
.task-list { max-height: 400px; overflow-y: auto; }
.task-item {
  display: flex; gap: 10px; padding: 10px 0;
  border-bottom: 1px solid #f7f8fa; cursor: pointer; transition: background 0.15s;
}
.task-item:hover { background: #f7f8fa; }
.task-item:last-child { border-bottom: none; }
.task-icon { flex-shrink: 0; display: flex; align-items: flex-start; padding-top: 2px; }
.task-content { flex: 1; min-width: 0; }
.task-title { display: flex; justify-content: space-between; align-items: center; gap: 8px; font-size: 13px; }
.task-progress { margin-top: 6px; }
.task-time { font-size: 12px; color: #86909c; margin-top: 4px; }
</style>
