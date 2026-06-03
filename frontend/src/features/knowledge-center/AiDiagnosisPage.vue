<template>
  <div class="aiops-page">
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">
          <el-icon style="margin-right: 6px"><MagicStick /></el-icon>
          AI 智能诊断
        </div>
        <div class="autops-page-desc">
          <template v-if="activeMode === 'analysis'">选择告警，由 AI 自动构建上下文并进行根因分析</template>
          <template v-else>输入运维任务，Agent 自主规划并执行多步骤排查</template>
        </div>
      </div>
    </div>

    <!-- Mode Tab Switch -->
    <div class="mode-tabs">
      <div
        class="mode-tab"
        :class="{ active: activeMode === 'analysis' }"
        @click="activeMode = 'analysis'"
      >
        <el-icon><DataAnalysis /></el-icon>
        分析模式
      </div>
      <div
        class="mode-tab"
        :class="{ active: activeMode === 'agent' }"
        @click="activeMode = 'agent'"
      >
        <el-icon><Promotion /></el-icon>
        Agent 模式
      </div>
    </div>

    <!-- ===================== 分析模式 ===================== -->
    <template v-if="activeMode === 'analysis'">
    <!-- Main Layout: Left (Workflow) + Right (History) -->
    <el-row :gutter="16">
      <!-- Left Column: Analysis Workflow -->
      <el-col :span="16">
        <!-- Step 1: Alert Selection -->
        <div class="autops-card workflow-card">
          
            <div class="autops-card-header">
              <span class="autops-card-title">
                <el-icon><Bell /></el-icon>
                选择告警
              </span>
              <el-button text type="primary" @click="loadAlerts" :loading="alertsLoading">
                <el-icon><Refresh /></el-icon>刷新
              </el-button>
            </div>
          

          <div class="alert-selector">
            <el-select
              v-model="selectedAlertId"
              placeholder="请选择需要 AI 分析的告警"
              filterable
              clearable
              style="width: 100%"
              @change="onAlertSelected"
            >
              <el-option
                v-for="alert in alerts"
                :key="alert.id"
                :label="alert.title || alert.name || `告警 #${alert.id}`"
                :value="alert.id"
              >
                <div class="alert-option">
                  <SeverityBadge :severity="alert.severity" size="small" />
                  <span class="alert-option-title">{{ alert.title || alert.name || `告警 #${alert.id}` }}</span>
                  <StatusBadge :status="alert.status" size="small" />
                  <span class="alert-option-time">{{ formatTime(alert.created_at) }}</span>
                </div>
              </el-option>
            </el-select>

            <el-button
              type="primary"
              :icon="Cpu"
              :disabled="!selectedAlertId"
              :loading="analyzing"
              @click="startAnalysis"
              style="margin-top: 12px"
            >
              开始 AI 分析
            </el-button>
          </div>
        </div>

        <!-- Step 2: Context Builder Panel -->
        <div class="autops-card workflow-card" v-if="context">
          
            <div class="autops-card-header">
              <span class="autops-card-title">
                <el-icon><FolderOpened /></el-icon>
                上下文构建
              </span>
              <el-tag type="info" size="small">
                已收集 {{ contextSourceCount }} 项上下文
              </el-tag>
            </div>
          

          <el-collapse v-model="expandedContextPanels">
            <!-- Alert Info -->
            <el-collapse-item name="alert" v-if="context.alert">
              <template #title>
                <div class="context-section-title">
                  <el-icon><Warning /></el-icon>
                  告警信息
                  <el-tag size="small" type="success">已加载</el-tag>
                </div>
              </template>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="标题">{{ context.alert.title }}</el-descriptions-item>
                <el-descriptions-item label="严重程度">
                  <SeverityBadge :severity="context.alert.severity" size="small" />
                </el-descriptions-item>
                <el-descriptions-item label="状态">
                  <StatusBadge :status="context.alert.status" size="small" />
                </el-descriptions-item>
                <el-descriptions-item label="时间">{{ formatTime(context.alert.created_at) }}</el-descriptions-item>
                <el-descriptions-item label="描述" :span="2">{{ context.alert.description || '-' }}</el-descriptions-item>
              </el-descriptions>
            </el-collapse-item>

            <!-- Related Asset -->
            <el-collapse-item name="asset" v-if="context.asset">
              <template #title>
                <div class="context-section-title">
                  <el-icon><Monitor /></el-icon>
                  关联资产
                  <el-tag size="small" type="success">已加载</el-tag>
                </div>
              </template>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="资产名称">{{ context.asset.name }}</el-descriptions-item>
                <el-descriptions-item label="类型">{{ context.asset.asset_type }}</el-descriptions-item>
                <el-descriptions-item label="IP">{{ context.asset.ip || '-' }}</el-descriptions-item>
                <el-descriptions-item label="状态">
                  <StatusBadge :status="context.asset.status" size="small" />
                </el-descriptions-item>
              </el-descriptions>
            </el-collapse-item>

            <!-- Recent Events -->
            <el-collapse-item name="events" v-if="context.recent_events?.length">
              <template #title>
                <div class="context-section-title">
                  <el-icon><Timer /></el-icon>
                  近期事件
                  <el-tag size="small" type="success">{{ context.recent_events.length }} 条</el-tag>
                </div>
              </template>
              <el-table stripe :data="context.recent_events" size="small"max-height="200">
                <el-table-column prop="title" label="事件" show-overflow-tooltip />
                <el-table-column prop="type" label="类型" width="120" />
                <el-table-column label="时间" width="170">
                  <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
                </el-table-column>
              </el-table>
            </el-collapse-item>

            <!-- Related Logs -->
            <el-collapse-item name="logs" v-if="context.logs?.length">
              <template #title>
                <div class="context-section-title">
                  <el-icon><Document /></el-icon>
                  相关日志
                  <el-tag size="small" type="success">{{ context.logs.length }} 条</el-tag>
                </div>
              </template>
              <div class="log-list">
                <div v-for="(log, idx) in context.logs" :key="idx" class="log-entry">
                  <span class="log-time">{{ log.timestamp || log.time }}</span>
                  <el-tag :type="log.level === 'error' ? 'danger' : log.level === 'warn' ? 'warning' : 'info'" size="small">
                    {{ log.level }}
                  </el-tag>
                  <span class="log-msg">{{ log.message }}</span>
                </div>
              </div>
            </el-collapse-item>

            <!-- Historical Knowledge -->
            <el-collapse-item name="knowledge" v-if="context.knowledge?.length">
              <template #title>
                <div class="context-section-title">
                  <el-icon><Reading /></el-icon>
                  历史知识
                  <el-tag size="small" type="success">{{ context.knowledge.length }} 篇</el-tag>
                </div>
              </template>
              <el-table stripe :data="context.knowledge" size="small"max-height="200">
                <el-table-column prop="title" label="标题" show-overflow-tooltip />
                <el-table-column prop="article_type" label="类型" width="120" />
                <el-table-column prop="risk_level" label="风险" width="80">
                  <template #default="{ row }">
                    <el-tag :type="riskTagType(row.risk_level)" size="small">{{ row.risk_level }}</el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </el-collapse-item>
          </el-collapse>
        </div>

        <!-- Step 3: Analysis Result -->
        <div class="autops-card workflow-card" v-if="analysisResult">
          
            <div class="autops-card-header">
              <span class="autops-card-title">
                <el-icon><MagicStick /></el-icon>
                AI 分析结果
              </span>
              <div class="result-meta">
                <el-tag
                  :type="analysisResult.confidence > 0.8 ? 'success' : analysisResult.confidence > 0.5 ? 'warning' : 'info'"
                  effect="dark"
                  size="small"
                >
                  置信度: {{ (analysisResult.confidence * 100).toFixed(0) }}%
                </el-tag>
                <el-tag type="info" size="small">{{ formatTime(analysisResult.analyzed_at) }}</el-tag>
              </div>
            </div>
          

          <!-- Root Cause -->
          <div class="result-section">
            <div class="section-label">根因分析</div>
            <div class="root-cause-content">{{ analysisResult.root_cause }}</div>
          </div>

          <!-- Evidence -->
          <div v-if="analysisResult.evidence?.length" class="result-section">
            <div class="section-label">关联证据</div>
            <el-timeline>
              <el-timeline-item
                v-for="(ev, idx) in analysisResult.evidence"
                :key="idx"
                :type="ev.type === 'critical' ? 'danger' : ev.type === 'warning' ? 'warning' : 'primary'"
              >
                <div class="evidence-item">
                  <strong v-if="ev.source">{{ ev.source }}：</strong>
                  {{ ev.description || ev.content || ev }}
                </div>
              </el-timeline-item>
            </el-timeline>
          </div>

          <!-- Recommended Actions -->
          <div v-if="analysisResult.recommended_actions?.length" class="result-section">
            <div class="section-label">建议操作</div>
            <div class="action-list">
              <div v-for="(action, idx) in analysisResult.recommended_actions" :key="idx" class="action-item">
                <div class="action-info">
                  <div class="action-header">
                    <span class="action-index">#{{ idx + 1 }}</span>
                    <span class="action-title">{{ action.title || action.name }}</span>
                    <el-tag :type="riskTagType(action.risk_level)" size="small">{{ riskLabel(action.risk_level) }}风险</el-tag>
                    <el-tag v-if="action.approval_required" type="warning" size="small" effect="dark">需要审批</el-tag>
                    <el-tag v-else type="success" size="small">自动执行</el-tag>
                  </div>
                  <div class="action-desc">{{ action.description }}</div>
                </div>
                <div class="action-buttons">
                  <!-- Create Ticket -->
                  <el-button
                    v-if="action.action_type === 'create_ticket'"
                    type="primary"
                    size="small"
                    :loading="actionExecuting[idx]"
                    @click="executeAction(idx, 'ticket', action)"
                  >
                    <el-icon><Tickets /></el-icon>创建工单
                  </el-button>
                  <!-- Trigger Policy -->
                  <el-button
                    v-if="action.action_type === 'trigger_policy'"
                    type="warning"
                    size="small"
                    :loading="actionExecuting[idx]"
                    @click="executeAction(idx, 'policy', action)"
                  >
                    <el-icon><SetUp /></el-icon>触发策略
                  </el-button>
                  <!-- Run Playbook -->
                  <el-button
                    v-if="action.action_type === 'run_playbook'"
                    type="success"
                    size="small"
                    :loading="actionExecuting[idx]"
                    @click="executeAction(idx, 'playbook', action)"
                  >
                    <el-icon><VideoPlay /></el-icon>执行 Playbook
                  </el-button>
                  <!-- Generic fallback -->
                  <el-button
                    v-if="!['create_ticket', 'trigger_policy', 'run_playbook'].includes(action.action_type)"
                    size="small"
                    :loading="actionExecuting[idx]"
                    @click="executeAction(idx, action.action_type, action)"
                  >
                    <el-icon><Position /></el-icon>执行
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <!-- Raw Response Toggle -->
          <el-collapse class="raw-collapse">
            <el-collapse-item name="raw">
              <template #title>
                <span class="raw-toggle">查看原始分析数据</span>
              </template>
              <JsonViewer :data="analysisResult" />
            </el-collapse-item>
          </el-collapse>

          <!-- Feedback Section -->
          <div class="feedback-section">
            <el-divider content-position="left">AI 反馈</el-divider>
            <div class="feedback-row">
              <span class="feedback-label">此分析是否有帮助？</span>
              <el-button-group>
                <el-button
                  :type="feedbackRating === 'helpful' ? 'success' : 'default'"
                  size="small"
                  @click="feedbackRating = 'helpful'"
                >
                  <el-icon><Select /></el-icon>有帮助
                </el-button>
                <el-button
                  :type="feedbackRating === 'not_helpful' ? 'danger' : 'default'"
                  size="small"
                  @click="feedbackRating = 'not_helpful'"
                >
                  <el-icon><CloseBold /></el-icon>无帮助
                </el-button>
              </el-button-group>
            </div>
            <el-input
              v-model="feedbackComment"
              type="textarea"
              :rows="2"
              placeholder="请输入您的反馈意见（可选）"
              style="margin-top: 8px"
            />
            <el-button
              type="primary"
              size="small"
              style="margin-top: 8px"
              :disabled="!feedbackRating"
              :loading="submittingFeedback"
              @click="submitFeedback"
            >
              提交反馈
            </el-button>
          </div>
        </div>
      </el-col>

      <!-- Right Column: History -->
      <el-col :span="8">
        <div class="autops-card history-card">
          
            <div class="autops-card-header">
              <span class="autops-card-title">
                <el-icon><Clock /></el-icon>
                近期分析记录
              </span>
              <el-button text type="primary" size="small" @click="loadHistory" :loading="historyLoading">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          

          <div v-loading="historyLoading">
            <el-empty v-if="!historyLoading && (!historyList || !historyList.length)" description="暂无分析记录" :image-size="80" />

            <div v-else class="history-list">
              <div
                v-for="item in historyList"
                :key="item.id"
                class="history-item"
                :class="{ active: analysisResult && analysisResult.id === item.id }"
                @click="loadAnalysisDetail(item.id)"
              >
                <div class="history-item-header">
                  <span class="history-alert-title">{{ item.alert_title || item.title || `分析 #${item.id}` }}</span>
                  <el-tag
                    :type="item.confidence > 0.8 ? 'success' : item.confidence > 0.5 ? 'warning' : 'info'"
                    size="small"
                  >
                    {{ item.confidence ? (item.confidence * 100).toFixed(0) + '%' : '-' }}
                  </el-tag>
                </div>
                <div class="history-item-summary">{{ item.result_summary || item.summary || '-' }}</div>
                <div class="history-item-time">{{ formatTime(item.created_at || item.analyzed_at) }}</div>
                <div v-if="item.feedback" class="history-feedback-badge">
                  <el-tag :type="item.feedback.rating === 'helpful' ? 'success' : 'danger'" size="small" effect="plain">
                    {{ item.feedback.rating === 'helpful' ? '已反馈: 有帮助' : '已反馈: 无帮助' }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
    </template>

    <!-- ===================== Agent 模式 ===================== -->
    <template v-if="activeMode === 'agent'">
    <el-row :gutter="16">
      <!-- Left Column: Agent Task + Process -->
      <el-col :span="16">
        <!-- Task Input -->
        <div class="autops-card workflow-card">
          
            <div class="autops-card-header">
              <span class="autops-card-title">
                <el-icon><EditPen /></el-icon>
                任务输入
              </span>
            </div>
          
          <el-input
            v-model="agentTask"
            type="textarea"
            :rows="4"
            placeholder="请描述您的运维任务，例如：排查 web-server-01 CPU 持续飙高的原因并给出修复建议"
            :disabled="agentRunning"
          />
          <div class="agent-input-actions">
            <el-button
              type="primary"
              :icon="Promotion"
              :loading="agentRunning"
              :disabled="!agentTask.trim()"
              @click="runAgent"
            >
              {{ agentRunning ? 'Agent 运行中...' : '运行 Agent' }}
            </el-button>
            <el-button
              v-if="agentRunning"
              type="danger"
              @click="cancelAgent"
            >
              取消运行
            </el-button>
          </div>
        </div>

        <!-- Thinking Process (Real-time Steps) -->
        <div class="autops-card workflow-card" v-if="agentSteps.length > 0">
          
            <div class="autops-card-header">
              <span class="autops-card-title">
                <el-icon><Cpu /></el-icon>
                思考过程
              </span>
              <el-tag v-if="agentRunning" type="warning" effect="dark" size="small">
                <el-icon class="is-loading"><Loading /></el-icon>
                运行中
              </el-tag>
              <el-tag v-else type="success" effect="dark" size="small">已完成</el-tag>
            </div>
          
          <el-timeline>
            <el-timeline-item
              v-for="(step, idx) in agentSteps"
              :key="idx"
              :type="step.status === 'error' ? 'danger' : step.status === 'running' ? 'warning' : 'success'"
              :hollow="step.status === 'running'"
            >
              <div class="agent-step">
                <div class="agent-step-header">
                  <span class="agent-step-index">Step {{ idx + 1 }}</span>
                  <span class="agent-step-action">{{ step.action }}</span>
                  <el-tag
                    v-if="step.status === 'running'"
                    type="warning"
                    size="small"
                    effect="plain"
                  >
                    <el-icon class="is-loading"><Loading /></el-icon>
                    执行中
                  </el-tag>
                  <el-tag v-else-if="step.status === 'done'" type="success" size="small" effect="plain">完成</el-tag>
                  <el-tag v-else-if="step.status === 'error'" type="danger" size="small" effect="plain">失败</el-tag>
                </div>
                <div v-if="step.thought" class="agent-step-thought">
                  <strong>思考：</strong>{{ step.thought }}
                </div>
                <div v-if="step.observation" class="agent-step-observation">
                  <strong>观察：</strong>{{ step.observation }}
                </div>
                <div v-if="step.tool" class="agent-step-tool">
                  <el-tag size="small" effect="plain" type="info">
                    <el-icon><SetUp /></el-icon>
                    {{ step.tool }}
                  </el-tag>
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>

        <!-- Final Conclusion -->
        <div class="autops-card workflow-card" v-if="agentConclusion">
          
            <div class="autops-card-header">
              <span class="autops-card-title">
                <el-icon><Finished /></el-icon>
                最终结论
              </span>
              <el-tag type="info" size="small">{{ formatTime(agentConclusion.completed_at) }}</el-tag>
            </div>
          
          <div class="agent-conclusion-summary">{{ agentConclusion.summary }}</div>
          <div v-if="agentConclusion.actions?.length" class="result-section" style="margin-top: 16px;">
            <div class="section-label">建议操作</div>
            <div class="action-list">
              <div v-for="(act, idx) in agentConclusion.actions" :key="idx" class="action-item">
                <div class="action-info">
                  <div class="action-header">
                    <span class="action-index">#{{ idx + 1 }}</span>
                    <span class="action-title">{{ act.title || act.name }}</span>
                  </div>
                  <div v-if="act.description" class="action-desc">{{ act.description }}</div>
                </div>
              </div>
            </div>
          </div>
          <!-- Raw Response -->
          <el-collapse class="raw-collapse" style="margin-top: 16px;">
            <el-collapse-item name="raw">
              <template #title>
                <span class="raw-toggle">查看原始数据</span>
              </template>
              <JsonViewer :data="agentConclusion" />
            </el-collapse-item>
          </el-collapse>
        </div>
      </el-col>

      <!-- Right Column: Agent History -->
      <el-col :span="8">
        <div class="autops-card history-card">
          
            <div class="autops-card-header">
              <span class="autops-card-title">
                <el-icon><Clock /></el-icon>
                Agent 运行历史
              </span>
              <el-button text type="primary" size="small" @click="loadAgentHistory" :loading="agentHistoryLoading">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          
          <div v-loading="agentHistoryLoading">
            <el-empty v-if="!agentHistoryLoading && !agentHistoryList.length" description="暂无 Agent 运行记录" :image-size="80" />
            <div v-else class="history-list">
              <div
                v-for="item in agentHistoryList"
                :key="item.id"
                class="history-item"
                :class="{ active: agentConclusion && agentConclusion.id === item.id }"
                @click="loadAgentResult(item.id)"
              >
                <div class="history-item-header">
                  <span class="history-alert-title">{{ item.task_summary || item.task || `任务 #${item.id}` }}</span>
                  <el-tag
                    :type="item.status === 'completed' ? 'success' : item.status === 'failed' ? 'danger' : 'warning'"
                    size="small"
                  >
                    {{ item.status === 'completed' ? '完成' : item.status === 'failed' ? '失败' : '运行中' }}
                  </el-tag>
                </div>
                <div class="history-item-summary">{{ item.summary || '-' }}</div>
                <div class="history-item-time">{{ formatTime(item.created_at || item.completed_at) }}</div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import {
  MagicStick, Bell, Refresh, Cpu, FolderOpened, Warning, Monitor,
  Timer, Document, Reading, Tickets, SetUp, VideoPlay, Position,
  Select, CloseBold, Clock, DataAnalysis, Promotion, EditPen,
  Loading, Finished,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import SeverityBadge from '@/shared/components/SeverityBadge.vue'
import JsonViewer from '@/shared/components/JsonViewer.vue'

// ─── Types ───────────────────────────────────────────────────────────
interface Alert {
  id: string
  title?: string
  name?: string
  severity: string
  status: string
  description?: string
  asset_id?: string
  created_at: string
}

interface Asset {
  id: string
  name: string
  asset_type: string
  ip?: string
  status: string
}

interface LogEntry {
  timestamp?: string
  time?: string
  level: string
  message: string
}

interface KnowledgeRef {
  id: string
  title: string
  article_type: string
  risk_level: string
}

interface AnalysisContext {
  alert: Alert | null
  asset: Asset | null
  recent_events: Array<any>
  logs: LogEntry[]
  knowledge: KnowledgeRef[]
}

interface RecommendedAction {
  title?: string
  name?: string
  description?: string
  action_type: 'create_ticket' | 'trigger_policy' | 'run_playbook' | string
  risk_level: string
  approval_required: boolean
  target_id?: string
  params?: Record<string, any>
}

interface AnalysisResult {
  id: string
  root_cause: string
  confidence: number
  evidence: Array<{ source?: string; description?: string; content?: string; type?: string } | string>
  recommended_actions: RecommendedAction[]
  result_summary?: string
  summary?: string
  analyzed_at: string
  alert_title?: string
  title?: string
  alert_id?: string
  feedback?: { rating: string; comment?: string }
}

interface HistoryItem {
  id: string
  alert_title?: string
  title?: string
  result_summary?: string
  summary?: string
  confidence?: number
  created_at?: string
  analyzed_at?: string
  feedback?: { rating: string; comment?: string }
}

// ─── State ───────────────────────────────────────────────────────────
// Mode switch
const activeMode = ref<'analysis' | 'agent'>('analysis')

// --- Analysis mode state ---
const alerts = ref<Alert[]>([])
const alertsLoading = ref(false)
const selectedAlertId = ref<string>('')

const context = ref<AnalysisContext | null>(null)
const expandedContextPanels = ref<string[]>(['alert', 'asset'])

const analyzing = ref(false)
const analysisResult = ref<AnalysisResult | null>(null)

const feedbackRating = ref<'helpful' | 'not_helpful' | ''>('')
const feedbackComment = ref('')
const submittingFeedback = ref(false)

const historyList = ref<HistoryItem[]>([])
const historyLoading = ref(false)

const actionExecuting = ref<Record<number, boolean>>({})

// ─── Agent Mode Types ────────────────────────────────────────────────
interface AgentStep {
  action: string
  thought?: string
  observation?: string
  tool?: string
  status: 'running' | 'done' | 'error'
}

interface AgentConclusion {
  id: string
  summary: string
  actions?: Array<{ title?: string; name?: string; description?: string }>
  completed_at: string
  [key: string]: any
}

interface AgentHistoryItem {
  id: string
  task?: string
  task_summary?: string
  summary?: string
  status: string
  created_at?: string
  completed_at?: string
}

// ─── Agent Mode State ────────────────────────────────────────────────
const agentTask = ref('')
const agentRunning = ref(false)
const agentSteps = ref<AgentStep[]>([])
const agentConclusion = ref<AgentConclusion | null>(null)
const agentHistoryList = ref<AgentHistoryItem[]>([])
const agentHistoryLoading = ref(false)
let agentPollTimer: ReturnType<typeof setInterval> | null = null

// ─── Agent: Run Task ────────────────────────────────────────────────
async function runAgent() {
  const task = agentTask.value.trim()
  if (!task) return

  agentRunning.value = true
  agentSteps.value = []
  agentConclusion.value = null

  try {
    const { data } = await api.post(R.AIOPS.AGENT_RUN, { task })
    if (data.code === 0) {
      const runId = data.data?.id || data.data?.task_id
      ElMessage.success('Agent 任务已提交')
      // Start polling for steps & result
      startAgentPolling(runId)
    } else {
      ElMessage.error(data.message || 'Agent 启动失败')
      agentRunning.value = false
    }
  } catch (e: any) {
    ElMessage.error('Agent 启动失败: ' + (e.message || e))
    agentRunning.value = false
  }
}

function startAgentPolling(runId: string) {
  // Poll every 2 seconds
  agentPollTimer = setInterval(async () => {
    try {
      const { data } = await api.get(R.AIOPS.AGENT_RESULTS, {
        params: { task_id: runId },
      })
      if (data.code === 0) {
        const result = data.data
        // Update steps
        if (result.steps?.length) {
          agentSteps.value = result.steps.map((s: any) => ({
            action: s.action || s.name || '',
            thought: s.thought || s.reasoning || '',
            observation: s.observation || s.result || '',
            tool: s.tool || s.tool_name || '',
            status: s.status || (s.error ? 'error' : 'done'),
          }))
        }
        // Check completion
        if (result.status === 'completed' || result.conclusion) {
          agentConclusion.value = {
            id: result.id || runId,
            summary: result.conclusion || result.summary || '',
            actions: result.actions || [],
            completed_at: result.completed_at || new Date().toISOString(),
            ...result,
          }
          stopAgentPolling()
          agentRunning.value = false
          loadAgentHistory()
        } else if (result.status === 'failed') {
          stopAgentPolling()
          agentRunning.value = false
          ElMessage.error('Agent 运行失败: ' + (result.error || '未知错误'))
        }
      }
    } catch {
      // Continue polling on transient errors
    }
  }, 2000)
}

function stopAgentPolling() {
  if (agentPollTimer) {
    clearInterval(agentPollTimer)
    agentPollTimer = null
  }
}

function cancelAgent() {
  stopAgentPolling()
  agentRunning.value = false
  ElMessage.info('Agent 运行已取消')
}

// ─── Agent: Load History ────────────────────────────────────────────
async function loadAgentHistory() {
  agentHistoryLoading.value = true
  try {
    const { data } = await api.get(R.AIOPS.AGENT_RESULTS, {
      params: { page_size: 20 },
    })
    if (data.code === 0) {
      agentHistoryList.value = data.data?.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载 Agent 历史失败: ' + (e.message || e))
  } finally {
    agentHistoryLoading.value = false
  }
}

// ─── Agent: Load Single Result ──────────────────────────────────────
async function loadAgentResult(id: string) {
  try {
    const { data } = await api.get(R.AIOPS.AGENT_RESULTS, {
      params: { task_id: id },
    })
    if (data.code === 0) {
      const result = data.data
      if (result.steps?.length) {
        agentSteps.value = result.steps.map((s: any) => ({
          action: s.action || s.name || '',
          thought: s.thought || s.reasoning || '',
          observation: s.observation || s.result || '',
          tool: s.tool || s.tool_name || '',
          status: s.status || (s.error ? 'error' : 'done'),
        }))
      }
      agentConclusion.value = {
        id: result.id || id,
        summary: result.conclusion || result.summary || '',
        actions: result.actions || [],
        completed_at: result.completed_at || '',
        ...result,
      }
    }
  } catch (e: any) {
    ElMessage.error('加载 Agent 结果失败: ' + (e.message || e))
  }
}

// ─── Computed ────────────────────────────────────────────────────────
const contextSourceCount = computed(() => {
  if (!context.value) return 0
  let count = 0
  if (context.value.alert) count++
  if (context.value.asset) count++
  if (context.value.recent_events?.length) count++
  if (context.value.logs?.length) count++
  if (context.value.knowledge?.length) count++
  return count
})

// ─── Helpers ─────────────────────────────────────────────────────────
function formatTime(t: string | undefined): string {
  return t ? new Date(t).toLocaleString('zh-CN') : '-'
}

function riskTagType(level: string): string {
  if (level === 'high') return 'danger'
  if (level === 'medium') return 'warning'
  return 'info'
}

function riskLabel(level: string): string {
  const m: Record<string, string> = { high: '高', medium: '中', low: '低' }
  return m[level] || level
}

// ─── Load Alerts ─────────────────────────────────────────────────────
async function loadAlerts() {
  alertsLoading.value = true
  try {
    const { data } = await api.get(R.ALERTS, { params: { page_size: 50, status: 'firing' } })
    if (data.code === 0) {
      alerts.value = data.data?.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载告警列表失败: ' + (e.message || e))
  } finally {
    alertsLoading.value = false
  }
}

// ─── Alert Selection → Build Context ─────────────────────────────────
async function onAlertSelected(alertId: string) {
  if (!alertId) {
    context.value = null
    analysisResult.value = null
    return
  }

  context.value = null
  expandedContextPanels.value = ['alert', 'asset']

  const alert = alerts.value.find((a) => a.id === alertId)
  if (!alert) return

  // Build context object with alert info first
  const ctx: AnalysisContext = {
    alert,
    asset: null,
    recent_events: [],
    logs: [],
    knowledge: [],
  }

  // Parallel load: asset, events, logs, knowledge
  const promises: Promise<void>[] = []

  // Load related asset
  if (alert.asset_id) {
    promises.push(
      api.get(R.ASSET_DETAIL(alert.asset_id)).then(({ data }) => {
        if (data.code === 0) ctx.asset = data.data
      }).catch(() => {})
    )
  }

  // Load recent events for the asset
  if (alert.asset_id) {
    promises.push(
      api.get(R.EVENTS, { params: { asset_id: alert.asset_id, page_size: 10 } }).then(({ data }) => {
        if (data.code === 0) ctx.recent_events = data.data?.items || data.data || []
      }).catch(() => {})
    )
  }

  // Load related logs (use events as proxy if no direct log endpoint available)
  promises.push(
    api.get(R.EVENTS, { params: { alert_id: alertId, page_size: 20 } }).then(({ data }) => {
      if (data.code === 0) {
        const events = data.data?.items || data.data || []
        ctx.logs = events.map((e: any) => ({
          timestamp: e.created_at,
          level: e.severity || 'info',
          message: e.description || e.title || '',
        }))
      }
    }).catch(() => {})
  )

  // Load historical knowledge
  promises.push(
    api.get(R.KNOWLEDGE, { params: { page_size: 5, status: 'published' } }).then(({ data }) => {
      if (data.code === 0) ctx.knowledge = data.data?.items || data.data || []
    }).catch(() => {})
  )

  await Promise.allSettled(promises)
  context.value = ctx
}

// ─── Start AI Analysis ──────────────────────────────────────────────
async function startAnalysis() {
  if (!selectedAlertId.value) return

  analyzing.value = true
  analysisResult.value = null
  feedbackRating.value = ''
  feedbackComment.value = ''

  try {
    // Ensure context is built before analysis
    if (!context.value) {
      await onAlertSelected(selectedAlertId.value)
    }

    const payload: Record<string, any> = {
      alert_id: selectedAlertId.value,
      context: context.value,
    }

    const { data } = await api.post(R.AIOPS.DIAGNOSE, payload)
    if (data.code === 0) {
      const result = data.data
      analysisResult.value = result
      ElMessage.success('AI 分析完成')
      // Refresh history
      loadHistory()
    }
  } catch (e: any) {
    ElMessage.error('AI 分析失败: ' + (e.message || e))
  } finally {
    analyzing.value = false
  }
}

// ─── Load Analysis Detail (from history) ─────────────────────────────
async function loadAnalysisDetail(id: string) {
  try {
    const { data } = await api.get(R.AIOPS.ANALYSIS_DETAIL(id))
    if (data.code === 0) {
      analysisResult.value = data.data
      feedbackRating.value = ''
      feedbackComment.value = ''
    }
  } catch (e: any) {
    ElMessage.error('加载分析详情失败: ' + (e.message || e))
  }
}

// ─── Execute Recommended Action ──────────────────────────────────────
async function executeAction(index: number, actionType: string, action: RecommendedAction) {
  const actionLabels: Record<string, string> = {
    ticket: '创建工单',
    policy: '触发策略',
    playbook: '执行 Playbook',
  }
  const label = actionLabels[actionType] || '执行操作'

  // Check if approval required
  if (action.approval_required) {
    try {
      await ElMessageBox.confirm(
        `该操作风险等级为「${riskLabel(action.risk_level)}」，需要确认后执行。是否继续？`,
        '操作确认',
        { confirmButtonText: '确认执行', cancelButtonText: '取消', type: 'warning' }
      )
    } catch {
      return // User cancelled
    }
  }

  actionExecuting.value[index] = true

  try {
    let response: any

    switch (actionType) {
      case 'ticket': {
        response = await api.post(R.TICKETS, {
          title: action.title || action.name || 'AI 诊断自动创建工单',
          description: action.description,
          alert_id: selectedAlertId.value,
          source: 'aiops',
          priority: action.risk_level === 'high' ? 'urgent' : action.risk_level === 'medium' ? 'high' : 'normal',
        })
        break
      }
      case 'policy': {
        const policyId = action.target_id
        if (policyId) {
          response = await api.post(R.POLICY_SIMULATE(policyId), {
            alert_id: selectedAlertId.value,
            params: action.params,
          })
        } else {
          // Trigger a generic policy action
          response = await api.post(R.EXECUTIONS, {
            type: 'policy',
            target_id: action.target_id,
            alert_id: selectedAlertId.value,
            params: action.params,
            source: 'aiops',
          })
        }
        break
      }
      case 'playbook': {
        response = await api.post(R.EXECUTIONS, {
          type: 'playbook',
          playbook_id: action.target_id,
          alert_id: selectedAlertId.value,
          params: action.params,
          source: 'aiops',
        })
        break
      }
      default: {
        // Generic execution
        response = await api.post(R.EXECUTIONS, {
          type: actionType,
          target_id: action.target_id,
          alert_id: selectedAlertId.value,
          params: action.params,
          source: 'aiops',
        })
      }
    }

    if (response.data?.code === 0) {
      ElMessage.success(`${label}成功`)
    }
  } catch (e: any) {
    ElMessage.error(`${label}失败: ` + (e.message || e))
  } finally {
    actionExecuting.value[index] = false
  }
}

// ─── Submit Feedback ─────────────────────────────────────────────────
async function submitFeedback() {
  if (!feedbackRating.value || !analysisResult.value) return

  submittingFeedback.value = true
  try {
    const { data } = await api.post(R.AIOPS.FEEDBACK(analysisResult.value.id), {
      rating: feedbackRating.value,
      comment: feedbackComment.value,
    })
    if (data.code === 0) {
      ElMessage.success('反馈已提交，感谢您的评价')
      // Update local state
      if (analysisResult.value) {
        analysisResult.value.feedback = { rating: feedbackRating.value, comment: feedbackComment.value }
      }
      // Refresh history to show feedback badge
      loadHistory()
    }
  } catch (e: any) {
    ElMessage.error('提交反馈失败: ' + (e.message || e))
  } finally {
    submittingFeedback.value = false
  }
}

// ─── Load History ────────────────────────────────────────────────────
async function loadHistory() {
  historyLoading.value = true
  try {
    const { data } = await api.get(R.AIOPS.ANALYSES, { params: { page_size: 20 } })
    if (data.code === 0) {
      historyList.value = data.data?.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载分析历史失败: ' + (e.message || e))
  } finally {
    historyLoading.value = false
  }
}

// ─── Init ────────────────────────────────────────────────────────────
onMounted(() => {
  loadAlerts()
  loadHistory()
  loadAgentHistory()
})

onUnmounted(() => {
  stopAgentPolling()
})

// Load agent history when switching to agent mode
watch(activeMode, (mode) => {
  if (mode === 'agent' && !agentHistoryList.value.length) {
    loadAgentHistory()
  }
})
</script>

<style scoped>
.aiops-page {
  padding: 0;
}

.page-top {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1d2129;
  display: flex;
  align-items: center;
}

/* Cards */
.workflow-card {
  margin-bottom: 16px;
}
/* Alert Selector */
.alert-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.alert-option-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.alert-option-time {
  color: #86909c;
  font-size: 12px;
}

/* Context Panel */
.context-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #1d2129;
}

.log-list {
  max-height: 200px;
  overflow-y: auto;
}

.log-entry {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}

.log-time {
  color: #86909c;
  white-space: nowrap;
  min-width: 150px;
}

.log-msg {
  color: #4e5969;
  word-break: break-all;
}

/* Analysis Result */
.result-section {
  margin-bottom: 20px;
}

.section-label {
  font-weight: 600;
  font-size: 14px;
  color: #1d2129;
  margin-bottom: 8px;
  padding-bottom: 4px;
  border-bottom: 2px solid #165dff;
  display: inline-block;
}

.root-cause-content {
  color: #4e5969;
  line-height: 1.8;
  padding: 8px 12px;
  background: #f0f9eb;
  border-radius: 6px;
  border-left: 3px solid #00b42a;
}

.evidence-item {
  color: #4e5969;
  line-height: 1.6;
}

/* Actions */
.action-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #e5e6eb;
  transition: box-shadow 0.2s;
}

.action-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.action-info {
  flex: 1;
}

.action-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.action-index {
  font-weight: 700;
  color: #165dff;
}

.action-title {
  font-weight: 600;
  color: #1d2129;
}

.action-desc {
  color: #86909c;
  font-size: 13px;
  margin-top: 4px;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 16px;
  flex-shrink: 0;
}

/* Result Meta */
.result-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Raw Toggle */
.raw-collapse {
  margin-bottom: 16px;
}

.raw-toggle {
  font-size: 13px;
  color: #86909c;
}

/* Feedback */
.feedback-section {
  margin-top: 8px;
}

.feedback-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.feedback-label {
  font-size: 14px;
  color: #4e5969;
  font-weight: 500;
}

/* History */
.history-card {
  position: sticky;
  top: 16px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #e5e6eb;
  cursor: pointer;
  transition: all 0.2s;
}

.history-item:hover {
  border-color: #165dff;
  background: #ecf5ff;
}

.history-item.active {
  border-color: #165dff;
  background: #ecf5ff;
  box-shadow: 0 0 0 1px #165dff;
}

.history-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.history-alert-title {
  font-weight: 600;
  font-size: 13px;
  color: #1d2129;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 8px;
}

.history-item-summary {
  font-size: 12px;
  color: #86909c;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  margin-bottom: 4px;
}

.history-item-time {
  font-size: 12px;
  color: #c9cdd4;
}

.history-feedback-badge {
  margin-top: 4px;
}

/* ─── Mode Tabs ────────────────────────────────────────────────────── */
.mode-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 16px;
  border-bottom: 2px solid #e5e6eb;
}

.mode-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 500;
  color: #86909c;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
  user-select: none;
}

.mode-tab:hover {
  color: #165dff;
}

.mode-tab.active {
  color: #165dff;
  border-bottom-color: #165dff;
}

/* ─── Agent Mode ───────────────────────────────────────────────────── */
.agent-input-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}

.agent-step {
  padding: 4px 0;
}

.agent-step-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.agent-step-index {
  font-weight: 700;
  color: #165dff;
  font-size: 13px;
  white-space: nowrap;
}

.agent-step-action {
  font-weight: 600;
  color: #1d2129;
  font-size: 14px;
}

.agent-step-thought {
  color: #4e5969;
  font-size: 13px;
  line-height: 1.6;
  padding: 6px 10px;
  background: #fdf6ec;
  border-radius: 4px;
  margin: 4px 0;
  border-left: 3px solid #ff7d00;
}

.agent-step-observation {
  color: #4e5969;
  font-size: 13px;
  line-height: 1.6;
  padding: 6px 10px;
  background: #f0f9eb;
  border-radius: 4px;
  margin: 4px 0;
  border-left: 3px solid #00b42a;
}

.agent-step-tool {
  margin-top: 4px;
}

.agent-conclusion-summary {
  color: #1d2129;
  line-height: 1.8;
  padding: 12px 16px;
  background: #ecf5ff;
  border-radius: 8px;
  border-left: 4px solid #165dff;
  font-size: 14px;
  white-space: pre-wrap;
}
</style>
