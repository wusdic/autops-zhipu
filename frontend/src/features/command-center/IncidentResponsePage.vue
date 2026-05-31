<template>
  <div class="incident-response-page">
    <!-- 顶部标题栏 -->
    <el-card class="page-header" shadow="never">
      <div class="header-bar">
        <div class="header-left">
          <h2 style="margin: 0">🚨 故障处置工作台</h2>
          <span v-if="selectedAlert" class="header-alert-tag">
            <el-tag :type="severityType(selectedAlert.severity)" effect="dark" size="small">
              {{ selectedAlert.severity }}
            </el-tag>
            <span class="alert-title-text">{{ selectedAlert.title }}</span>
            <StatusBadge :status="selectedAlert.status" size="small" show-icon />
          </span>
        </div>
        <div class="header-right">
          <el-button @click="loadAlerts" :loading="alertLoading" size="default">刷新告警</el-button>
          <el-button
            type="primary"
            @click="startAIDiagnosis"
            :loading="aiLoading"
            :disabled="!selectedAlert"
          >
            <el-icon style="margin-right: 4px"><MagicStick /></el-icon>
            AI 诊断分析
          </el-button>
        </div>
      </div>
      <!-- 告警快速选择条 -->
      <el-table
        :data="activeAlerts"
        highlight-current-row
        @current-change="selectAlert"
        max-height="200"
        v-loading="alertLoading"
        size="small"
        class="alert-quick-bar"
      >
        <el-table-column prop="severity" label="级别" width="80">
          <template #default="{ row }">
            <el-tag :type="severityType(row.severity)" size="small">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="告警标题" min-width="240" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <StatusBadge :status="row.status" size="small" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="触发时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 三栏主体: 时间线 | 证据与分析 | 推荐动作 -->
    <el-row :gutter="16" class="main-columns" v-if="selectedAlert">
      <!-- 左栏: 时间线 (span=6) -->
      <el-col :span="6">
        <el-card class="col-card timeline-col" shadow="hover">
          <template #header>
            <div class="col-header">
              <span>📜 时间线</span>
              <el-tag size="small" type="info">{{ timelineItems.length }}</el-tag>
            </div>
          </template>
          <div class="col-scroll">
            <TimelineView :items="timelineItems" />
          </div>
        </el-card>
      </el-col>

      <!-- 中栏: 证据与分析 (span=12) -->
      <el-col :span="12">
        <div class="evidence-col">
          <!-- 关键指标 -->
          <el-card shadow="hover" class="col-card" style="margin-bottom: 16px">
            <template #header>
              <div class="col-header">
                <span>📊 关键指标</span>
              </div>
            </template>
            <el-row :gutter="12">
              <el-col :span="12">
                <MetricChart
                  :data="metricData"
                  title="CPU 使用率"
                  height="180px"
                  color="#E6A23C"
                  unit="%"
                />
              </el-col>
              <el-col :span="12">
                <MetricChart
                  :data="memMetricData"
                  title="内存使用率"
                  height="180px"
                  color="#F56C6C"
                  unit="%"
                />
              </el-col>
            </el-row>
          </el-card>

          <!-- AI 分析结果 -->
          <el-card shadow="hover" class="col-card" style="margin-bottom: 16px" v-if="aiResult || aiLoading">
            <div v-if="aiLoading" style="text-align: center; padding: 32px 0">
              <el-icon class="is-loading" :size="24"><Loading /></el-icon>
              <div style="margin-top: 8px; color: #909399">AI 正在诊断分析中...</div>
            </div>
            <AiAnalysisCard
              v-else
              :root-cause="aiResult?.root_cause"
              :recommendations="aiResult?.recommendations"
              :confidence="aiResult?.confidence"
              :summary="aiResult?.impact"
            />
            <!-- Evidence Chain -->
            <div v-if="aiResult?.evidence_chain?.length" style="margin-top: 12px">
              <div style="font-weight: 600; margin-bottom: 6px">🔗 证据链</div>
              <el-steps direction="vertical" :active="aiResult.evidence_chain.length" finish-status="success" :space="40">
                <el-step
                  v-for="(ev, idx) in aiResult.evidence_chain"
                  :key="idx"
                  :title="ev.source || `证据 ${idx + 1}`"
                  :description="ev.detail || ev.description || ev"
                  :status="ev.confirmed ? 'success' : 'process'"
                />
              </el-steps>
            </div>
          </el-card>

          <!-- 告警上下文详情 -->
          <el-card shadow="hover" class="col-card">
            <template #header>
              <div class="col-header">
                <span>📋 告警上下文</span>
                <el-tag size="small">{{ selectedAlert.id }}</el-tag>
              </div>
            </template>
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="告警标题" :span="2">{{ selectedAlert.title }}</el-descriptions-item>
              <el-descriptions-item label="严重程度">
                <el-tag :type="severityType(selectedAlert.severity)" size="small">{{ selectedAlert.severity }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="状态">
                <StatusBadge :status="selectedAlert.status" size="small" show-icon />
              </el-descriptions-item>
              <el-descriptions-item label="触发时间" :span="2">{{ formatTime(selectedAlert.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="上下文信息" :span="2">
                <div style="white-space: pre-wrap; max-height: 120px; overflow: auto; font-size: 13px">
                  {{ selectedAlert.context || '无上下文信息' }}
                </div>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- 关联告警 -->
          <el-card shadow="hover" class="col-card" style="margin-bottom: 16px" v-if="relatedAlerts.length">
            <template #header>
              <div class="col-header">
                <span>🔔 关联告警</span>
                <el-tag size="small" type="info">{{ relatedAlerts.length }}</el-tag>
              </div>
            </template>
            <el-table :data="relatedAlerts" size="small" max-height="200">
              <el-table-column prop="severity" label="级别" width="80">
                <template #default="{ row }">
                  <el-tag :type="severityType(row.severity)" size="small">{{ row.severity }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="title" label="告警标题" min-width="180" show-overflow-tooltip />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <StatusBadge :status="row.status" size="small" />
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="时间" width="150">
                <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
              </el-table-column>
            </el-table>
          </el-card>

          <!-- 关联日志 -->
          <el-card shadow="hover" class="col-card" style="margin-bottom: 16px">
            <template #header>
              <div class="col-header">
                <span>📄 关联日志</span>
                <el-tag size="small" type="info">{{ relatedLogs.length }} 条</el-tag>
              </div>
            </template>
            <div class="related-logs-scroll">
              <div v-for="(log, idx) in relatedLogs" :key="idx" class="log-entry" :class="'log-level-' + (log.level || 'info').toLowerCase()">
                <span class="log-time">{{ formatTime(log.timestamp || log.created_at) }}</span>
                <el-tag :type="logLevelType(log.level)" size="small" style="margin: 0 8px">{{ log.level || 'info' }}</el-tag>
                <span class="log-message">{{ log.message || log.content }}</span>
              </div>
              <el-empty v-if="!relatedLogs.length" description="暂无关联日志" :image-size="60" />
            </div>
          </el-card>

          <!-- 资产状态变更 -->
          <el-card shadow="hover" class="col-card" v-if="assetChanges.length">
            <template #header>
              <div class="col-header">
                <span>🔄 资产状态变更</span>
                <el-tag size="small" type="info">{{ assetChanges.length }}</el-tag>
              </div>
            </template>
            <el-timeline>
              <el-timeline-item
                v-for="(change, idx) in assetChanges"
                :key="idx"
                :timestamp="formatTime(change.timestamp || change.created_at)"
                placement="top"
              >
                <div class="asset-change-item">
                  <span class="change-asset">{{ change.asset_name || change.asset_id }}</span>
                  <el-tag size="small" type="info">{{ change.field || '状态' }}</el-tag>
                  <span class="change-values">
                    <span class="old-value">{{ change.old_value }}</span>
                    →
                    <span class="new-value">{{ change.new_value }}</span>
                  </span>
                </div>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </div>
      </el-col>

      <!-- 右栏: 推荐动作 (span=6) -->
      <el-col :span="6">
        <div class="action-col">
          <!-- 操作面板 -->
          <el-card shadow="hover" class="col-card" style="margin-bottom: 16px">
            <template #header>
              <div class="col-header">
                <span>⚡ 操作面板</span>
              </div>
            </template>
            <el-space direction="vertical" :size="10" style="width: 100%">
              <el-button
                type="warning"
                style="width: 100%"
                @click="handleAcknowledge(selectedAlert.id)"
                :disabled="selectedAlert.status !== 'firing'"
              >
                确认告警
              </el-button>
              <el-button
                type="danger"
                style="width: 100%"
                plain
                @click="handleEscalate(selectedAlert.id)"
                :disabled="!selectedAlert || selectedAlert.status === 'resolved'"
              >
                升级告警
              </el-button>
              <el-button
                type="primary"
                style="width: 100%"
                @click="matchPolicy"
                :disabled="!selectedAlert"
              >
                策略匹配
              </el-button>
              <el-button
                style="width: 100%"
                @click="executeDryRun"
                :disabled="!matchedPolicy"
              >
                Dry-Run 预执行
              </el-button>
              <el-button
                type="danger"
                style="width: 100%"
                @click="handleExecuteAction"
                :disabled="!matchedPolicy"
              >
                执行自动化
              </el-button>
              <el-divider style="margin: 4px 0" />
              <el-button
                style="width: 100%"
                @click="createTicketFromAlert(selectedAlert.id)"
              >
                转工单
              </el-button>
              <el-button
                type="success"
                style="width: 100%"
                @click="handleResolve(selectedAlert.id)"
                :disabled="selectedAlert.status === 'resolved'"
              >
                关闭告警
              </el-button>
            </el-space>
          </el-card>

          <!-- 匹配策略卡片 -->
          <el-card shadow="hover" class="col-card" v-if="matchedPolicy" style="margin-bottom: 16px">
            <template #header>
              <div class="col-header">
                <span>🎯 匹配策略</span>
                <el-tag :type="matchedPolicy.risk_level === 'high' ? 'danger' : matchedPolicy.risk_level === 'medium' ? 'warning' : 'success'" size="small">
                  {{ matchedPolicy.risk_level }}
                </el-tag>
              </div>
            </template>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="策略名">{{ matchedPolicy.name }}</el-descriptions-item>
              <el-descriptions-item label="需审批">
                <el-tag :type="matchedPolicy.requires_approval ? 'warning' : 'success'" size="small">
                  {{ matchedPolicy.requires_approval ? '是' : '否' }}
                </el-tag>
              </el-descriptions-item>
              <!-- Trigger Conditions -->
              <el-descriptions-item label="触发条件">
                <div v-if="parseTriggerConditions(matchedPolicy.trigger_conditions).length">
                  <div v-for="(cond, i) in parseTriggerConditions(matchedPolicy.trigger_conditions)" :key="i" class="trigger-cond">
                    <el-tag size="small" type="info">{{ cond.metric || cond.field }}</el-tag>
                    <span style="margin: 0 4px">{{ cond.operator || cond.op }}</span>
                    <el-tag size="small">{{ cond.value }}</el-tag>
                  </div>
                </div>
                <span v-else style="color: #909399">{{ matchedPolicy.trigger_conditions || '未配置' }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="动作链">
                <div v-for="(a, i) in parseActionChain(matchedPolicy.action_chain)" :key="i" style="margin: 2px 0">
                  <el-tag size="small" type="info">{{ a.step || a.name || `步骤${i + 1}` }}</el-tag>
                </div>
              </el-descriptions-item>
            </el-descriptions>
            <!-- One-click Apply -->
            <div style="margin-top: 12px; text-align: center">
              <el-button
                type="primary"
                size="small"
                @click="applyPolicyNow"
                :loading="applyingPolicy"
                style="width: 100%"
              >
                一键应用此策略
              </el-button>
            </div>
          </el-card>

          <!-- 执行历史 -->
          <el-card shadow="hover" class="col-card" v-if="executionRecords.length">
            <template #header>
              <div class="col-header">
                <span>📝 执行历史</span>
                <el-tag size="small" type="info">{{ executionRecords.length }}</el-tag>
              </div>
            </template>
            <div v-for="(exec, i) in executionRecords" :key="i" class="exec-record">
              <div class="exec-record-header">
                <StatusBadge :status="exec.status || 'pending'" size="small" />
                <span class="exec-time">{{ formatTime(exec.created_at) }}</span>
              </div>
              <div class="exec-detail">{{ exec.execution_type }} - {{ exec.target_id }}</div>
              <el-button
                v-if="exec.id"
                link
                type="primary"
                size="small"
                @click="loadExecutionLogs(exec.id)"
              >
                查看日志
              </el-button>
            </div>
          </el-card>
        </div>
      </el-col>
    </el-row>

    <!-- 未选择告警时的占位提示 -->
    <el-empty
      v-if="!selectedAlert && !alertLoading"
      description="请从上方告警列表中选择一条告警以开始处置"
      :image-size="120"
      style="padding: 80px 0"
    />

    <!-- 底部: 实时日志流 (全宽) -->
    <el-card shadow="hover" class="log-stream-card" v-if="selectedAlert">
      <template #header>
        <div class="col-header">
          <span>🖥️ 实时日志流</span>
          <div class="log-stream-controls">
            <el-radio-group v-model="logLevelFilter" size="small" style="margin-right: 12px">
              <el-radio-button value="all">全部</el-radio-button>
              <el-radio-button value="error">Error</el-radio-button>
              <el-radio-button value="warning">Warning</el-radio-button>
              <el-radio-button value="info">Info</el-radio-button>
            </el-radio-group>
            <el-button
              v-if="currentExecutionId"
              size="small"
              type="primary"
              link
              @click="loadExecutionLogs(currentExecutionId)"
              :loading="logLoading"
            >
              刷新日志
            </el-button>
            <el-tag size="small" type="info">{{ filteredLogLines.length }} / {{ logLines.length }} 行</el-tag>
          </div>
        </div>
      </template>
      <LogStream :lines="filteredLogLines" height="260px" />
    </el-card>

    <!-- 审批对话框 -->
    <ApprovalDialog
      v-model="approvalVisible"
      :title="'审批确认 - ' + (matchedPolicy?.name || '')"
      @confirm="onApprovalConfirm"
      @cancel="approvalVisible = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Loading } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'
import TimelineView from '@/shared/components/TimelineView.vue'
import LogStream from '@/shared/components/LogStream.vue'
import AiAnalysisCard from '@/shared/components/AiAnalysisCard.vue'
import ApprovalDialog from '@/shared/components/ApprovalDialog.vue'
import MetricChart from '@/shared/components/MetricChart.vue'
import StatusBadge from '@/shared/components/StatusBadge.vue'

// ─── Router ───
const route = useRoute()

// ─── Reactive State ───
const alertLoading = ref(false)
const activeAlerts = ref<any[]>([])
const selectedAlert = ref<any>(null)

const aiLoading = ref(false)
const aiResult = ref<any>(null)

const matchedPolicy = ref<any>(null)
const executionRecords = ref<any[]>([])

const logLoading = ref(false)
const logLines = ref<string[]>([])
const currentExecutionId = ref<string>('')

const approvalVisible = ref(false)

// ─── New Evidence State ───
const relatedAlerts = ref<any[]>([])
const relatedLogs = ref<any[]>([])
const assetChanges = ref<any[]>([])
const logLevelFilter = ref<string>('all')
const applyingPolicy = ref(false)

// ─── Mock Metric Data (demonstrates MetricChart usage) ───
const metricData = computed(() => generateMockMetric(70, 95))
const memMetricData = computed(() => generateMockMetric(60, 90))

function generateMockMetric(min: number, max: number) {
  const now = Date.now()
  return Array.from({ length: 30 }, (_, i) => ({
    time: new Date(now - (30 - i) * 60000).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    value: Math.floor(min + Math.random() * (max - min)),
  }))
}

// ─── Timeline ───
const timelineItems = computed(() => {
  const items: Array<Record<string, any>> = []
  if (!selectedAlert.value) return items

  // Alert fired event
  items.push({
    time: formatTime(selectedAlert.value.created_at),
    type: 'critical',
    severity: 'critical',
    title: '告警触发',
    description: selectedAlert.value.title,
    icon: 'WarningFilled',
  })

  // Related events from backend
  if (relatedEvents.value.length) {
    for (const evt of relatedEvents.value) {
      items.push({
        time: formatTime(evt.created_at || evt.timestamp),
        type: evt.severity || 'info',
        severity: evt.severity || 'info',
        title: evt.title || evt.event_type || '关联事件',
        description: evt.description || evt.content || '',
      })
    }
  }

  // AI diagnosis event
  if (aiResult.value) {
    items.push({
      time: new Date().toLocaleString('zh-CN'),
      type: 'success',
      severity: 'success',
      title: 'AI 诊断完成',
      description: aiResult.value.root_cause || '分析完成',
      icon: 'MagicStick',
    })
  }

  // Policy match event
  if (matchedPolicy.value) {
    items.push({
      time: new Date().toLocaleString('zh-CN'),
      type: 'success',
      severity: 'success',
      title: `策略匹配: ${matchedPolicy.value.name}`,
      description: `风险级别: ${matchedPolicy.value.risk_level}`,
    })
  }

  // Execution events
  for (const exec of executionRecords.value) {
    items.push({
      time: formatTime(exec.created_at),
      type: exec.status === 'failed' ? 'critical' : exec.status === 'running' ? 'warning' : 'success',
      severity: exec.status === 'failed' ? 'critical' : exec.status === 'running' ? 'warning' : 'success',
      title: exec.status === 'running' ? '自动化执行中' : '自动化执行完成',
      description: `执行ID: ${exec.id} | ${exec.execution_type}`,
    })
  }

  return items
})

const relatedEvents = ref<any[]>([])

// ─── Helpers ───
function formatTime(t: string) {
  return t ? new Date(t).toLocaleString('zh-CN') : ''
}

function parseActionChain(s: string) {
  try {
    return JSON.parse(s || '[]')
  } catch {
    return []
  }
}

function severityType(severity: string) {
  const map: Record<string, string> = { critical: 'danger', high: 'danger', warning: 'warning', info: 'info' }
  return map[severity] || 'info'
}

function logLevelType(level?: string) {
  const map: Record<string, string> = { error: 'danger', warning: 'warning', warn: 'warning', info: 'info', debug: 'info' }
  return map[(level || 'info').toLowerCase()] || 'info'
}

function parseTriggerConditions(raw: string | undefined | any[]) {
  if (!raw) return []
  try {
    const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

// ─── Filtered log lines (by level) ───
const filteredLogLines = computed(() => {
  if (logLevelFilter.value === 'all') return logLines.value
  const level = logLevelFilter.value.toLowerCase()
  return logLines.value.filter(line => {
    const lower = line.toLowerCase()
    if (level === 'error') return lower.includes('error') || lower.includes('fail') || lower.includes('exception')
    if (level === 'warning') return lower.includes('warning') || lower.includes('warn')
    if (level === 'info') return !lower.includes('error') && !lower.includes('warning') && !lower.includes('warn')
    return true
  })
})

// ─── Data Loading ───
async function loadAlerts() {
  alertLoading.value = true
  try {
    const { data } = await api.get(API.ALERTS, { params: { page: 1, page_size: 50 } })
    if (data.code === 0) {
      activeAlerts.value = (data.data.items || []).filter((a: any) => a.status !== 'resolved')
    }
  } finally {
    alertLoading.value = false
  }
}

async function loadAlertDetail(id: string) {
  try {
    const { data } = await api.get(API.ALERT_DETAIL(id))
    if (data.code === 0 && data.data) {
      selectedAlert.value = data.data
      // Auto-load related data
      loadRelatedEvents(id)
      loadExecutions(id)
      loadAlertMetrics(id)
      loadRelatedAlerts(id)
      loadRelatedLogs(id)
      loadAssetChanges(id)
    }
  } catch {
    ElMessage.error('加载告警详情失败')
  }
}

async function loadRelatedEvents(alertId: string) {
  try {
    const { data } = await api.get(API.EVENTS, { params: { alert_id: alertId, page: 1, page_size: 20 } })
    if (data.code === 0) {
      relatedEvents.value = data.data.items || data.data || []
    }
  } catch {
    relatedEvents.value = []
  }
}

async function loadExecutions(alertId: string) {
  try {
    const { data } = await api.get(API.EXECUTIONS, { params: { alert_id: alertId, page: 1, page_size: 20 } })
    if (data.code === 0) {
      executionRecords.value = data.data.items || data.data || []
    }
  } catch {
    executionRecords.value = []
  }
}

function loadAlertMetrics(_alertId: string) {
  // Metric data is currently mock; placeholder for future real metric API
}

async function loadRelatedAlerts(alertId: string) {
  try {
    const { data } = await api.get(API.ALERTS, { params: { related_to: alertId, page: 1, page_size: 20 } })
    if (data.code === 0) {
      const items = data.data.items || data.data || []
      relatedAlerts.value = items.filter((a: any) => a.id !== alertId)
    }
  } catch {
    relatedAlerts.value = []
  }
}

async function loadRelatedLogs(alertId: string) {
  try {
    const { data } = await api.get(API.EVENTS, { params: { alert_id: alertId, event_type: 'log', page: 1, page_size: 50 } })
    if (data.code === 0) {
      relatedLogs.value = data.data.items || data.data || []
    }
  } catch {
    relatedLogs.value = []
  }
}

async function loadAssetChanges(alertId: string) {
  try {
    const alert = selectedAlert.value
    const assetId = alert?.asset_id
    if (!assetId) { assetChanges.value = []; return }
    const { data } = await api.get(API.STATES.CHANGES(assetId), { params: { page: 1, page_size: 20 } })
    if (data.code === 0) {
      assetChanges.value = data.data.items || data.data || []
    }
  } catch {
    assetChanges.value = []
  }
}

// ─── Alert Selection ───
function selectAlert(row: any) {
  if (!row) return
  selectedAlert.value = row
  matchedPolicy.value = null
  aiResult.value = null
  logLines.value = []
  currentExecutionId.value = ''
  relatedEvents.value = []
  executionRecords.value = []
  relatedAlerts.value = []
  relatedLogs.value = []
  assetChanges.value = []
  logLevelFilter.value = 'all'

  // Load full detail if we have an id
  if (row.id) {
    loadAlertDetail(row.id)
  }
}

// ─── Alert Actions (with confirmation) ───
async function acknowledgeAlert(id: string) {
  try {
    const { data } = await api.post(API.ALERT_ACKNOWLEDGE(id))
    if (data.code === 0) {
      ElMessage.success('已确认告警')
      loadAlertDetail(id)
      loadAlerts()
    }
  } catch {
    ElMessage.error('确认失败')
  }
}

async function handleAcknowledge(id: string) {
  try {
    await ElMessageBox.confirm('确认此告警？确认后将标记为已确认状态。', '确认告警', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await acknowledgeAlert(id)
  } catch { /* cancelled */ }
}

async function resolveAlert(id: string) {
  try {
    const { data } = await api.post(API.ALERT_RESOLVE(id))
    if (data.code === 0) {
      ElMessage.success('告警已关闭')
      loadAlertDetail(id)
      loadAlerts()
    }
  } catch {
    ElMessage.error('关闭失败')
  }
}

async function handleResolve(id: string) {
  try {
    await ElMessageBox.confirm('确认关闭此告警？关闭后将标记为已解决状态。', '关闭告警', {
      confirmButtonText: '确认关闭',
      cancelButtonText: '取消',
      type: 'success',
    })
    await resolveAlert(id)
  } catch { /* cancelled */ }
}

async function escalateAlert(id: string) {
  try {
    const { data } = await api.post(API.ALERT_ESCALATE(id), {
      reason: '手动升级',
      alert_id: id,
    })
    if (data.code === 0) {
      ElMessage.success('告警已升级')
      loadAlertDetail(id)
      loadAlerts()
    }
  } catch {
    ElMessage.error('升级失败')
  }
}

async function handleEscalate(id: string) {
  try {
    const { value } = await ElMessageBox.prompt('请输入升级原因', '升级告警', {
      confirmButtonText: '确认升级',
      cancelButtonText: '取消',
      inputPlaceholder: '例如：需要更高级别工程师介入',
      inputValidator: (v: string) => v ? true : '请输入升级原因',
    })
    try {
      const { data } = await api.post(API.ALERT_ESCALATE(id), {
        reason: value,
        alert_id: id,
      })
      if (data.code === 0) {
        ElMessage.success('告警已升级')
        loadAlertDetail(id)
        loadAlerts()
      }
    } catch {
      ElMessage.error('升级失败')
    }
  } catch { /* cancelled */ }
}

async function createTicketFromAlert(alertId: string) {
  try {
    const { data } = await api.post(API.TICKETS, {
      title: `告警工单: ${selectedAlert.value?.title}`,
      alert_ids: JSON.stringify([alertId]),
    })
    if (data.code === 0) {
      ElMessage.success('工单已创建')
    }
  } catch {
    ElMessage.error('创建工单失败')
  }
}

// ─── AI Diagnosis ───
async function startAIDiagnosis() {
  if (!selectedAlert.value) {
    ElMessage.warning('请先选择告警')
    return
  }
  aiLoading.value = true
  try {
    const { data } = await api.post(API.AIOPS.DIAGNOSE, {
      alert_id: selectedAlert.value.id,
      alert_title: selectedAlert.value.title,
      alert_context: selectedAlert.value.context || '',
    })
    if (data.code === 0 && data.data) {
      aiResult.value = data.data
      ElMessage.success('AI 诊断分析完成')
    }
  } catch {
    aiResult.value = {
      root_cause: 'AI 服务暂不可用，请稍后重试',
      confidence: 0,
      recommendations: [],
    }
    ElMessage.error('AI 诊断服务异常')
  } finally {
    aiLoading.value = false
  }
}

// ─── Policy Matching ───
async function matchPolicy() {
  if (!selectedAlert.value) return
  try {
    const { data } = await api.get(API.POLICIES, { params: { page: 1, page_size: 50 } })
    if (data.code === 0) {
      const policies = data.data.items || []
      matchedPolicy.value = policies.length > 0 ? policies[0] : null
      if (matchedPolicy.value) {
        ElMessage.success(`匹配策略: ${matchedPolicy.value.name}`)
      } else {
        ElMessage.info('未找到匹配策略')
      }
    }
  } catch {
    ElMessage.error('策略匹配失败')
  }
}

async function applyPolicyNow() {
  if (!matchedPolicy.value || !selectedAlert.value) return
  applyingPolicy.value = true
  try {
    // First do a dry-run to validate
    const { data: simData } = await api.post(API.POLICY_SIMULATE(matchedPolicy.value.id), {
      trigger_event: selectedAlert.value.severity || 'alert',
      asset_ids: [selectedAlert.value.asset_id || 'test'],
    })
    if (simData.code !== 0) {
      ElMessage.warning('策略模拟执行未通过，请检查策略配置')
      applyingPolicy.value = false
      return
    }
    // If approval required, show approval dialog
    if (matchedPolicy.value.requires_approval) {
      applyingPolicy.value = false
      approvalVisible.value = true
      return
    }
    // Execute directly
    const scripts = parseActionChain(matchedPolicy.value.action_chain)
    if (scripts.length > 0) {
      const { data } = await api.post(API.EXECUTIONS, {
        execution_type: 'script',
        target_id: scripts[0].script_name || scripts[0].step,
        asset_ids: [selectedAlert.value.asset_id || 'test'],
        is_dry_run: false,
        policy_id: matchedPolicy.value.id,
      })
      if (data.code === 0) {
        ElMessage.success('策略已应用并执行')
        currentExecutionId.value = data.data.id
        executionRecords.value.unshift(data.data)
        loadExecutionLogs(data.data.id)
      }
    }
  } catch {
    ElMessage.error('策略应用失败')
  } finally {
    applyingPolicy.value = false
  }
}

// ─── Execution ───
async function executeDryRun() {
  if (!matchedPolicy.value) return
  try {
    const { data } = await api.post(API.POLICY_SIMULATE(matchedPolicy.value.id), {
      trigger_event: selectedAlert.value?.severity || 'alert',
      asset_ids: [selectedAlert.value?.asset_id || 'test'],
    })
    if (data.code === 0) {
      ElMessage.success('Dry-Run 预执行完成')
      logLines.value = typeof data.data === 'string' ? data.data.split('\n') : JSON.stringify(data.data, null, 2).split('\n')
    }
  } catch {
    ElMessage.error('Dry-Run 执行失败')
  }
}

function handleExecuteAction() {
  if (!matchedPolicy.value) return
  if (matchedPolicy.value.requires_approval) {
    approvalVisible.value = true
  } else {
    doExecute()
  }
}

function onApprovalConfirm(result: { decision: string; comment: string }) {
  if (result.decision === 'approved') {
    doExecute()
  } else {
    ElMessage.info('执行已驳回')
  }
  approvalVisible.value = false
}

async function doExecute() {
  if (!matchedPolicy.value) return
  const scripts = parseActionChain(matchedPolicy.value.action_chain)
  if (scripts.length > 0) {
    try {
      const { data } = await api.post(API.EXECUTIONS, {
        execution_type: 'script',
        target_id: scripts[0].script_name || scripts[0].step,
        asset_ids: [selectedAlert.value?.asset_id || 'test'],
        is_dry_run: false,
      })
      if (data.code === 0) {
        ElMessage.success('自动化执行已创建')
        currentExecutionId.value = data.data.id
        executionRecords.value.unshift(data.data)
        // Auto-load logs
        loadExecutionLogs(data.data.id)
      }
    } catch {
      ElMessage.error('执行创建失败')
    }
  }
}

// ─── Logs ───
async function loadExecutionLogs(execId: string) {
  logLoading.value = true
  currentExecutionId.value = execId
  try {
    const { data } = await api.get(API.LOGS.EXECUTION(execId))
    if (data.code === 0 && data.data) {
      const raw = data.data.content || data.data.log || data.data
      logLines.value = typeof raw === 'string' ? raw.split('\n') : JSON.stringify(raw, null, 2).split('\n')
    }
  } catch {
    logLines.value = ['[错误] 无法加载执行日志']
  } finally {
    logLoading.value = false
  }
}

// ─── Init: handle optional alertId from URL ───
onMounted(async () => {
  await loadAlerts()
  const alertId = route.query.alertId as string
  if (alertId) {
    loadAlertDetail(alertId)
  }
})
</script>

<style scoped>
.incident-response-page {
  padding: 0;
}

.page-header {
  margin-bottom: 16px;
}

.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  font-size: 18px;
  white-space: nowrap;
}

.header-alert-tag {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.alert-title-text {
  color: #606266;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-right {
  display: flex;
  gap: 8px;
}

.alert-quick-bar {
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.main-columns {
  margin-bottom: 16px;
}

.col-card {
  height: 100%;
}

.col-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.col-scroll {
  max-height: calc(100vh - 420px);
  overflow-y: auto;
  padding-right: 4px;
}

.evidence-col,
.action-col {
  display: flex;
  flex-direction: column;
}

.exec-record {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.exec-record:last-child {
  border-bottom: none;
}

.exec-record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.exec-time {
  color: #909399;
  font-size: 12px;
}

.exec-detail {
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
}

.log-stream-card {
  margin-top: 0;
}

.log-stream-controls {
  display: flex;
  align-items: center;
}

.related-logs-scroll {
  max-height: 240px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 13px;
  line-height: 1.6;
}

.log-entry {
  padding: 4px 0;
  border-bottom: 1px solid #f5f5f5;
  display: flex;
  align-items: baseline;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-time {
  color: #909399;
  font-size: 12px;
  white-space: nowrap;
}

.log-message {
  flex: 1;
  word-break: break-all;
}

.log-level-error .log-message {
  color: #f56c6c;
}

.log-level-warning .log-message {
  color: #e6a23c;
}

.log-level-info .log-message {
  color: #606266;
}

.log-level-debug .log-message {
  color: #909399;
}

.asset-change-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.change-asset {
  font-weight: 600;
  color: #303133;
}

.change-values {
  color: #606266;
}

.old-value {
  color: #f56c6c;
  text-decoration: line-through;
}

.new-value {
  color: #67c23a;
  font-weight: 600;
}

.trigger-cond {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 4px 0;
  font-size: 13px;
}
</style>
