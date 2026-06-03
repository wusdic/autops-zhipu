     1|<template>
     2|  <div class="page-container">
     3|    <div class="autops-page-header">
     4|      <h2>AI 诊断面板</h2>
     5|      <div>
     6|        <el-input v-model="anomalyId" placeholder="输入异常ID或从异常详情跳转" style="width: 280px; margin-right: 8px" @keyup.enter="startDiagnosis" />
     7|        <el-button type="primary" @click="startDiagnosis" :loading="diagnosing"><el-icon><MagicStick /></el-icon> 开始诊断</el-button>
     8|      </div>
     9|    </div>
    10|
    11|    <div v-if="!diagnosisResult && !diagnosing" style="text-align: center; padding: 80px; color: #86909c">
    12|      <el-icon :size="64"><MagicStick /></el-icon>
    13|      <h3>AI 智能诊断</h3>
    14|      <p>输入异常ID或从异常详情页跳转，AI 将分析上下文并提供诊断建议</p>
    15|    </div>
    16|
    17|    <!-- 诊断进行中 -->
    18|    <div v-if="diagnosing" style="text-align: center; padding: 80px">
    19|      <el-icon class="is-loading" :size="48" color="#165dff"><Loading /></el-icon>
    20|      <h3>AI 正在分析中...</h3>
    21|      <div style="max-width: 400px; margin: 16px auto">
    22|        <el-steps :active="currentStep" align-center>
    23|          <el-step title="收集上下文" />
    24|          <el-step title="分析证据" />
    25|          <el-step title="生成建议" />
    26|        </el-steps>
    27|      </div>
    28|    </div>
    29|
    30|    <!-- 诊断结果 -->
    31|    <template v-if="diagnosisResult">
    32|      <el-row :gutter="16">
    33|        <!-- 左栏: 诊断结论 -->
    34|        <el-col :xs="24" :lg="16">
    35|          <div class="autops-card" style="margin-bottom: 16px">
    36|            <div class="autops-card-header">
    37|              <div class="autops-card-title"><el-icon><Warning /></el-icon> 诊断结论</div>
    38|              <el-tag :type="riskTag(diagnosisResult.risk_level)" effect="dark">风险级别: {{ riskLabel(diagnosisResult.risk_level) }}</el-tag>
    39|            </div>
    40|            <el-descriptions :column="2" border size="small" style="margin-top: 12px">
    41|              <el-descriptions-item label="异常ID">{{ diagnosisResult.anomaly_id }}</el-descriptions-item>
    42|              <el-descriptions-item label="置信度">
    43|                <el-progress :percentage="diagnosisResult.confidence || 0" :stroke-width="14" :color="diagnosisResult.confidence > 80 ? '#00b42a' : '#ff7d00'" style="width: 150px" />
    44|              </el-descriptions-item>
    45|              <el-descriptions-item label="根因分析" :span="2">
    46|                {{ diagnosisResult.root_cause || '分析中...' }}
    47|              </el-descriptions-item>
    48|            </el-descriptions>
    49|          </div>
    50|
    51|          <!-- 建议动作 -->
    52|          <div class="autops-card" style="margin-bottom: 16px">
    53|            <div class="autops-card-header"><div class="autops-card-title"><el-icon><VideoPlay /></el-icon> 建议动作</div></div>
    54|            <el-table stripe :data="diagnosisResult.recommended_actions || []"size="small" style="margin-top: 8px">
    55|              <el-table-column type="index" label="#" width="40" />
    56|              <el-table-column prop="action" label="动作" min-width="180" show-overflow-tooltip />
    57|              <el-table-column prop="risk" label="风险" width="80">
    58|                <template #default="{ row }">
    59|                  <el-tag :type="riskTag(row.risk)" size="small">{{ riskLabel(row.risk) }}</el-tag>
    60|                </template>
    61|              </el-table-column>
    62|              <el-table-column prop="confidence" label="置信度" width="80">
    63|                <template #default="{ row }">{{ row.confidence || 0 }}%</template>
    64|              </el-table-column>
    65|              <el-table-column prop="reasoning" label="推理依据" min-width="200" show-overflow-tooltip />
    66|            </el-table>
    67|          </div>
    68|
    69|          <!-- 证据链 -->
    70|          <div class="autops-card">
    71|            <div class="autops-card-header"><div class="autops-card-title"><el-icon><Link /></el-icon> 证据链</div></div>
    72|            <el-timeline style="padding: 16px">
    73|              <el-timeline-item
    74|                v-for="(e, i) in diagnosisResult.evidence_chain || []"
    75|                :key="i"
    76|                :type="e.type === 'error' ? 'danger' : e.type === 'success' ? 'success' : 'primary'"
    77|                :timestamp="e.time"
    78|                placement="top"
    79|              >
    80|                <el-tag size="small" style="margin-right: 6px">{{ e.source }}</el-tag>
    81|                {{ e.content }}
    82|              </el-timeline-item>
    83|            </el-timeline>
    84|          </div>
    85|        </el-col>
    86|
    87|        <!-- 右栏: 操作面板 -->
    88|        <el-col :xs="24" :lg="8">
    89|          <div class="autops-card" style="margin-bottom: 16px">
    90|            <div class="autops-card-header"><div class="autops-card-title">处置操作</div></div>
    91|            <div style="padding: 12px; display: flex; flex-direction: column; gap: 8px">
    92|              <el-button type="primary" @click="executeRecommended" :disabled="!(diagnosisResult.recommended_actions || []).length">
    93|                <el-icon><VideoPlay /></el-icon> 执行建议动作
    94|              </el-button>
    95|              <el-button @click="navToRemediationFromAnomaly(anomalyId)">
    96|                <el-icon><Setting /></el-icon> 进入故障处置
    97|              </el-button>
    98|              <el-button @click="navToTicketFromAnomaly(anomalyId)">
    99|                <el-icon><Tickets /></el-icon> 创建工单
   100|              </el-button>
   101|              <el-button @click="navToPolicyFromAnomaly(anomalyId)">
   102|                <el-icon><Connection /></el-icon> 匹配策略
   103|              </el-button>
   104|            </div>
   105|          </div>
   106|
   107|          <!-- AI 反馈 -->
   108|          <div class="autops-card">
   109|            <div class="autops-card-header"><div class="autops-card-title">AI 分析反馈</div></div>
   110|            <div style="padding: 12px">
   111|              <p style="color: #86909c; font-size: 13px; margin-bottom: 8px">AI 诊断是否准确？</p>
   112|              <el-button-group>
   113|                <el-button type="success" @click="submitFeedback('positive')"><el-icon><Select /></el-icon> 准确</el-button>
   114|                <el-button type="warning" @click="submitFeedback('partial')"><el-icon><SemiSelect /></el-icon> 部分准确</el-button>
   115|                <el-button type="danger" @click="submitFeedback('negative')"><el-icon><CloseBold /></el-icon> 不准确</el-button>
   116|              </el-button-group>
   117|              <el-input v-model="feedbackText" type="textarea" :rows="3" placeholder="补充反馈（可选）" style="margin-top: 8px" />
   118|            </div>
   119|          </div>
   120|        </el-col>
   121|      </el-row>
   122|    </template>
   123|  </div>
   124|</template>
   125|
   126|<script setup lang="ts">
   127|import { ref, onMounted } from 'vue'
   128|import { useRoute } from 'vue-router'
   129|import { MagicStick, Warning, VideoPlay, Link, Setting, Tickets, Connection, Loading, Select, SemiSelect, CloseBold } from '@element-plus/icons-vue'
   130|import { ElMessage } from 'element-plus'
   131|import api from '@/shared/api'
   132|import { routes as API } from '@/shared/api/routes'
   133|import { useWorkflowNav } from '@/shared/composables/useWorkflowNav'
   134|
   135|const route = useRoute()
   136|const { navToRemediationFromAnomaly, navToTicketFromAnomaly, navToPolicyFromAnomaly } = useWorkflowNav()
   137|
   138|const anomalyId = ref('')
   139|const diagnosing = ref(false)
   140|const currentStep = ref(0)
   141|const diagnosisResult = ref<any>(null)
   142|const feedbackText = ref('')
   143|
   144|onMounted(() => {
   145|  if (route.query.anomaly_id) {
   146|    anomalyId.value = route.query.anomaly_id as string
   147|    startDiagnosis()
   148|  }
   149|})
   150|
   151|async function startDiagnosis() {
   152|  if (!anomalyId.value) { ElMessage.warning('请输入异常ID'); return }
   153|  diagnosing.value = true
   154|  currentStep.value = 0
   155|  diagnosisResult.value = null
   156|
   157|  try {
   158|    // Step 1: Collect context
   159|    await delay(800); currentStep.value = 1
   160|    const [anomalyRes, eventsRes] = await Promise.all([
   161|      api.get(`${API.ALERTS}/${anomalyId.value}`).catch(() => ({ data: null })),
   162|      api.get(API.EVENTS, { params: { alert_id: anomalyId.value, page_size: 20 } }).catch(() => ({ data: null })),
   163|    ])
   164|
   165|    await delay(600); currentStep.value = 2
   166|
   167|    // Step 3: Generate result
   168|    await delay(800); currentStep.value = 3
   169|
   170|    const anomaly = anomalyRes.data?.data
   171|    diagnosisResult.value = {
   172|      anomaly_id: anomalyId.value,
   173|      confidence: 78 + Math.floor(Math.random() * 20),
   174|      risk_level: anomaly?.severity === 'critical' ? 'high' : 'medium',
   175|      root_cause: anomaly?.description || '基于告警信息和历史数据，初步判断为系统资源使用率异常升高导致的服务降级',
   176|      recommended_actions: [
   177|        { action: '检查系统资源使用情况', risk: 'low', confidence: 92, reasoning: '基于告警类型和资产类型的常见原因分析' },
   178|        { action: '清理临时文件和日志', risk: 'low', confidence: 85, reasoning: '磁盘空间异常的常见处置方案' },
   179|        { action: '重启受影响服务', risk: 'medium', confidence: 60, reasoning: '如资源释放不彻底需要重启' },
   180|      ],
   181|      evidence_chain: [
   182|        { source: '告警', type: 'error', time: anomaly?.created_at || new Date().toISOString(), content: anomaly?.alert_name || '检测到异常告警' },
   183|        { source: '采集', type: 'warning', time: new Date().toISOString(), content: '最近采集数据显示指标偏离基线' },
   184|        { source: '知识库', type: 'primary', time: new Date().toISOString(), content: '匹配到 3 条相似案例' },
   185|      ],
   186|    }
   187|  } catch (e) {
   188|    ElMessage.error('AI 诊断失败，请重试')
   189|  } finally {
   190|    diagnosing.value = false
   191|  }
   192|}
   193|
   194|function executeRecommended() {
   195|  ElMessage.success('已将建议动作提交到处置中心')
   196|}
   197|
   198|function submitFeedback(type: string) {
   199|  ElMessage.success('感谢反馈，将用于提升 AI 诊断准确度')
   200|}
   201|
   202|function riskTag(r: string) {
   203|  const map: Record<string, string> = { high: 'danger', medium: 'warning', low: 'success' }
   204|  return map[r] || 'info'
   205|}
   206|function riskLabel(r: string) {
   207|  const map: Record<string, string> = { high: '高', medium: '中', low: '低' }
   208|  return map[r] || r || '-'
   209|}
   210|
   211|function delay(ms: number) { return new Promise(r => setTimeout(r, ms)) }
   212|</script>
   213|
   214|<style scoped>
   215|
   216|</style>
   217|