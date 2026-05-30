<template>
  <div>
    <!-- 故障处置台 - 时间线 + 证据链 + AI 分析 + 策略 + 审批 + 执行控制 -->
    <el-row :gutter="16">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>故障处置工作台</span>
              <div>
                <el-button @click="loadAlerts">刷新</el-button>
                <el-button type="primary" @click="startAIDiagnosis" :loading="aiLoading">
                  AI 诊断分析
                </el-button>
              </div>
            </div>
          </template>

          <!-- 告警选择 -->
          <el-table :data="activeAlerts" highlight-current-row @current-change="selectAlert"
            max-height="300" v-loading="alertLoading" size="small">
            <el-table-column prop="severity" label="级别" width="80">
              <template #default="{ row }">
                <el-tag :type="row.severity==='critical'?'danger':'warning'" size="small">{{ row.severity }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="告警标题" min-width="200" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.status==='resolved'?'success':row.status==='acknowledged'?'warning':'danger'" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="触发时间" width="160">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 故障时间线 -->
        <el-card style="margin-top:16px" v-if="selectedAlert">
          <template #header><span>故障时间线</span></template>
          <el-timeline>
            <el-timeline-item v-for="(item, idx) in timeline" :key="idx"
              :type="item.type" :timestamp="item.time" placement="top">
              <el-card shadow="hover" :body-style="{padding:'12px'}">
                <div style="display:flex;justify-content:space-between;align-items:center">
                  <strong>{{ item.title }}</strong>
                  <el-tag size="small" :type="item.tagType">{{ item.tag }}</el-tag>
                </div>
                <p style="margin:4px 0 0;color:#666;font-size:13px">{{ item.detail }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-card>

        <!-- AI 诊断结果 -->
        <el-card style="margin-top:16px" v-if="aiResult">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>🤖 AI 诊断分析</span>
              <el-tag type="success">分析完成</el-tag>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="根因分析" :span="2">{{ aiResult.root_cause }}</el-descriptions-item>
            <el-descriptions-item label="置信度">
              <el-progress :percentage="aiResult.confidence || 85" :color="aiResult.confidence > 80 ? '#67c23a' : '#e6a23c'" />
            </el-descriptions-item>
            <el-descriptions-item label="影响范围">{{ aiResult.impact || '待评估' }}</el-descriptions-item>
          </el-descriptions>
          <div v-if="aiResult.recommendations" style="margin-top:12px">
            <h4>处置建议</h4>
            <el-table :data="aiResult.recommendations" size="small" stripe>
              <el-table-column prop="action" label="动作" min-width="200" />
              <el-table-column prop="risk" label="风险" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.risk==='high'?'danger':row.risk==='medium'?'warning':'success'" size="small">{{ row.risk }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="auto" label="可自动" width="80">
                <template #default="{ row }">{{ row.auto ? '✅' : '❌' }}</template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <!-- 快速操作面板 -->
        <el-card v-if="selectedAlert">
          <template #header><span>快速操作</span></template>
          <el-space direction="vertical" :size="12" style="width:100%">
            <el-button type="warning" style="width:100%" @click="acknowledgeAlert(selectedAlert.id)" :disabled="selectedAlert.status!=='firing'">
              确认告警
            </el-button>
            <el-button type="primary" style="width:100%" @click="matchPolicy" :disabled="!selectedAlert">
              策略匹配
            </el-button>
            <el-button type="success" style="width:100%" @click="executeDryRun" :disabled="!matchedPolicy">
              Dry-Run 预执行
            </el-button>
            <el-button type="danger" style="width:100%" @click="executeAction" :disabled="!matchedPolicy">
              执行自动化
            </el-button>
            <el-button style="width:100%" @click="createTicketFromAlert(selectedAlert.id)">
              转工单
            </el-button>
            <el-button type="success" style="width:100%" @click="resolveAlert(selectedAlert.id)" :disabled="selectedAlert.status==='resolved'">
              关闭告警
            </el-button>
          </el-space>
        </el-card>

        <!-- 策略匹配结果 -->
        <el-card style="margin-top:16px" v-if="matchedPolicy">
          <template #header><span>匹配策略</span></template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="策略名">{{ matchedPolicy.name }}</el-descriptions-item>
            <el-descriptions-item label="风险级别">
              <el-tag :type="matchedPolicy.risk_level==='high'?'danger':matchedPolicy.risk_level==='medium'?'warning':'success'" size="small">
                {{ matchedPolicy.risk_level }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="需审批">{{ matchedPolicy.requires_approval ? '是' : '否' }}</el-descriptions-item>
            <el-descriptions-item label="动作链">
              <div v-for="(a,i) in parseActionChain(matchedPolicy.action_chain)" :key="i" style="margin:2px 0">
                <el-tag size="small">{{ a.step }}</el-tag>
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 告警详情 -->
        <el-card style="margin-top:16px" v-if="selectedAlert">
          <template #header><span>告警上下文</span></template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="告警ID">{{ selectedAlert.id }}</el-descriptions-item>
            <el-descriptions-item label="标题">{{ selectedAlert.title }}</el-descriptions-item>
            <el-descriptions-item label="上下文">{{ selectedAlert.context || '无' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/shared/api/client'

const alertLoading = ref(false)
const activeAlerts = ref<any[]>([])
const selectedAlert = ref<any>(null)
const matchedPolicy = ref<any>(null)
const aiLoading = ref(false)
const aiResult = ref<any>(null)
const timeline = ref<any[]>([])

function formatTime(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '' }
function parseActionChain(s: string) {
  try { return JSON.parse(s) } catch { return [] }
}

async function loadAlerts() {
  alertLoading.value = true
  try {
    const { data } = await api.get('/api/v1/alerts', { params: { page: 1, page_size: 50 } })
    if (data.code === 0) activeAlerts.value = (data.data.items || []).filter((a: any) => a.status !== 'resolved')
  } finally { alertLoading.value = false }
}

function selectAlert(row: any) {
  selectedAlert.value = row
  matchedPolicy.value = null
  aiResult.value = null
  buildTimeline(row)
}

function buildTimeline(alert: any) {
  timeline.value = [
    { type: 'primary', tagType: 'info', tag: '事件', time: formatTime(alert.created_at), title: '告警触发', detail: alert.title },
    { type: 'warning', tagType: 'warning', tag: '分析中', time: '', title: '等待分析', detail: 'AI 正在分析根因...' },
  ]
}

async function acknowledgeAlert(id: string) {
  const { data } = await api.post(`/api/v1/alerts/${id}/acknowledge`)
  if (data.code === 0) { ElMessage.success('已确认'); loadAlerts() }
}

async function resolveAlert(id: string) {
  const { data } = await api.post(`/api/v1/alerts/${id}/resolve`)
  if (data.code === 0) { ElMessage.success('已关闭'); loadAlerts() }
}

async function createTicketFromAlert(alertId: string) {
  const { data } = await api.post('/api/v1/tickets', { title: `告警工单: ${selectedAlert.value?.title}`, alert_ids: JSON.stringify([alertId]) })
  if (data.code === 0) { ElMessage.success('工单已创建'); timeline.value.push({ type: 'primary', tagType: 'primary', tag: '工单', time: new Date().toLocaleString('zh-CN'), title: '创建工单', detail: data.data.id }) }
}

async function matchPolicy() {
  if (!selectedAlert.value) return
  const { data } = await api.get('/api/v1/policies', { params: { page: 1, page_size: 50 } })
  if (data.code === 0) {
    const policies = data.data.items || []
    matchedPolicy.value = policies.length > 0 ? policies[0] : null
    if (matchedPolicy.value) {
      ElMessage.success(`匹配策略: ${matchedPolicy.value.name}`)
      timeline.value.push({ type: 'success', tagType: 'success', tag: '策略', time: new Date().toLocaleString('zh-CN'), title: `策略匹配: ${matchedPolicy.value.name}`, detail: `风险: ${matchedPolicy.value.risk_level}` })
    }
  }
}

async function executeDryRun() {
  if (!matchedPolicy.value) return
  const { data } = await api.post(`/api/v1/policies/${matchedPolicy.value.id}/simulate`, {
    trigger_event: 'disk_usage_high', asset_ids: [selectedAlert.value?.asset_id || 'test']
  })
  if (data.code === 0) {
    ElMessage.success('Dry-Run 完成')
    timeline.value.push({ type: 'info', tagType: 'info', tag: 'Dry-Run', time: new Date().toLocaleString('zh-CN'), title: 'Dry-Run 预执行完成', detail: JSON.stringify(data.data) })
  }
}

async function executeAction() {
  if (!matchedPolicy.value) return
  if (matchedPolicy.value.requires_approval) {
    try {
      await ElMessageBox.confirm('此策略需要审批确认，是否继续？', '审批确认', { type: 'warning' })
    } catch { return }
  }
  const scripts = parseActionChain(matchedPolicy.value.action_chain)
  if (scripts.length > 0) {
    const { data } = await api.post('/api/v1/executions', {
      execution_type: 'script', target_id: scripts[0].script_name,
      asset_ids: [selectedAlert.value?.asset_id || 'test'], is_dry_run: false
    })
    if (data.code === 0) {
      ElMessage.success('执行已创建')
      timeline.value.push({ type: 'danger', tagType: 'danger', tag: '执行', time: new Date().toLocaleString('zh-CN'), title: '自动化执行已触发', detail: `执行ID: ${data.data.id}` })
    }
  }
}

async function startAIDiagnosis() {
  if (!selectedAlert.value) { ElMessage.warning('请先选择告警'); return }
  aiLoading.value = true
  try {
    const { data } = await api.post('/api/v1/aiops/diagnose', {
      alert_id: selectedAlert.value.id, alert_title: selectedAlert.value.title,
      alert_context: selectedAlert.value.context || ''
    })
    if (data.code === 0 && data.data) {
      aiResult.value = data.data
      timeline.value.push({ type: 'success', tagType: 'success', tag: 'AI', time: new Date().toLocaleString('zh-CN'), title: 'AI 诊断完成', detail: data.data.root_cause || '分析完成' })
    }
  } catch { aiResult.value = { root_cause: 'AI 服务暂不可用', confidence: 0, recommendations: [] } }
  finally { aiLoading.value = false }
}

onMounted(() => loadAlerts())
</script>
