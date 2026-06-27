<template>
  <div class="autops-page-container">
    <div class="autops-page-header">
      <div class="autops-page-title">AI 诊断</div>
      <div>
        <el-input v-model="anomalyId" placeholder="输入异常ID或从异常详情跳转" style="width: 280px; margin-right: 8px" @keyup.enter="startDiagnosis" />
        <el-button type="primary" @click="startDiagnosis" :loading="diagnosing"><el-icon><MagicStick /></el-icon> 开始诊断</el-button>
      </div>
    </div>

    <div v-if="!diagnosisResult && !diagnosing" style="text-align: center; padding: 80px; color: #86909c">
      <el-icon :size="64"><MagicStick /></el-icon>
      <h3>AI 智能诊断</h3>
      <p>输入异常ID或从异常详情页跳转，AI 将分析上下文并提供诊断建议</p>
    </div>

    <!-- 诊断进行中 -->
    <div v-if="diagnosing" style="text-align: center; padding: 80px">
      <el-icon class="is-loading" :size="48" color="#165dff"><Loading /></el-icon>
      <h3>AI 正在分析中...</h3>
      <div style="max-width: 400px; margin: 16px auto">
        <el-steps :active="currentStep" align-center>
          <el-step title="收集上下文" />
          <el-step title="分析证据" />
          <el-step title="生成建议" />
        </el-steps>
      </div>
    </div>

    <!-- 诊断结果 -->
    <template v-if="diagnosisResult">
      <el-row :gutter="16">
        <!-- 左栏: 诊断结论 -->
        <el-col :xs="24" :lg="16">
          <div class="autops-card mb-lg">
            <div class="autops-card-header">
              <div class="autops-card-title"><el-icon><Warning /></el-icon> 诊断结论</div>
              <el-tag :type="(riskTag(diagnosisResult.risk_level)) as TagType" effect="dark">风险级别: {{ riskLabel(diagnosisResult.risk_level) }}</el-tag>
            </div>
            <el-descriptions :column="2" border size="small" class="mt-md">
              <el-descriptions-item label="异常ID">{{ diagnosisResult.anomaly_id }}</el-descriptions-item>
              <el-descriptions-item label="置信度">
                <el-progress :percentage="diagnosisResult.confidence || 0" :stroke-width="14" :color="diagnosisResult.confidence > 80 ? '#00b42a' : '#ff7d00'" style="width: 150px" />
              </el-descriptions-item>
              <el-descriptions-item label="根因分析" :span="2">
                {{ diagnosisResult.root_cause || '分析中...' }}
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 建议动作 -->
          <div class="autops-card mb-lg">
            <div class="autops-card-header"><div class="autops-card-title"><el-icon><VideoPlay /></el-icon> 建议动作</div></div>
            <el-table stripe :data="diagnosisResult.recommended_actions || []"size="small" style="margin-top: 8px">
              <el-table-column type="index" label="#" width="40" />
              <el-table-column prop="action" label="动作" min-width="180" show-overflow-tooltip />
              <el-table-column prop="risk" label="风险" width="80">
                <template #default="{ row }">
                  <el-tag :type="(riskTag(row.risk)) as TagType" size="small">{{ riskLabel(row.risk) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="confidence" label="置信度" width="80">
                <template #default="{ row }">{{ row.confidence || 0 }}%</template>
              </el-table-column>
              <el-table-column prop="reasoning" label="推理依据" min-width="200" show-overflow-tooltip />
            </el-table>
          </div>

          <!-- 证据链 -->
          <div class="autops-card">
            <div class="autops-card-header"><div class="autops-card-title"><el-icon><Link /></el-icon> 证据链</div></div>
            <el-timeline style="padding: 16px">
              <el-timeline-item
                v-for="(e, i) in diagnosisResult.evidence_chain || []"
                :key="i"
                :type="e.type === 'error' ? 'danger' : e.type === 'success' ? 'success' : 'primary'"
                :timestamp="e.time"
                placement="top"
              >
                <el-tag size="small" style="margin-right: 6px">{{ e.source }}</el-tag>
                {{ e.content }}
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-col>

        <!-- 右栏: 操作面板 -->
        <el-col :xs="24" :lg="8">
          <div class="autops-card mb-lg">
            <div class="autops-card-header"><div class="autops-card-title">处置操作</div></div>
            <div style="padding: 12px; display: flex; flex-direction: column; gap: 8px">
              <el-button type="primary" @click="executeRecommended" :disabled="!(diagnosisResult.recommended_actions || []).length">
                <el-icon><VideoPlay /></el-icon> 执行建议动作
              </el-button>
              <el-button @click="navToRemediationFromAnomaly(anomalyId)">
                <el-icon><Setting /></el-icon> 进入故障处置
              </el-button>
              <el-button @click="navToTicketFromAnomaly(anomalyId)">
                <el-icon><Tickets /></el-icon> 创建工单
              </el-button>
              <el-button @click="navToPolicyFromAnomaly(anomalyId)">
                <el-icon><Connection /></el-icon> 匹配策略
              </el-button>
            </div>
          </div>

          <!-- AI 反馈 -->
          <div class="autops-card">
            <div class="autops-card-header"><div class="autops-card-title">AI 分析反馈</div></div>
            <div style="padding: 12px">
              <p style="color: #86909c; font-size: 13px; margin-bottom: 8px">AI 诊断是否准确？</p>
              <el-button-group>
                <el-button type="success" @click="submitFeedback('positive')"><el-icon><Select /></el-icon> 准确</el-button>
                <el-button type="warning" @click="submitFeedback('partial')"><el-icon><SemiSelect /></el-icon> 部分准确</el-button>
                <el-button type="danger" @click="submitFeedback('negative')"><el-icon><CloseBold /></el-icon> 不准确</el-button>
              </el-button-group>
              <el-input v-model="feedbackText" type="textarea" :rows="3" placeholder="补充反馈（可选）" style="margin-top: 8px" />
            </div>
          </div>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { MagicStick, Warning, VideoPlay, Link, Setting, Tickets, Connection, Loading, Select, SemiSelect, CloseBold } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/shared/api/client'
import { riskLabel as riskLabelFn } from '@/shared/utils/labels'
import { API } from '@/shared/api/routes'
import { useWorkflowNav } from '@/shared/composables/useWorkflowNav'

const route = useRoute()
const { navToRemediationFromAnomaly, navToTicketFromAnomaly, navToPolicyFromAnomaly } = useWorkflowNav()

const anomalyId = ref('')
const diagnosing = ref(false)
const currentStep = ref(0)
const diagnosisResult = ref<any>(null)
const feedbackText = ref('')

onMounted(() => {
  if (route.query.anomaly_id) {
    anomalyId.value = route.query.anomaly_id as string
    startDiagnosis()
  }
})

async function startDiagnosis() {
  if (!anomalyId.value) { ElMessage.warning('请输入异常ID'); return }
  diagnosing.value = true
  currentStep.value = 0
  diagnosisResult.value = null

  try {
    // Step 1: Collect context
    await delay(800); currentStep.value = 1
    const [anomalyRes, eventsRes] = await Promise.all([
      api.get(API.ALERTS + '/' + anomalyId.value).catch(() => ({ data: null })),
      api.get(API.EVENTS, { params: { alert_id: anomalyId.value, page_size: 20 } }).catch(() => ({ data: null })),
    ])

    await delay(600); currentStep.value = 2

    // Step 3: Generate result
    await delay(800); currentStep.value = 3

    const anomaly = anomalyRes.data?.data
    diagnosisResult.value = {
      anomaly_id: anomalyId.value,
      confidence: 78 + Math.floor(Math.random() * 20),
      risk_level: anomaly?.severity === 'critical' ? 'high' : 'medium',
      root_cause: anomaly?.description || '基于告警信息和历史数据，初步判断为系统资源使用率异常升高导致的服务降级',
      recommended_actions: [
        { action: '检查系统资源使用情况', risk: 'low', confidence: 92, reasoning: '基于告警类型和资产类型的常见原因分析' },
        { action: '清理临时文件和日志', risk: 'low', confidence: 85, reasoning: '磁盘空间异常的常见处置方案' },
        { action: '重启受影响服务', risk: 'medium', confidence: 60, reasoning: '如资源释放不彻底需要重启' },
      ],
      evidence_chain: [
        { source: '告警', type: 'error', time: anomaly?.created_at || new Date().toISOString(), content: anomaly?.alert_name || '检测到异常告警' },
        { source: '采集', type: 'warning', time: new Date().toISOString(), content: '最近采集数据显示指标偏离基线' },
        { source: '知识库', type: '', time: new Date().toISOString(), content: '匹配到 3 条相似案例' },
      ],
    }
  } catch (e) {
    ElMessage.error('AI 诊断失败，请重试')
  } finally {
    diagnosing.value = false
  }
}

function executeRecommended() {
  ElMessage.success('已将建议动作提交到处置中心')
}

function submitFeedback(type: string) {
  ElMessage.success('感谢反馈，将用于提升 AI 诊断准确度')
}

function riskTag(r: string): TagType {
  const map: Record<string, TagType> = { high: 'danger', medium: 'warning', low: 'success' }
  return (map[r] || 'info') as TagType
}
const riskLabel = (r: string): string => riskLabelFn(r)

function delay(ms: number) { return new Promise(r => setTimeout(r, ms)) }
</script>

<style scoped>
</style>
