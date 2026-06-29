<template>
  <div class="autops-page-container">
    <PageHeader title="故障工作台" desc="集中处理进行中的故障事件">
      <template #actions>
        <el-select v-model="severityFilter" placeholder="严重级别" style="width: 120px" clearable @change="fetchIncidents">
          <el-option label="紧急" value="critical" />
          <el-option label="严重" value="major" />
          <el-option label="一般" value="minor" />
          <el-option label="提示" value="info" />
        </el-select>
        <el-select v-model="statusFilter" placeholder="状态" style="width: 120px" clearable @change="fetchIncidents">
          <el-option label="待处理" value="open" />
          <el-option label="处理中" value="in_progress" />
          <el-option label="已解决" value="resolved" />
          <el-option label="已关闭" value="closed" />
        </el-select>
        <el-button @click="fetchIncidents"><el-icon><Refresh /></el-icon> 刷新</el-button>
      </template>
    </PageHeader>

    <el-row :gutter="16">
      <!-- 左栏: 事件列表 -->
      <el-col :xs="24" :lg="10">
        <div class="autops-card" style="height: calc(100vh - 160px); overflow-y: auto">
          <div v-if="loading" style="text-align: center; padding: 40px">
            <el-icon class="is-loading" :size="24"><Loading /></el-icon>
            <p>加载中...</p>
          </div>
          <div v-else-if="incidents.length === 0" style="text-align: center; padding: 40px; color: #86909c">
            <el-icon :size="48"><CircleCheck /></el-icon>
            <p>当前无活跃事件</p>
          </div>
          <div v-else>
            <div
              v-for="inc in incidents"
              :key="inc.id"
              class="incident-card"
              :class="{ active: selectedId === inc.id }"
              @click="selectIncident(inc)"
            >
              <div class="incident-header">
                <SeverityBadge :severity="inc.severity" size="small" />
                <StatusBadge :status="inc.status" />
              </div>
              <div class="incident-title">{{ inc.title || inc.alert_name || '事件 #' + inc.id?.slice(0,8) }}</div>
              <div class="incident-meta">
                <span v-if="inc.asset_name"><el-icon><Box /></el-icon> {{ inc.asset_name }}</span>
                <span><el-icon><Clock /></el-icon> {{ formatTime(inc.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 右栏: 事件详情 -->
      <el-col :xs="24" :lg="14">
        <div class="autops-card" style="min-height: calc(100vh - 160px)">
          <div v-if="!selectedIncident" style="text-align: center; padding: 80px; color: #86909c">
            <el-icon :size="48"><InfoFilled /></el-icon>
            <p>请从左侧选择一个事件查看详情</p>
          </div>
          <template v-else>
            <!-- 详情头 -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px">
              <h3 style="margin: 0">{{ selectedIncident.title || '事件详情' }}</h3>
              <div>
                <SeverityBadge :severity="selectedIncident.severity" />
                <StatusBadge :status="selectedIncident.status" style="margin-left: 8px" />
              </div>
            </div>

            <!-- 基本信息 -->
            <el-descriptions :column="2" border size="small" class="mb-lg">
              <el-descriptions-item label="资产">{{ selectedIncident.asset_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="来源">{{ selectedIncident.source || '-' }}</el-descriptions-item>
              <el-descriptions-item label="发生时间">{{ formatTime(selectedIncident.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="持续时间">{{ selectedIncident.duration || '计算中...' }}</el-descriptions-item>
              <el-descriptions-item label="关联告警" :span="2">{{ selectedIncident.alert_count || 0 }} 条</el-descriptions-item>
            </el-descriptions>

            <!-- 时间线 -->
            <h4 style="margin-bottom: 8px">处置时间线</h4>
            <el-timeline v-if="timeline.length > 0" style="margin-bottom: 16px; max-height: 250px; overflow-y: auto">
              <el-timeline-item
                v-for="(evt, idx) in timeline"
                :key="idx"
                :timestamp="formatTime(evt.created_at)"
                :type="evt.type === 'error' ? 'danger' : evt.type === 'success' ? 'success' : 'primary'"
                placement="top"
              >
                {{ evt.content || evt.description }}
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无时间线记录" :image-size="60" />

            <!-- 证据列表 -->
            <h4 style="margin-bottom: 8px">关联证据</h4>
            <el-table stripe :data="evidenceList"size="small" v-if="evidenceList.length > 0" class="mb-lg">
              <el-table-column prop="type" label="类型" width="100">
                <template #default="{ row }">
                  <el-tag size="small">{{ row.type }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="title" label="描述" show-overflow-tooltip />
              <el-table-column prop="created_at" label="时间" width="160">
                <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
              </el-table-column>
            </el-table>
            <el-empty v-else description="暂无证据" :image-size="60" />

            <!-- 工作流操作按钮 -->
            <el-divider>处置操作</el-divider>
            <div style="display: flex; gap: 8px; flex-wrap: wrap">
              <el-button type="primary" @click="navToAIFromAnomaly(selectedIncident.id)">
                <el-icon><MagicStick /></el-icon> AI 诊断
              </el-button>
              <el-button type="warning" @click="navToRemediationFromAnomaly(selectedIncident.id)">
                <el-icon><VideoPlay /></el-icon> 故障处置
              </el-button>
              <el-button type="success" @click="navToTicketFromAnomaly(selectedIncident.id)">
                <el-icon><Tickets /></el-icon> 创建工单
              </el-button>
              <el-button @click="navToPolicyFromAnomaly(selectedIncident.id)">
                <el-icon><Setting /></el-icon> 匹配策略
              </el-button>
              <el-button v-if="selectedIncident.status === 'in_progress'" type="success" plain @click="resolveIncident">
                <el-icon><CircleCheck /></el-icon> 标记解决
              </el-button>
              <el-button v-if="selectedIncident.status === 'resolved'" type="info" plain @click="closeIncident">
                <el-icon><Close /></el-icon> 关闭事件
              </el-button>
            </div>
          </template>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { TagType } from '@/shared/types'
import { Refresh, Loading, Box, Clock, InfoFilled, CircleCheck, MagicStick, VideoPlay, Tickets, Setting, Close } from '@element-plus/icons-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import SeverityBadge from '@/shared/components/SeverityBadge.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'
import { useWorkflowNav } from '@/shared/composables/useWorkflowNav'

const { navToAIFromAnomaly, navToRemediationFromAnomaly, navToTicketFromAnomaly, navToPolicyFromAnomaly } = useWorkflowNav()

const loading = ref(false)
const incidents = ref<any[]>([])
const selectedIncident = ref<any>(null)
const selectedId = ref('')
const timeline = ref<any[]>([])
const evidenceList = ref<any[]>([])
const severityFilter = ref('')
const statusFilter = ref('')

async function fetchIncidents() {
  loading.value = true
  try {
    const params: any = { page_size: 100 }
    if (severityFilter.value) params.severity = severityFilter.value
    if (statusFilter.value) params.status = statusFilter.value
    const [alertRes, eventRes] = await Promise.all([
      api.get(API.ALERTS, { params }),
      api.get(API.EVENTS, { params: { page_size: 50 } }),
    ])
    const alertData = alertRes.data
    if (alertData?.code === 0) {
      incidents.value = (alertData.data?.items || []).map((a: any) => ({
        ...a,
        title: a.alert_name || a.name || a.title,
        source: a.source || '告警',
        status: a.status === 'firing' ? 'open' : a.status === 'resolved' ? 'resolved' : a.status || 'open',
        asset_name: a.asset_name || a.asset?.name,
        alert_count: 1,
      }))
    }
  } catch (e) {
    console.error('Fetch incidents error:', e)
    ElMessage.error('获取事件列表失败')
  } finally {
    loading.value = false
  }
}

async function selectIncident(inc: any) {
  selectedIncident.value = inc
  selectedId.value = inc.id
  // Fetch timeline
  try {
    const res = await api.get(API.EVENTS, { params: { alert_id: inc.id, page_size: 50 } })
    const data = res.data
    if (data?.code === 0) {
      timeline.value = (data.data?.items || []).map((e: any) => ({
        created_at: e.created_at,
        content: e.description || e.message || e.event_type,
        type: e.severity === 'critical' ? 'error' : 'primary',
      }))
      evidenceList.value = (data.data?.items || []).slice(0, 10).map((e: any) => ({
        type: e.event_type || 'event',
        title: e.description || e.message || '-',
        created_at: e.created_at,
      }))
    }
  } catch (e) {
    timeline.value = []
    evidenceList.value = []
  }
}

async function resolveIncident() {
  try {
    await ElMessageBox.confirm('确认标记该事件为已解决？', '确认')
    await api.patch(API.ALERTS + '/' + selectedId.value, { status: 'resolved' })
    ElMessage.success('事件已标记为已解决')
    fetchIncidents()
  } catch { /* cancelled */ }
}

async function closeIncident() {
  try {
    await ElMessageBox.confirm('确认关闭该事件？', '确认')
    await api.patch(API.ALERTS + '/' + selectedId.value, { status: 'closed' })
    ElMessage.success('事件已关闭')
    fetchIncidents()
  } catch { /* cancelled */ }
}

function severityType(s: string): TagType {
  const map: Record<string, string> = { critical: 'danger', major: 'warning', minor: 'primary', info: 'info' }
  return (map[s] || 'info') as TagType
}
function severityLabel(s: string) {
  const map: Record<string, string> = { critical: '紧急', major: '严重', minor: '一般', info: '提示' }
  return map[s] || s || '-'
}
function statusType(s: string): TagType {
  const map: Record<string, string> = { open: 'danger', in_progress: 'warning', resolved: 'success', closed: 'info' }
  return (map[s] || 'info') as TagType
}
function statusLabel(s: string) {
  const map: Record<string, string> = { open: '待处理', in_progress: '处理中', resolved: '已解决', closed: '已关闭', firing: '触发中' }
  return map[s] || s || '-'
}
function formatTime(t: string) {
  return t ? new Date(t).toLocaleString('zh-CN') : '-'
}

onMounted(fetchIncidents)
</script>

<style scoped>
.incident-card {
  padding: var(--autops-space-md); border: 1px solid var(--autops-bg-4); border-radius: 6px; margin-bottom: var(--autops-space-sm); cursor: pointer; transition: all 0.2s;
}
.incident-card:hover { border-color: var(--autops-primary); box-shadow: 0 2px 8px rgba(22,93,255,0.12); }
.incident-card.active { border-color: var(--autops-primary); background: var(--autops-table-hover); }
.incident-header { display: flex; gap: 6px; margin-bottom: 6px; }
.incident-title { font-weight: 500; font-size: var(--autops-font-14); margin-bottom: 4px; }
.incident-meta { font-size: var(--autops-font-12); color: var(--autops-info); display: flex; gap: 12px; }
.incident-meta .el-icon { margin-right: 2px; }
</style>
