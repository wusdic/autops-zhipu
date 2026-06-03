<template>
  <div class="notification-bell">
    <el-popover placement="bottom-end" :width="420" trigger="click" @show="loadNotifications">
      <template #reference>
        <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
          <el-button :icon="Bell" circle size="small" />
        </el-badge>
      </template>

      <div class="notification-panel">
        <div class="notification-header">
          <span class="title">通知</span>
          <el-button link type="primary" size="small" @click="markAllRead" :disabled="!unreadCount">全部已读</el-button>
        </div>

        <el-tabs v-model="activeTab" size="small">
          <el-tab-pane label="全部" name="all" />
          <el-tab-pane name="unread">
            <template #label>未读 <el-badge :value="unreadCount" :hidden="!unreadCount" class="tab-badge" /></template>
          </el-tab-pane>
          <el-tab-pane label="告警" name="alert" />
          <el-tab-pane label="审批" name="approval" />
        </el-tabs>

        <div class="notification-list" v-loading="loading">
          <div v-if="!filteredNotifications.length" class="empty-state">
            <el-empty description="暂无通知" :image-size="60" />
          </div>
          <div
            v-for="n in filteredNotifications" :key="n.id"
            class="notification-item"
            :class="{ unread: !n.read_at }"
            @click="handleNotification(n)"
          >
            <div class="notification-icon">
              <el-icon :size="18" :color="iconColor(n.type)">
                <WarningFilled v-if="n.type==='alert'" />
                <CircleCheck v-else-if="n.type==='approval'" />
                <InfoFilled v-else-if="n.type==='info'" />
                <Bell v-else />
              </el-icon>
            </div>
            <div class="notification-content">
              <div class="notification-title">{{ n.title }}</div>
              <div class="notification-desc">{{ n.message }}</div>
              <div class="notification-time">{{ fmtTime(n.created_at) }}</div>
            </div>
            <el-button v-if="!n.read_at" link size="small" @click.stop="markRead(n.id)">已读</el-button>
          </div>
        </div>

        <div class="notification-footer" v-if="notifications.length">
          <el-button link type="primary" @click="viewAll">查看全部通知</el-button>
        </div>
      </div>
    </el-popover>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Bell, WarningFilled, CircleCheck, InfoFilled } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'
import { wsService, WSEvents } from '@/shared/api/websocket'

const router = useRouter()

const notifications = ref<any[]>([])
const loading = ref(false)
const activeTab = ref('all')
const unreadCount = computed(() => notifications.value.filter(n => !n.read_at).length)

const filteredNotifications = computed(() => {
  let result = [...notifications.value]
  if (activeTab.value === 'unread') result = result.filter(n => !n.read_at)
  else if (activeTab.value === 'alert') result = result.filter(n => n.type === 'alert')
  else if (activeTab.value === 'approval') result = result.filter(n => n.type === 'approval')
  return result.slice(0, 20)
})

function fmtTime(t: string) {
  if (!t) return ''
  const d = new Date(t)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff/60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff/3600000)} 小时前`
  return d.toLocaleDateString('zh-CN')
}

function iconColor(type: string) {
  return ({ alert: '#f53f3f', approval: '#ff7d00', info: '#165dff', system: '#86909c' })[type] || '#86909c'
}

async function loadNotifications() {
  loading.value = true
  try {
    const { data } = await api.get(API.NOTIFICATIONS, { params: { page_size: 30 } })
    if (data?.code === 0) notifications.value = data.data?.items || data.data || []
  } catch { /* silent */ }
  finally { loading.value = false }
}

async function markRead(id: string) {
  try {
    await api.patch(API.NOTIFICATION_READ(id))
    const n = notifications.value.find(n => n.id === id)
    if (n) n.read_at = new Date().toISOString()
  } catch { /* silent */ }
}

async function markAllRead() {
  try {
    await api.post(API.NOTIFICATION_READ_ALL)
    notifications.value.forEach(n => { if (!n.read_at) n.read_at = new Date().toISOString() })
  } catch { /* silent */ }
}

function handleNotification(n: any) {
  if (!n.read_at) markRead(n.id)
  if (n.link) router.push(n.link)
  else if (n.type === 'alert' && n.ref_id) router.push(`/alerts/${n.ref_id}`)
  else if (n.type === 'approval' && n.ref_id) router.push(`/executions/${n.ref_id}`)
  else if (n.type === 'ticket' && n.ref_id) router.push(`/tickets/${n.ref_id}`)
}

function viewAll() { router.push('/notifications') }

// WebSocket real-time push
function handleWSMessage(msg: any) {
  if (msg.type === WSEvents.NOTIFICATION || msg.type === WSEvents.ALERT_NEW || msg.type === WSEvents.APPROVAL_REQUEST) {
    notifications.value.unshift({
      id: msg.payload?.id || Date.now().toString(),
      type: msg.type.includes('alert') ? 'alert' : msg.type.includes('approval') ? 'approval' : 'info',
      title: msg.payload?.title || '新通知',
      message: msg.payload?.message || msg.payload?.description || '',
      link: msg.payload?.link,
      ref_id: msg.payload?.ref_id,
      created_at: msg.payload?.created_at || new Date().toISOString(),
      read_at: null,
    })
    ElMessage.info({ message: msg.payload?.title || '新通知', duration: 3000 })
  }
}

let unsubscribe: (() => void) | null = null

onMounted(() => {
  loadNotifications()
  unsubscribe = wsService.onAny(handleWSMessage)
})

onUnmounted(() => { if (unsubscribe) unsubscribe() })
</script>

<style scoped>
.notification-panel { margin: -12px; }
.notification-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; border-bottom: 1px solid #e5e6eb; }
.notification-header .title { font-weight: bold; font-size: 15px; }
.notification-list { max-height: 400px; overflow-y: auto; }
.notification-item { display: flex; align-items: flex-start; gap: 10px; padding: 10px 12px; border-bottom: 1px solid #f2f3f5; cursor: pointer; transition: background 0.2s; }
.notification-item:hover { background: #f7f8fa; }
.notification-item.unread { background: #ecf5ff; }
.notification-item.unread:hover { background: #d9ecff; }
.notification-icon { flex-shrink: 0; margin-top: 2px; }
.notification-content { flex: 1; min-width: 0; }
.notification-title { font-size: 13px; font-weight: 500; color: #1d2129; }
.notification-desc { font-size: 12px; color: #86909c; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.notification-time { font-size: 11px; color: #c9cdd4; margin-top: 4px; }
.empty-state { padding: 20px; }
.notification-footer { padding: 8px 12px; text-align: center; border-top: 1px solid #e5e6eb; }
.tab-badge { margin-left: 4px; }
.tab-badge :deep(.el-badge__content) { font-size: 10px; }
</style>
