<template>
  <el-drawer v-model="visible" title="通知中心" direction="rtl" size="420px" :append-to-body="true">
    <!-- 通知类型Tab -->
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="全部" name="all">
        <template #label>
          全部 <el-badge v-if="counts.all > 0" :value="counts.all" :max="99" class="tab-badge" />
        </template>
      </el-tab-pane>
      <el-tab-pane label="告警" name="alert">
        <template #label>
          告警 <el-badge v-if="counts.alert > 0" :value="counts.alert" :max="99" class="tab-badge" />
        </template>
      </el-tab-pane>
      <el-tab-pane label="执行" name="execution">
        <template #label>
          执行 <el-badge v-if="counts.execution > 0" :value="counts.execution" :max="99" class="tab-badge" />
        </template>
      </el-tab-pane>
      <el-tab-pane label="审批" name="approval">
        <template #label>
          审批 <el-badge v-if="counts.approval > 0" :value="counts.approval" :max="99" class="tab-badge" />
        </template>
      </el-tab-pane>
      <el-tab-pane label="系统" name="system">
        <template #label>
          系统 <el-badge v-if="counts.system > 0" :value="counts.system" :max="99" class="tab-badge" />
        </template>
      </el-tab-pane>
    </el-tabs>

    <!-- 操作栏 -->
    <div class="action-bar" v-if="notifications.length > 0">
      <el-button link type="primary" size="small" @click="markAllRead">全部已读</el-button>
      <el-button link type="danger" size="small" @click="clearAll">清空</el-button>
    </div>

    <!-- 通知列表 -->
    <div class="notification-list">
      <div
        v-for="item in filteredNotifications"
        :key="item.id"
        class="notification-item"
        :class="{ unread: !item.read }"
        @click="handleNotificationClick(item)"
      >
        <div class="notification-icon" :style="{ background: getIconBg(item.type) }">
          <el-icon :size="16" color="#fff">
            <component :is="getIcon(item.type)" />
          </el-icon>
        </div>
        <div class="notification-content">
          <div class="notification-title">
            <span>{{ item.title }}</span>
            <el-tag v-if="getPriorityTag(item.priority)" :type="getPriorityTag(item.priority)" size="small">
              {{ item.priority }}
            </el-tag>
          </div>
          <div class="notification-desc">{{ item.description }}</div>
          <div class="notification-meta">
            <span class="notification-time">{{ item.time }}</span>
            <span v-if="item.source" class="notification-source">{{ item.source }}</span>
          </div>
        </div>
      </div>

      <el-empty v-if="filteredNotifications.length === 0" description="暂无通知" :image-size="80" />
    </div>

    <!-- 底部 -->
    <template #footer>
      <el-button type="primary" link @click="$router.push('/alerts')">查看所有告警</el-button>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Warning, Cpu, Checked, Bell, InfoFilled } from '@element-plus/icons-vue'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: boolean): void }>()

const router = useRouter()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const activeTab = ref('all')
const counts = ref({ all: 5, alert: 3, execution: 1, approval: 1, system: 0 })

const notifications = ref([
  { id: 1, type: 'alert', title: 'CPU 使用率超过阈值', description: 'web-server-01 CPU使用率达到 95%，已触发告警', time: '2分钟前', source: '告警规则', priority: '高', read: false },
  { id: 2, type: 'alert', title: '磁盘空间不足', description: 'db-server-03 /data 分区使用率 92%', time: '15分钟前', source: '告警规则', priority: '高', read: false },
  { id: 3, type: 'alert', title: 'SSL 证书即将过期', description: 'api.example.com 证书将在7天后过期', time: '1小时前', source: '巡检任务', priority: '中', read: false },
  { id: 4, type: 'execution', title: '自动化执行完成', description: '策略「磁盘清理」执行成功，释放空间 15GB', time: '30分钟前', source: '自动化中心', priority: '低', read: false },
  { id: 5, type: 'approval', title: '高危策略待审批', description: '用户 ops 提交了「数据库重启」策略，需要审批', time: '5分钟前', source: '审批中心', priority: '高', read: false },
])

const filteredNotifications = computed(() => {
  if (activeTab.value === 'all') return notifications.value
  return notifications.value.filter(n => n.type === activeTab.value)
})

const iconMap: Record<string, any> = { alert: Warning, execution: Cpu, approval: Checked, system: InfoFilled }
const iconBgMap: Record<string, string> = { alert: '#f53f3f', execution: '#165dff', approval: '#ff7d00', system: '#86909c' }
const getIcon = (t: string) => iconMap[t] || Bell
const getIconBg = (t: string) => iconBgMap[t] || '#86909c'
const getPriorityTag = (p: string) => p === '高' ? 'danger' : p === '中' ? 'warning' : p === '低' ? 'info' : ''

function handleTabChange() {}

function handleNotificationClick(item: any) {
  item.read = true
  counts.value.all = notifications.value.filter(n => !n.read).length
  if (item.type === 'alert') router.push('/alerts')
  else if (item.type === 'execution') router.push('/executions')
  else if (item.type === 'approval') router.push('/approvals')
  visible.value = false
}

function markAllRead() {
  notifications.value.forEach(n => n.read = true)
  counts.value = { all: 0, alert: 0, execution: 0, approval: 0, system: 0 }
  ElMessage.success('已全部标记已读')
}

function clearAll() {
  notifications.value = []
  counts.value = { all: 0, alert: 0, execution: 0, approval: 0, system: 0 }
  ElMessage.success('已清空通知')
}
</script>

<style scoped>
.action-bar {
  display: flex; justify-content: flex-end; gap: 8px;
  margin-bottom: var(--autops-space-sm); padding: 0 4px;
}
.notification-list { max-height: calc(100vh - 250px); overflow-y: auto; }
.notification-item {
  display: flex; gap: 12px; padding: var(--autops-space-md) 8px;
  border-bottom: 1px solid var(--autops-bg-3); cursor: pointer; transition: background 0.15s;
}
.notification-item:hover { background: var(--autops-bg-2); }
.notification-item.unread { background: var(--autops-primary-light-5); }
.notification-item.unread:hover { background: var(--autops-primary-light-5); }
.notification-icon {
  width: 32px; height: 32px; border-radius: var(--autops-radius-md);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.notification-content { flex: 1; min-width: 0; }
.notification-title {
  display: flex; align-items: center; gap: 8px;
  font-size: var(--autops-font-14); font-weight: 500; color: var(--autops-text-1);
}
.notification-desc {
  font-size: var(--autops-font-13); color: var(--autops-text-2); margin-top: 4px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.notification-meta {
  display: flex; gap: 12px; margin-top: 6px;
  font-size: var(--autops-font-12); color: var(--autops-info);
}
.tab-badge { margin-left: 4px; }
</style>
