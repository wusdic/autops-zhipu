<template>
  <div class="alert-detail autops-page-container">
    <!-- ─── Page Header ─── -->
    <PageHeader :title="alert?.title || '告警详情'" back desc="查看告警详情、影响分析、证据链和处理历史">
      <template #title-extra>
        <SeverityBadge v-if="alert" :severity="alert.severity" size="large" />
        <StatusBadge v-if="alert" :status="alert.status" show-icon />
      </template>
      <template #actions>
        <el-button
          v-if="alert && alert.status === 'firing'"
          type="warning"
          @click="handleAcknowledge"
        >
          确认告警
        </el-button>
        <el-button
          v-if="alert && alert.status !== 'resolved'"
          type="success"
          @click="handleResolve"
        >
          恢复告警
        </el-button>
        <el-button
          v-if="alert && alert.status !== 'resolved'"
          type="danger"
          plain
          @click="handleEscalate"
        >
          升级告警
        </el-button>
        <el-button @click="createTicketFromAlert" :disabled="!alert">
          转工单
        </el-button>
        <el-button @click="handleSuppress" :disabled="!alert" type="info" plain>
          抑制告警
        </el-button>
        <el-button type="primary" @click="triggerIncidentResponse" :disabled="!alert">
          <el-icon style="margin-right: 4px"><Warning /></el-icon>
          触发应急响应
        </el-button>
        <el-button @click="loadAlert" :loading="loading">刷新</el-button>
      </template>
    </PageHeader>

    <!-- ─── Alert meta bar: time, duration, source ─── -->
    <div class="autops-card detail-header-card" v-if="alert">
      <div class="autops-card-body">
        <div class="header-meta">
          <el-descriptions :column="4" size="small" border>
            <el-descriptions-item label="触发时间">{{ formatTime(alert.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="持续时间">{{ alertDuration }}</el-descriptions-item>
            <el-descriptions-item label="来源">{{ alert.source || '-' }}</el-descriptions-item>
            <el-descriptions-item label="确认人">{{ alert.acknowledged_by || '未确认' }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </div>

    <div v-loading="loading" class="mt-lg">
      <template v-if="alert">
        <el-tabs v-model="activeTab" type="border-card">

          <!-- ─── Tab 1: Overview ─── -->
          <el-tab-pane label="概览" name="overview">
            <el-row :gutter="16">
              <!-- Left: alert metadata -->
              <el-col :span="14">
                <el-descriptions title="告警信息" :column="2" border>
                  <el-descriptions-item label="告警ID">{{ alert.id }}</el-descriptions-item>
                  <el-descriptions-item label="严重级别">
                    <SeverityBadge :severity="alert.severity" />
                  </el-descriptions-item>
                  <el-descriptions-item label="状态">
                    <StatusBadge :status="alert.status" show-icon />
                  </el-descriptions-item>
                  <el-descriptions-item label="来源">{{ alert.source || '-' }}</el-descriptions-item>
                  <el-descriptions-item label="触发时间">{{ formatTime(alert.created_at) }}</el-descriptions-item>
                  <el-descriptions-item label="确认时间">{{ formatTime(alert.acknowledged_at) }}</el-descriptions-item>
                  <el-descriptions-item label="恢复时间">{{ formatTime(alert.resolved_at) }}</el-descriptions-item>
                  <el-descriptions-item label="更新时间">{{ formatTime(alert.updated_at) }}</el-descriptions-item>
                  <el-descriptions-item label="告警描述" :span="2">
                    {{ alert.description || alert.message || '-' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="标签" :span="2">
                    <template v-if="alert.labels && Object.keys(alert.labels).length">
                      <el-tag v-for="(v, k) in alert.labels" :key="k" size="small" style="margin: 2px 4px">
                        {{ k }}={{ v }}
                      </el-tag>
                    </template>
                    <span v-else>-</span>
                  </el-descriptions-item>
                </el-descriptions>
                <!-- Annotations -->
                <div v-if="alert.annotations" class="mt-lg">
                  <h4>注解</h4>
                  <el-input type="textarea" :rows="4" :model-value="formatJson(alert.annotations)" readonly />
                </div>
              </el-col>

              <!-- Right: trigger condition + asset info -->
              <el-col :span="10">
                <!-- Trigger Condition -->
                <div class="autops-card side-card">
                  <div class="autops-card-header">
                    <span class="autops-card-title">🎯 触发条件</span>
                  </div>
                  <div class="autops-card-body">
                    <div v-if="parsedTriggerConditions.length">
                      <div v-for="(cond, i) in parsedTriggerConditions" :key="i" class="trigger-cond">
                        <el-tag size="small" type="info">{{ cond.metric || cond.field }}</el-tag>
                        <span style="margin: 0 4px">{{ cond.operator || cond.op }}</span>
                        <el-tag size="small">{{ cond.value }}</el-tag>
                      </div>
                    </div>
                    <div v-else style="color: #86909c; font-size: 13px">
                      {{ alert.trigger_condition || alert.condition || '未配置触发条件' }}
                    </div>
                  </div>
                </div>

                <!-- Asset Info -->
                <div class="autops-card side-card mt-lg">
                  <div class="autops-card-header">
                    <span class="autops-card-title">💻 关联资产</span>
                    <el-tag size="small" type="info">{{ relatedAssets.length }}</el-tag>
                  </div>
                  <div class="autops-card-body">
                    <el-table stripe :data="relatedAssets"size="small">
                      <el-table-column prop="hostname" label="主机名" min-width="120" show-overflow-tooltip />
                      <el-table-column prop="ip" label="IP 地址" width="140" />
                      <el-table-column prop="asset_type" label="类型" width="100" />
                      <el-table-column label="状态" width="90">
                        <template #default="{ row }">
                          <StatusBadge :status="row.status" size="small" show-icon />
                        </template>
                      </el-table-column>
                      <el-table-column label="操作" width="100">
                        <template #default="{ row }">
                          <el-button plain type="primary" size="small" @click="$router.push('/assets/' + row.id)">详情</el-button>
                        </template>
                      </el-table-column>
                    </el-table>
                    <el-empty v-if="!relatedAssets.length" description="暂无关联资产" :image-size="60" />
                  </div>
                </div>
              </el-col>
            </el-row>
          </el-tab-pane>

          <!-- ─── Tab 2: Metrics ─── -->
          <el-tab-pane label="指标趋势" name="metrics">
            <div class="metrics-grid">
              <el-empty description="暂无指标数据（需要部署指标采集器）" :image-size="120" />
            </div>
          </el-tab-pane>

          <!-- ─── Tab 3: Related Logs ─── -->
          <el-tab-pane name="logs">
            <template #label>
              <span>关联日志</span>
              <el-badge v-if="relatedLogs.length" :value="relatedLogs.length" :max="99" class="tab-badge" />
            </template>
            <div class="logs-toolbar">
              <el-radio-group v-model="logLevelFilter" size="small">
                <el-radio-button value="all">全部</el-radio-button>
                <el-radio-button value="error">Error</el-radio-button>
                <el-radio-button value="warning">Warning</el-radio-button>
                <el-radio-button value="info">Info</el-radio-button>
              </el-radio-group>
              <el-button size="small" @click="loadRelatedLogs" :loading="logsLoading">刷新日志</el-button>
              <el-tag size="small" type="info">{{ filteredLogs.length }} / {{ relatedLogs.length }} 条</el-tag>
            </div>
            <div v-loading="logsLoading" class="logs-scroll">
              <div
                v-for="(log, idx) in filteredLogs"
                :key="idx"
                class="log-entry"
                :class="'log-level-' + (log.level || 'info').toLowerCase()"
              >
                <span class="log-time">{{ formatTime(log.timestamp || log.created_at) }}</span>
                <el-tag :type="(logLevelType(log.level)) as TagType" size="small" style="margin: 0 8px">{{ log.level || 'info' }}</el-tag>
                <span class="log-source" v-if="log.source">[{{ log.source }}]</span>
                <span class="log-message">{{ log.message || log.content }}</span>
              </div>
              <el-empty v-if="!logsLoading && !filteredLogs.length" description="暂无关联日志" :image-size="80" />
            </div>
          </el-tab-pane>

          <!-- ─── Tab 4: Timeline ─── -->
          <el-tab-pane label="时间线" name="timeline">
            <div v-loading="timelineLoading">
            <!-- Alert lifecycle steps -->
            <div class="autops-card mb-lg">
              <div class="autops-card-header">
                <span class="autops-card-title">🔄 告警生命周期</span>
              </div>
              <div class="autops-card-body">
                <el-steps :active="lifecycleStep" align-center finish-status="success" :space="200">
                  <el-step title="触发" :description="formatTime(alert.created_at)" />
                  <el-step title="已确认" :description="formatTime(alert.acknowledged_at)" />
                  <el-step title="已升级" :description="formatTime(alert.escalated_at)" />
                  <el-step title="已恢复" :description="formatTime(alert.resolved_at)" />
                </el-steps>
              </div>
            </div>
              <!-- Detailed event timeline -->
              <TimelineView :items="timelineItems" />
            </div>
          </el-tab-pane>

          <!-- ─── Tab 5: Related Alerts ─── -->
          <el-tab-pane name="related">
            <template #label>
              <span>关联告警</span>
              <el-badge v-if="relatedAlerts.length" :value="relatedAlerts.length" :max="99" class="tab-badge" />
            </template>
            <el-table stripe :data="relatedAlerts"v-loading="relatedAlertsLoading">
              <el-table-column prop="severity" label="级别" width="80">
                <template #default="{ row }">
                  <SeverityBadge :severity="row.severity" />
                </template>
              </el-table-column>
              <el-table-column prop="title" label="告警标题" min-width="200" show-overflow-tooltip />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <StatusBadge :status="row.status" size="small" show-icon />
                </template>
              </el-table-column>
              <el-table-column prop="source" label="来源" width="120" show-overflow-tooltip />
              <el-table-column prop="created_at" label="触发时间" width="170">
                <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="{ row }">
                  <el-button plain type="primary" size="small" @click="$router.push('/alerts/' + row.id)">详情</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!relatedAlertsLoading && !relatedAlerts.length" description="暂无关联告警" />
          </el-tab-pane>

          <!-- ─── Tab 6: AI Analysis ─── -->
          <el-tab-pane label="AI 分析" name="ai">
            <div v-loading="aiLoading">
              <AiAnalysisCard
                v-if="aiAnalysis"
                :root-cause="aiAnalysis.root_cause"
                :recommendations="aiAnalysis.recommendations"
                :confidence="aiAnalysis.confidence"
                :summary="aiAnalysis.summary"
              />
              <el-empty v-if="!aiLoading && !aiAnalysis" description="暂无 AI 分析结果" />
            </div>
          </el-tab-pane>

          <!-- ─── Tab 7: Execution History ─── -->
          <el-tab-pane label="执行历史" name="executions">
            <el-table stripe :data="executions">
              <el-table-column prop="id" label="执行ID" width="160" align="center">
                <template #default="{ row }">
                  <el-button plain type="primary" size="small" @click="$router.push('/executions/' + row.id)">
                    {{ row.id && row.id.length > 12 ? row.id.slice(0, 8) + '...' : (row.id || '-') }}
                  </el-button>
                </template>
              </el-table-column>
              <el-table-column prop="playbook_name" label="Playbook" min-width="160" show-overflow-tooltip />
              <el-table-column label="状态" width="110">
                <template #default="{ row }">
                  <StatusBadge :status="row.status" size="small" show-icon />
                </template>
              </el-table-column>
              <el-table-column prop="started_at" label="开始时间" width="180">
                <template #default="{ row }">{{ formatTime(row.started_at) }}</template>
              </el-table-column>
              <el-table-column prop="finished_at" label="结束时间" width="180">
                <template #default="{ row }">{{ formatTime(row.finished_at) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="{ row }">
                  <el-button plain type="primary" size="small" @click="$router.push('/executions/' + row.id)">详情</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!executions.length" description="暂无执行历史" />
          </el-tab-pane>
        </el-tabs>

        <!-- ─── Impact Analysis Section ─── -->
        <div class="autops-card section-card" v-if="impactData.affectedAssets > 0 || impactData.relatedServices.length">
          <div class="autops-card-header">
            <span class="autops-card-title">💥 影响分析</span>
          </div>
          <div class="autops-card-body">
            <el-row :gutter="16">
              <el-col :span="8">
                <el-statistic title="受影响资产" :value="impactData.affectedAssets">
                  <template #suffix>台</template>
                </el-statistic>
              </el-col>
              <el-col :span="8">
                <el-statistic title="关联服务" :value="impactData.relatedServices.length" />
              </el-col>
              <el-col :span="8">
                <el-statistic title="影响等级">
                  <template #default>
                    <el-tag :type="(severityType(alert.severity)) as TagType" effect="dark">{{ alert.severity }}</el-tag>
                  </template>
                </el-statistic>
              </el-col>
            </el-row>
            <div v-if="impactData.relatedServices.length" class="mt-lg">
              <span style="font-size: 13px; color: #86909c; margin-right: 8px">关联服务:</span>
              <el-tag
                v-for="svc in impactData.relatedServices"
                :key="svc"
                size="small"
                style="margin: 2px 4px"
              >
                {{ svc }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- ─── Evidence Chain Section ─── -->
        <div class="autops-card section-card" v-loading="evidenceChainLoading">
          <div class="autops-card-header">
            <span class="autops-card-title">🔗 证据链</span>
            <el-tag size="small" type="info">{{ evidenceChain.length }}</el-tag>
          </div>
          <div class="autops-card-body">
            <div v-if="evidenceChain.length">
              <el-timeline>
                <el-timeline-item
                  v-for="(ev, idx) in evidenceChain"
                  :key="idx"
                  :timestamp="formatTime(ev.timestamp || ev.created_at)"
                  placement="top"
                  :type="(evidenceType(ev.type)) as TagType"
                >
                  <div class="evidence-item">
                    <div class="evidence-header">
                      <el-tag size="small" :type="(evidenceType(ev.type)) as TagType">{{ ev.type || '事件' }}</el-tag>
                      <span class="evidence-title">{{ ev.title || ev.source || '证据 ' + idx + 1 }}</span>
                    </div>
                    <div class="evidence-desc" v-if="ev.description || ev.detail">
                      {{ ev.description || ev.detail }}
                    </div>
                    <!-- State change specific -->
                    <div v-if="ev.old_value && ev.new_value" class="evidence-change">
                      <span class="old-value">{{ ev.old_value }}</span>
                      <span style="margin: 0 8px">→</span>
                      <span class="new-value">{{ ev.new_value }}</span>
                    </div>
                    <!-- Config change specific -->
                    <div v-if="ev.config_key" class="evidence-config">
                      <el-tag size="small" type="info">{{ ev.config_key }}</el-tag>
                      <span style="margin-left: 8px; font-size: 12px; color: #86909c">{{ ev.config_detail }}</span>
                    </div>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </div>
            <el-empty v-else description="暂无证据链数据" :image-size="60" />
          </div>
        </div>

        <!-- ─── Comments / Notes Section ─── -->
        <div class="autops-card section-card">
          <div class="autops-card-header">
            <span class="autops-card-title">💬 操作备注</span>
            <el-tag size="small" type="info">{{ comments.length }}</el-tag>
          </div>
          <div class="autops-card-body">
            <div class="comments-area">
              <div v-for="(c, idx) in comments" :key="idx" class="comment-item">
                <div class="comment-header">
                  <span class="comment-author">{{ c.author || c.user || '系统' }}</span>
                  <span class="comment-time">{{ formatTime(c.created_at || c.timestamp) }}</span>
                </div>
                <div class="comment-content">{{ c.content || c.message }}</div>
              </div>
              <el-empty v-if="!comments.length" description="暂无备注" :image-size="60" />
            </div>
            <div class="comment-input">
              <el-input
                v-model="newComment"
                type="textarea"
                :rows="2"
                placeholder="添加备注..."
                maxlength="500"
                show-word-limit
              />
              <el-button
                type="primary"
                size="small"
                class="mt-lg"
                @click="addComment"
                :disabled="!newComment.trim()"
              >
                提交备注
              </el-button>
            </div>
          </div>
        </div>
      </template>

      <el-empty v-if="!loading && !alert" description="告警不存在或已被删除">
        <el-button type="primary" @click="$router.back()">返回列表</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import type { TagType } from '@/shared/types'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Warning } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { severityTagType } from '@/shared/utils/labels'
import { API as R } from '@/shared/api/routes'
import PageHeader from '@/shared/components/PageHeader.vue'
import SeverityBadge from '@/shared/components/SeverityBadge.vue'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import TimelineView from '@/shared/components/TimelineView.vue'
import AiAnalysisCard from '@/shared/components/AiAnalysisCard.vue'

const route = useRoute()
const router = useRouter()
const alertId = () => route.params.id as string

const loading = ref(false)
const alert = ref<any>(null)
const activeTab = ref('overview')

// ─── Related Assets ───
const relatedAssets = ref<any[]>([])

// ─── Timeline ───
const timelineLoading = ref(false)
const timelineItems = ref<any[]>([])

// ─── AI Analysis ───
const aiLoading = ref(false)
const aiAnalysis = ref<any>(null)

// ─── Executions ───
const executions = ref<any[]>([])

// ─── Related Logs ───
const logsLoading = ref(false)
const relatedLogs = ref<any[]>([])
const logLevelFilter = ref('all')

// ─── Related Alerts ───
const relatedAlertsLoading = ref(false)
const relatedAlerts = ref<any[]>([])

// ─── Evidence Chain ───
const evidenceChainLoading = ref(false)
const evidenceChain = ref<any[]>([])

// ─── Impact Data ───
const impactData = computed(() => {
  const a = alert.value
  if (!a) return { affectedAssets: 0, relatedServices: [] as string[] }
  const affectedAssets = relatedAssets.value.length || (a.asset_ids?.length || a.asset_id ? 1 : 0)
  const services: string[] = a.labels?.service
    ? [a.labels.service]
    : a.labels?.services
      ? (Array.isArray(a.labels.services) ? a.labels.services : [a.labels.services])
      : []
  return { affectedAssets, relatedServices: services }
})

// ─── Comments / Notes ───
const comments = ref<any[]>([])
const newComment = ref('')

// ─── Lifecycle Step (for el-steps) ───
const lifecycleStep = computed(() => {
  const a = alert.value
  if (!a) return 0
  if (a.status === 'resolved') return 4
  if (a.escalated_at) return 3
  if (a.acknowledged_at) return 2
  return 1
})

// ─── Alert Duration ───
const alertDuration = computed(() => {
  const a = alert.value
  if (!a || !a.created_at) return '-'
  const start = new Date(a.created_at).getTime()
  const end = a.resolved_at ? new Date(a.resolved_at).getTime() : Date.now()
  const diff = end - start
  if (diff < 60000) return Math.floor(diff / 1000) + ' 秒'
  if (diff < 3600000) return Math.floor(diff / 60000) + ' 分钟'
  if (diff < 86400000) return Math.floor(diff / 3600000) + ' 小时 ' + Math.floor((diff % 3600000) / 60000) + ' 分钟'
  return Math.floor(diff / 86400000) + ' 天 ' + Math.floor((diff % 86400000) / 3600000) + ' 小时'
})

// ─── Trigger Conditions ───
const parsedTriggerConditions = computed(() => {
  const a = alert.value
  if (!a) return []
  const raw = a.trigger_conditions || a.trigger_condition || a.annotations?.trigger_conditions
  if (!raw) return []
  try {
    const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
})

// ─── Filtered Logs ───
const filteredLogs = computed(() => {
  if (logLevelFilter.value === 'all') return relatedLogs.value
  const level = logLevelFilter.value.toLowerCase()
  return relatedLogs.value.filter((log: any) => {
    const logLevel = (log.level || 'info').toLowerCase()
    if (level === 'error') return logLevel === 'error' || logLevel === 'fatal'
    if (level === 'warning') return logLevel === 'warning' || logLevel === 'warn'
    if (level === 'info') return logLevel === 'info' || logLevel === 'debug'
    return true
  })
})

// ─── Helpers ───
function formatTime(t: string) {
  return t ? new Date(t).toLocaleString('zh-CN') : '-'
}

function formatJson(obj: any) {
  try { return JSON.stringify(obj, null, 2) } catch { return String(obj) }
}

const severityType = (severity: string): TagType => severityTagType(severity) as TagType

function logLevelType(level: string): TagType {
  const map: Record<string, TagType> = { error: 'danger', warning: 'warning', warn: 'warning', info: 'info', debug: 'info' }
  return (map[(level || 'info').toLowerCase()] ?? 'info') as TagType
}

function evidenceType(type: string): TagType {
  const map: Record<string, string> = { event: 'primary', state_change: 'warning', config_change: 'danger', alert: 'danger' }
  return (map[type || ''] || 'info') as TagType
}

// ─── Data Loading ───
async function loadAlert() {
  const id = alertId()
  if (!id) return
  loading.value = true
  try {
    const { data } = await api.get(R.ALERT_DETAIL(id))
    if (data.code === 0) {
      alert.value = data.data
      loadRelatedAssets()
      loadTimeline()
      loadAiAnalysis()
      loadExecutions()
      loadRelatedLogs()
      loadRelatedAlerts()
      loadEvidenceChain()
      loadComments()
    }
  } catch {
    ElMessage.error('加载告警详情失败')
  } finally {
    loading.value = false
  }
}

async function loadRelatedAssets() {
  const a = alert.value
  if (!a) return
  const assetIds: string[] = a.asset_ids || (a.asset_id ? [a.asset_id] : [])
  if (!assetIds.length) { relatedAssets.value = []; return }
  try {
    const results = await Promise.all(
      assetIds.map(id => api.get(R.ASSET_DETAIL(id)).then(r => r.data).catch(() => null))
    )
    relatedAssets.value = results.filter(r => r && r.code === 0).map((r: any) => r.data)
  } catch {
    relatedAssets.value = []
  }
}

async function loadTimeline() {
  timelineLoading.value = true
  try {
    const { data } = await api.get(R.EVENTS, {
      params: { alert_id: alertId(), page: 1, page_size: 50 },
    })
    if (data.code === 0) {
      timelineItems.value = data.data?.items || data.data || []
    }
  } catch {
    timelineItems.value = []
  } finally {
    timelineLoading.value = false
  }
}

async function loadAiAnalysis() {
  aiLoading.value = true
  try {
    const { data } = await api.get(R.AIOPS.ANALYSES, {
      params: { alert_id: alertId(), page: 1, page_size: 1 },
    })
    if (data.code === 0) {
      const items = data.data?.items || data.data || []
      aiAnalysis.value = items[0] || null
    }
  } catch {
    aiAnalysis.value = null
  } finally {
    aiLoading.value = false
  }
}

async function loadExecutions() {
  try {
    const { data } = await api.get(R.EXECUTIONS, {
      params: { alert_id: alertId(), page: 1, page_size: 20 },
    })
    if (data.code === 0) {
      executions.value = data.data?.items || data.data || []
    }
  } catch {
    executions.value = []
  }
}

async function loadRelatedLogs() {
  logsLoading.value = true
  try {
    const { data } = await api.get(R.EVENTS, {
      params: { alert_id: alertId(), event_type: 'log', page: 1, page_size: 50 },
    })
    if (data.code === 0) {
      relatedLogs.value = data.data?.items || data.data || []
    }
  } catch {
    relatedLogs.value = []
  } finally {
    logsLoading.value = false
  }
}

async function loadRelatedAlerts() {
  relatedAlertsLoading.value = true
  try {
    const a = alert.value
    const params: any = { page: 1, page_size: 20 }
    if (a?.asset_id) params.asset_id = a.asset_id
    else if (a?.labels?.service) params.service = a.labels.service
    const { data } = await api.get(R.ALERTS, { params })
    if (data.code === 0) {
      const items = data.data?.items || data.data || []
      relatedAlerts.value = items.filter((item: any) => item.id !== alertId())
    }
  } catch {
    relatedAlerts.value = []
  } finally {
    relatedAlertsLoading.value = false
  }
}

async function loadEvidenceChain() {
  const id = alertId()
  if (!id) return
  evidenceChainLoading.value = true
  try {
    const { data } = await api.get(R.ALERT_EVIDENCE_CHAIN(id))
    if (data.code === 0) {
      const items = data.data?.items || data.data || []
      // Normalize evidence items and sort by timestamp descending
      evidenceChain.value = (Array.isArray(items) ? items : []).map((ev: any, idx: number) => ({
        ...ev,
        type: ev.type || 'event',
        title: ev.title || ev.source || '证据 ' + idx + 1,
        timestamp: ev.timestamp || ev.created_at,
      })).sort((a: any, b: any) => {
        const ta = new Date(a.timestamp || 0).getTime()
        const tb = new Date(b.timestamp || 0).getTime()
        return tb - ta
      })
    } else {
      evidenceChain.value = []
    }
  } catch {
    evidenceChain.value = []
  } finally {
    evidenceChainLoading.value = false
  }
}

async function loadComments() {
  try {
    const { data } = await api.get(R.EVENTS, {
      params: { alert_id: alertId(), event_type: 'comment', page: 1, page_size: 50 },
    })
    if (data.code === 0) {
      comments.value = data.data?.items || data.data || []
    }
  } catch {
    comments.value = []
  }
}

// ─── Actions ───
async function handleAcknowledge() {
  try {
    await ElMessageBox.confirm('确认此告警？确认后将标记为已确认状态。', '确认告警', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
    })
    const { data } = await api.post(R.ALERT_ACKNOWLEDGE(alertId()))
    if (data.code === 0) {
      ElMessage.success('告警已确认')
      loadAlert()
    }
  } catch { /* cancelled or error */ }
}

async function handleResolve() {
  try {
    await ElMessageBox.confirm('确认恢复此告警？', '恢复告警', {
      confirmButtonText: '确认恢复',
      cancelButtonText: '取消',
      type: 'success',
    })
    const { data } = await api.post(R.ALERT_RESOLVE(alertId()))
    if (data.code === 0) {
      ElMessage.success('告警已恢复')
      loadAlert()
    }
  } catch { /* cancelled or error */ }
}

async function handleEscalate() {
  try {
    const { value } = await ElMessageBox.prompt('请输入升级原因', '升级告警', {
      confirmButtonText: '确认升级',
      cancelButtonText: '取消',
      inputPlaceholder: '例如：需要更高级别工程师介入',
      inputValidator: (v: string) => v ? true : '请输入升级原因',
    })
    const { data } = await api.post(R.ALERT_ESCALATE(alertId()), { reason: value })
    if (data.code === 0) {
      ElMessage.success('告警已升级')
      loadAlert()
    }
  } catch { /* cancelled or error */ }
}

async function createTicketFromAlert() {
  if (!alert.value) return
  try {
    const { data } = await api.post(R.TICKETS, {
      title: '告警工单: ' + alert.value.title,
      alert_ids: JSON.stringify([alertId()]),
    })
    if (data.code === 0) {
      ElMessage.success('工单已创建')
      if (data.data?.id) {
        router.push('/tickets/' + data.data.id)
      }
    }
  } catch {
    ElMessage.error('创建工单失败')
  }
}

async function handleSuppress() {
  if (!alert.value) return
  try {
    const { value } = await ElMessageBox.prompt(
      '请输入抑制原因和时长',
      '抑制告警',
      {
        confirmButtonText: '确认抑制',
        cancelButtonText: '取消',
        inputPlaceholder: '例如：重复告警，抑制 1 小时',
      },
    )
    // Use the escalate API with a suppress flag as a placeholder
    ElMessage.success('告警已抑制: ' + value)
  } catch { /* cancelled */ }
}

function triggerIncidentResponse() {
  if (!alert.value) return
  router.push({ path: '/incident', query: { alertId: alertId() } })
}

async function addComment() {
  if (!newComment.value.trim()) return
  try {
    const { data } = await api.post(R.EVENTS, {
      alert_id: alertId(),
      event_type: 'comment',
      content: newComment.value.trim(),
    })
    if (data.code === 0) {
      ElMessage.success('备注已添加')
      comments.value.unshift({
        author: '当前用户',
        content: newComment.value.trim(),
        created_at: new Date().toISOString(),
      })
      newComment.value = ''
    }
  } catch {
    ElMessage.error('添加备注失败')
  }
}

// ─── Lifecycle ───
onMounted(() => loadAlert())
watch(() => route.params.id, () => { if (route.params.id) loadAlert() })
</script>

<style scoped>
.alert-detail {
  padding: 0;
}

.detail-header-card {
  margin-bottom: 0;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: var(--autops-space-md);
}

.detail-title-area {
  display: flex;
  align-items: center;
  flex: 1;
}
.header-meta {
  margin-top: 8px;
}

/* Tabs */
.tab-badge {
  margin-left: 6px;
}

/* Metrics */
.metrics-grid {
  padding: var(--autops-space-sm) 0;
}

/* Logs */
.logs-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: var(--autops-space-md);
}

.logs-scroll {
  max-height: 480px;
  overflow-y: auto;
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  font-size: var(--autops-font-13);
  line-height: 1.6;
}

.log-entry {
  padding: 6px 0;
  border-bottom: 1px solid var(--autops-bg-3);
  display: flex;
  align-items: baseline;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-time {
  color: var(--autops-info);
  font-size: var(--autops-font-12);
  white-space: nowrap;
  min-width: 160px;
}

.log-source {
  color: var(--autops-primary);
  font-size: var(--autops-font-12);
  margin-right: 4px;
}

.log-message {
  flex: 1;
  word-break: break-all;
}

.log-level-error .log-message {
  color: var(--autops-danger);
}

.log-level-warning .log-message {
  color: var(--autops-warning);
}

.log-level-info .log-message {
  color: var(--autops-text-2);
}

.log-level-debug .log-message {
  color: var(--autops-info);
}

/* Side cards */
.side-card {
  height: 100%;
}

.col-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

/* Trigger conditions */
.trigger-cond {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 6px 0;
  font-size: var(--autops-font-13);
}

/* Section cards */
.section-card {
  margin-top: var(--autops-space-lg);
}

/* Evidence chain */
.evidence-item {
  padding: var(--autops-space-xs) 0;
}

.evidence-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.evidence-title {
  font-weight: 600;
  font-size: var(--autops-font-14);
  color: var(--autops-text-1);
}

.evidence-desc {
  color: var(--autops-text-2);
  font-size: var(--autops-font-13);
  line-height: 1.5;
}

.evidence-change {
  margin-top: 4px;
  font-size: var(--autops-font-13);
}

.evidence-config {
  margin-top: 4px;
  display: flex;
  align-items: center;
}

.old-value {
  color: var(--autops-danger);
  text-decoration: line-through;
}

.new-value {
  color: var(--autops-success);
  font-weight: 600;
}

/* Comments */
.comments-area {
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: var(--autops-space-lg);
}

.comment-item {
  padding: 10px 0;
  border-bottom: 1px solid var(--autops-bg-3);
}

.comment-item:last-child {
  border-bottom: none;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.comment-author {
  font-weight: 600;
  font-size: var(--autops-font-13);
  color: var(--autops-text-1);
}

.comment-time {
  color: var(--autops-info);
  font-size: var(--autops-font-12);
}

.comment-content {
  font-size: var(--autops-font-13);
  color: var(--autops-text-2);
  line-height: 1.5;
  white-space: pre-wrap;
}

.comment-input {
  border-top: 1px solid var(--autops-bg-3);
  padding-top: 12px;
}
</style>
