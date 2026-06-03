     1|<template>
     2|  <div class="page-container">
     3|    <div class="autops-page-header">
     4|      <div>
     5|        <div class="autops-page-title">策略模拟</div>
     6|        <div class="autops-page-desc">在沙箱中验证策略匹配结果</div>
     7|      </div>
     8|    </div>
     9|
    10|    <!-- 顶部导航 -->
    11|    <div class="autops-toolbar">
    12|      <el-button @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回策略列表</el-button>
    13|      <div style="flex:1" />
    14|      <el-tag v-if="policyDetail" :type="riskTagType(policyDetail.risk_level)" size="large">
    15|        风险: {{ policyDetail.risk_level || 'low' }}
    16|      </el-tag>
    17|    </div>
    18|
    19|    <!-- 策略概要卡片 -->
    20|    <div class="autops-card summary-card" v-if="policyDetail">
    21|      <div class="summary-grid">
    22|        <div class="summary-item">
    23|          <div class="summary-label">策略名称</div>
    24|          <div class="summary-value">{{ policyDetail.name }}</div>
    25|        </div>
    26|        <div class="summary-item">
    27|          <div class="summary-label">触发源</div>
    28|          <div class="summary-value"><el-tag size="small">{{ triggerLabel(policyDetail.trigger_source) }}</el-tag></div>
    29|        </div>
    30|        <div class="summary-item">
    31|          <div class="summary-label">状态</div>
    32|          <div class="summary-value"><el-tag :type="policyDetail.status==='active'?'success':'info'" size="small">{{ statusLabel(policyDetail.status) }}</el-tag></div>
    33|        </div>
    34|        <div class="summary-item">
    35|          <div class="summary-label">条件数</div>
    36|          <div class="summary-value">{{ policyDetail.conditions?.length || 0 }}</div>
    37|        </div>
    38|        <div class="summary-item">
    39|          <div class="summary-label">动作数</div>
    40|          <div class="summary-value">{{ policyDetail.actions?.length || 0 }}</div>
    41|        </div>
    42|        <div class="summary-item">
    43|          <div class="summary-label">需审批</div>
    44|          <div class="summary-value">{{ policyDetail.requires_approval ? '是' : '否' }}</div>
    45|        </div>
    46|      </div>
    47|    </div>
    48|
    49|    <el-row :gutter="16" style="margin-top:16px">
    50|      <!-- 左侧：模拟参数 -->
    51|      <el-col :span="10">
    52|        <div class="autops-card">
    53|          <span style="font-weight:bold">模拟参数</span>
    54|          <el-form :model="simParams" label-width="90px">
    55|            <!-- 资产选择器 -->
    56|            <el-form-item label="目标资产" required>
    57|              <el-select v-model="simParams.asset_id" filterable remote reserve-keyword
    58|                placeholder="搜索资产名称/IP"
    59|                :remote-method="searchAssets"
    60|                :loading="assetSearching"
    61|                style="width:100%"
    62|                value-key="id"
    63|                @change="onAssetSelect">
    64|                <el-option v-for="a in assetOptions" :key="a.id" :label="`${a.name} (${a.ip || a.id})`" :value="a.id">
    65|                  <div style="display:flex;justify-content:space-between;align-items:center">
    66|                    <span>{{ a.name }}</span>
    67|                    <el-tag size="small" type="info">{{ a.asset_type || a.type }}</el-tag>
    68|                  </div>
    69|                </el-option>
    70|              </el-select>
    71|            </el-form-item>
    72|
    73|            <!-- 已选资产信息 -->
    74|            <div v-if="selectedAsset" class="asset-info-box">
    75|              <el-descriptions :column="2" size="small" border>
    76|                <el-descriptions-item label="名称">{{ selectedAsset.name }}</el-descriptions-item>
    77|                <el-descriptions-item label="IP">{{ selectedAsset.ip || '-' }}</el-descriptions-item>
    78|                <el-descriptions-item label="类型">{{ selectedAsset.asset_type || selectedAsset.type }}</el-descriptions-item>
    79|                <el-descriptions-item label="状态">
    80|                  <el-tag :type="selectedAsset.health_status==='healthy'?'success':selectedAsset.health_status==='warning'?'warning':'danger'" size="small">
    81|                    {{ selectedAsset.health_status || '未知' }}
    82|                  </el-tag>
    83|                </el-descriptions-item>
    84|              </el-descriptions>
    85|            </div>
    86|
    87|            <el-form-item label="告警类型">
    88|              <el-select v-model="simParams.alert_type" placeholder="选择告警类型" clearable style="width:100%">
    89|                <el-option label="CPU过高" value="cpu_high" />
    90|                <el-option label="内存过高" value="memory_high" />
    91|                <el-option label="磁盘空间不足" value="disk_full" />
    92|                <el-option label="服务不可达" value="service_down" />
    93|                <el-option label="端口异常" value="port_error" />
    94|                <el-option label="证书过期" value="cert_expiring" />
    95|                <el-option label="连接数过高" value="conn_high" />
    96|                <el-option label="响应超时" value="response_timeout" />
    97|                <el-option label="自定义" value="custom" />
    98|              </el-select>
    99|            </el-form-item>
   100|
   101|            <el-form-item label="严重等级">
   102|              <el-radio-group v-model="simParams.severity">
   103|                <el-radio-button value="">自动</el-radio-button>
   104|                <el-radio-button value="low">低</el-radio-button>
   105|                <el-radio-button value="medium">中</el-radio-button>
   106|                <el-radio-button value="high">高</el-radio-button>
   107|                <el-radio-button value="critical">严重</el-radio-button>
   108|              </el-radio-group>
   109|            </el-form-item>
   110|
   111|            <!-- 模拟指标值 -->
   112|            <el-divider content-position="left">模拟指标</el-divider>
   113|            <div class="metric-inputs">
   114|              <div v-for="(m, idx) in simMetrics" :key="idx" class="metric-row">
   115|                <el-select v-model="m.key" placeholder="指标" style="width:140px" size="small">
   116|                  <el-option label="CPU使用率" value="cpu_usage" />
   117|                  <el-option label="内存使用率" value="memory_usage" />
   118|                  <el-option label="磁盘使用率" value="disk_usage" />
   119|                  <el-option label="响应时间" value="response_time" />
   120|                  <el-option label="连接数" value="connection_count" />
   121|                  <el-option label="状态码" value="status_code" />
   122|                </el-select>
   123|                <el-input-number v-model="m.value" :min="0" :max="10000" placeholder="值" style="width:130px" size="small" />
   124|                <el-input v-model="m.unit" placeholder="单位" style="width:70px" size="small" />
   125|                <el-button size="small" type="danger" @click="simMetrics.splice(idx,1)"><el-icon><Delete /></el-icon></el-button>
   126|              </div>
   127|              <el-button size="small" @click="simMetrics.push({key:'',value:0,unit:'%'})">+ 添加指标</el-button>
   128|            </div>
   129|
   130|            <el-form-item label="扩展参数" style="margin-top:12px">
   131|              <el-input v-model="simParams.extra_json" type="textarea" :rows="3"
   132|                placeholder="可选 JSON，如 {&quot;duration&quot;: &quot;5m&quot;}"
   133|                style="font-family:monospace" />
   134|            </el-form-item>
   135|
   136|            <el-form-item>
   137|              <el-button type="primary" @click="runSimulate" :loading="simulating" size="large">
   138|                <el-icon><VideoPlay /></el-icon> 执行模拟
   139|              </el-button>
   140|              <el-button @click="resetParams">重置参数</el-button>
   141|            </el-form-item>
   142|          </el-form>
   143|        </div>
   144|      </el-col>
   145|
   146|      <!-- 右侧：模拟结果 -->
   147|      <el-col :span="14">
   148|        <!-- 等待模拟 -->
   149|        <div class="autops-card result-placeholder" v-if="!simulateResult && !simulating">
   150|          <el-empty description="配置模拟参数后点击「执行模拟」查看结果" :image-size="100">
   151|            <template #image>
   152|              <el-icon :size="80" color="#c9cdd4"><VideoPlay /></el-icon>
   153|            </template>
   154|          </el-empty>
   155|        </div>
   156|
   157|        <!-- 模拟中 -->
   158|        <div class="autops-card result-placeholder" v-if="simulating">
   159|          <div class="simulating-box">
   160|            <el-icon :size="48" class="rotating"><Loading /></el-icon>
   161|            <p style="margin-top:16px;font-size:16px">正在模拟策略执行...</p>
   162|            <p style="color:#86909c">分析条件匹配、计算影响范围、生成执行计划</p>
   163|          </div>
   164|        </div>
   165|
   166|        <!-- 模拟结果 -->
   167|        <template v-if="simulateResult && !simulating">
   168|          <!-- 匹配结果总览 -->
   169|          <div class="autops-card result-card" :class="simulateResult.matched ? 'matched' : 'unmatched'">
   170|            <div class="result-header">
   171|              <el-icon :size="32" :color="simulateResult.matched ? '#00b42a' : '#86909c'">
   172|                <component :is="simulateResult.matched ? 'SuccessFilled' : 'CircleCloseFilled'" />
   173|              </el-icon>
   174|              <div>
   175|                <h2 style="margin:0">{{ simulateResult.matched ? '策略命中' : '策略未命中' }}</h2>
   176|                <p style="margin:4px 0 0;color:#86909c">{{ simulateResult.matched ? '模拟条件满足策略触发条件' : '当前条件不满足任何触发条件' }}</p>
   177|              </div>
   178|            </div>
   179|            <el-row :gutter="12" style="margin-top:16px">
   180|              <el-col :span="8">
   181|                <div class="mini-stat">
   182|                  <div class="mini-value">{{ simulateResult.risk_level || policyDetail?.risk_level || '-' }}</div>
   183|                  <div class="mini-label">风险等级</div>
   184|                </div>
   185|              </el-col>
   186|              <el-col :span="8">
   187|                <div class="mini-stat">
   188|                  <div class="mini-value">{{ simulateResult.actions?.length || 0 }}</div>
   189|                  <div class="mini-label">预期动作</div>
   190|                </div>
   191|              </el-col>
   192|              <el-col :span="8">
   193|                <div class="mini-stat">
   194|                  <div class="mini-value">{{ simulateResult.requires_approval ? '需要' : '不需要' }}</div>
   195|                  <div class="mini-label">审批</div>
   196|                </div>
   197|              </el-col>
   198|            </el-row>
   199|          </div>
   200|
   201|          <!-- 条件匹配详情 -->
   202|          <div class="autops-card" v-if="simulateResult.condition_details?.length" style="margin-top:16px">
   203|            <span style="font-weight:bold">条件匹配详情</span>
   204|            <el-table stripe :data="simulateResult.condition_details">
   205|              <el-table-column prop="field" label="条件字段" min-width="140">
   206|                <template #default="{ row }">
   207|                  <el-tag size="small">{{ row.field || row.metric }}</el-tag>
   208|                </template>
   209|              </el-table-column>
   210|              <el-table-column label="运算符" width="80" align="center">
   211|                <template #default="{ row }">
   212|                  <span style="font-weight:bold;color:#165dff">{{ row.operator }}</span>
   213|                </template>
   214|              </el-table-column>
   215|              <el-table-column label="阈值" width="100" align="center">
   216|                <template #default="{ row }">
   217|                  <el-tag type="warning" size="small">{{ row.threshold }}{{ row.unit || '' }}</el-tag>
   218|                </template>
   219|              </el-table-column>
   220|              <el-table-column label="实际值" width="100" align="center">
   221|                <template #default="{ row }">
   222|                  <el-tag :type="row.matched ? 'success' : 'danger'" size="small">{{ row.actual }}{{ row.unit || '' }}</el-tag>
   223|                </template>
   224|              </el-table-column>
   225|              <el-table-column label="匹配" width="80" align="center">
   226|                <template #default="{ row }">
   227|                  <el-icon :size="18" :color="row.matched ? '#00b42a' : '#f53f3f'">
   228|                    <component :is="row.matched ? 'SuccessFilled' : 'CircleCloseFilled'" />
   229|                  </el-icon>
   230|                </template>
   231|              </el-table-column>
   232|              <el-table-column prop="explanation" label="说明" min-width="160" show-overflow-tooltip />
   233|            </el-table>
   234|            <div v-if="simulateResult.condition_logic" style="margin-top:8px;color:#86909c;font-size:13px">
   235|              条件逻辑: <strong>{{ simulateResult.condition_logic }}</strong>
   236|              ({{ simulateResult.matched_count || 0 }}/{{ simulateResult.total_conditions || simulateResult.condition_details.length }} 条件满足)
   237|            </div>
   238|          </div>
   239|
   240|          <!-- 命中解释 -->
   241|          <div class="autops-card" v-if="simulateResult.explanation" style="margin-top:16px">
   242|            <span style="font-weight:bold">命中解释</span>
   243|            <div class="explanation-box">
   244|              <el-alert :title="simulateResult.explanation" :type="simulateResult.matched ? 'success' : 'info'" show-icon :closable="false" />
   245|              <div v-if="simulateResult.hit_reasons?.length" style="margin-top:12px">
   246|                <h4>命中原因：</h4>
   247|                <ul class="reason-list">
   248|                  <li v-for="(r, i) in simulateResult.hit_reasons" :key="i">
   249|                    <el-tag :type="r.type === 'match' ? 'success' : r.type === 'scope' ? 'primary' : 'info'" size="small">{{ r.label }}</el-tag>
   250|                    {{ r.description }}
   251|                  </li>
   252|                </ul>
   253|              </div>
   254|            </div>
   255|          </div>
   256|
   257|          <!-- 执行动作预览 -->
   258|          <div class="autops-card" v-if="simulateResult.actions?.length" style="margin-top:16px">
   259|            <span style="font-weight:bold">预期执行动作链</span>
   260|            <el-timeline>
   261|              <el-timeline-item v-for="(act, idx) in simulateResult.actions" :key="idx"
   262|                :type="getActionColor(act.type)" :hollow="false" size="large"
   263|                :timestamp="`步骤 ${idx+1}`">
   264|                <div class="action-preview-card">
   265|                  <div class="action-preview-header">
   266|                    <el-tag :type="getActionColor(act.type)">{{ actionTypeLabel(act.type) }}</el-tag>
   267|                    <span style="font-weight:bold;margin-left:8px">{{ act.target || act.name || '-' }}</span>
   268|                  </div>
   269|                  <div v-if="act.params" class="action-params">
   270|                    <code>{{ typeof act.params === 'object' ? JSON.stringify(act.params, null, 2) : act.params }}</code>
   271|                  </div>
   272|                  <div v-if="act.description" style="color:#86909c;font-size:13px;margin-top:4px">{{ act.description }}</div>
   273|                  <div class="action-meta">
   274|                    <span v-if="act.timeout"><el-icon><Timer /></el-icon> 超时 {{ act.timeout }}s</span>
   275|                    <span v-if="act.on_failure"><el-icon><Warning /></el-icon> 失败 {{ act.on_failure }}</span>
   276|                  </div>
   277|                </div>
   278|              </el-timeline-item>
   279|            </el-timeline>
   280|
   281|            <!-- 执行顺序流程图 -->
   282|            <el-divider content-position="left">执行流程预览</el-divider>
   283|            <div class="flow-chain">
   284|              <div v-for="(act, idx) in simulateResult.actions" :key="idx" class="flow-step">
   285|                <div class="flow-step-box" :style="{borderColor: getActionColor(act.type) === 'danger' ? '#f53f3f' : getActionColor(act.type) === 'warning' ? '#ff7d00' : '#165dff'}">
   286|                  <div class="flow-step-num">{{ idx + 1 }}</div>
   287|                  <div class="flow-step-name">{{ actionTypeLabel(act.type) }}</div>
   288|                  <div class="flow-step-target">{{ act.target || '-' }}</div>
   289|                </div>
   290|                <div v-if="idx < simulateResult.actions.length - 1" class="flow-connector">
   291|                  <div class="flow-line"></div>
   292|                  <div class="flow-arrow-down">▼</div>
   293|                </div>
   294|              </div>
   295|            </div>
   296|          </div>
   297|
   298|          <!-- 影响分析 -->
   299|          <div class="autops-card" v-if="simulateResult.impact" style="margin-top:16px">
   300|            <span style="font-weight:bold">影响分析</span>
   301|            <el-descriptions :column="2" border>
   302|              <el-descriptions-item label="影响资产数">{{ simulateResult.impact.affected_assets || 1 }}</el-descriptions-item>
   303|              <el-descriptions-item label="预估影响时间">{{ simulateResult.impact.estimated_duration || '未知' }}</el-descriptions-item>
   304|              <el-descriptions-item label="影响等级">
   305|                <el-tag :type="riskTagType(simulateResult.impact.impact_level || 'low')" size="small">
   306|                  {{ simulateResult.impact.impact_level || 'low' }}
   307|                </el-tag>
   308|              </el-descriptions-item>
   309|              <el-descriptions-item label="可回滚">{{ simulateResult.impact.rollbackable ? '是' : '否' }}</el-descriptions-item>
   310|              <el-descriptions-item label="说明" :span="2">{{ simulateResult.impact.description || '-' }}</el-descriptions-item>
   311|            </el-descriptions>
   312|          </div>
   313|        </template>
   314|      </el-col>
   315|    </el-row>
   316|  </div>
   317|</template>
   318|
   319|<script setup lang="ts">
   320|import { ref, reactive, onMounted } from 'vue'
   321|import { useRoute } from 'vue-router'
   322|import { ElMessage } from 'element-plus'
   323|import {
   324|  ArrowLeft, VideoPlay, Delete, Loading, SuccessFilled,
   325|  CircleCloseFilled, Timer, Warning
   326|} from '@element-plus/icons-vue'
   327|import api from '@/shared/api/client'
   328|import { API } from '@/shared/api/routes'
   329|
   330|const route = useRoute()
   331|const policyId = route.params.id as string
   332|
   333|const policyDetail = ref<any>(null)
   334|const simulating = ref(false)
   335|const simulateResult = ref<any>(null)
   336|const assetSearching = ref(false)
   337|const assetOptions = ref<any[]>([])
   338|const selectedAsset = ref<any>(null)
   339|
   340|const simParams = reactive({
   341|  asset_id: '',
   342|  alert_type: '',
   343|  severity: '',
   344|  extra_json: '',
   345|})
   346|
   347|const simMetrics = reactive<{ key: string; value: number; unit: string }[]>([
   348|  { key: 'cpu_usage', value: 95, unit: '%' },
   349|])
   350|
   351|function riskTagType(level: string) {
   352|  const map: Record<string, string> = { low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }
   353|  return map[level] || 'info'
   354|}
   355|
   356|function triggerLabel(s: string) {
   357|  return ({ event: '事件', alert: '告警', state_change: '状态变更', manual: '手动', schedule: '定时' })[s] || s
   358|}
   359|
   360|function statusLabel(s: string) {
   361|  return ({ draft: '草稿', active: '已激活', deprecated: '已废弃' })[s] || s
   362|}
   363|
   364|function actionTypeLabel(t: string) {
   365|  return ({ script: '执行脚本', playbook: '执行Playbook', notification: '发送通知', ticket: '创建工单', suppress: '抑制告警' })[t] || t
   366|}
   367|
   368|function getActionColor(t: string) {
   369|  return ({ script: 'warning', playbook: 'danger', notification: 'primary', ticket: 'success', suppress: 'info' })[t] || 'primary'
   370|}
   371|
   372|async function loadPolicy() {
   373|  try {
   374|    const { data } = await api.get(API.POLICY_DETAIL(policyId))
   375|    if (data.code === 0) policyDetail.value = data.data
   376|  } catch {}
   377|}
   378|
   379|async function searchAssets(query: string) {
   380|  if (!query) return
   381|  assetSearching.value = true
   382|  try {
   383|    const res = await api.get(API.ASSETS, { params: { keyword: query, page_size: 20 } })
   384|    if (res.data?.code === 0) {
   385|      assetOptions.value = res.data.data?.items || res.data.data || []
   386|    }
   387|  } catch {}
   388|  finally { assetSearching.value = false }
   389|}
   390|
   391|function onAssetSelect(id: string) {
   392|  selectedAsset.value = assetOptions.value.find(a => a.id === id) || null
   393|}
   394|
   395|function resetParams() {
   396|  simParams.asset_id = ''
   397|  simParams.alert_type = ''
   398|  simParams.severity = ''
   399|  simParams.extra_json = ''
   400|  simMetrics.splice(0, simMetrics.length, { key: 'cpu_usage', value: 95, unit: '%' })
   401|  selectedAsset.value = null
   402|  simulateResult.value = null
   403|}
   404|
   405|async function runSimulate() {
   406|  if (!simParams.asset_id) return ElMessage.warning('请选择目标资产')
   407|
   408|  const payload: any = { asset_id: simParams.asset_id }
   409|  if (simParams.alert_type) payload.alert_type = simParams.alert_type
   410|  if (simParams.severity) payload.severity = simParams.severity
   411|
   412|  const metricsObj: Record<string, any> = {}
   413|  for (const m of simMetrics) {
   414|    if (m.key) metricsObj[m.key] = m.value
   415|  }
   416|  if (Object.keys(metricsObj).length) payload.metrics = metricsObj
   417|
   418|  if (simParams.extra_json.trim()) {
   419|    try { payload.extra = JSON.parse(simParams.extra_json) }
   420|    catch { return ElMessage.error('扩展参数 JSON 格式错误') }
   421|  }
   422|
   423|  simulating.value = true
   424|  simulateResult.value = null
   425|  try {
   426|    const { data } = await api.post(API.POLICY_SIMULATE(policyId), payload)
   427|    if (data.code === 0) {
   428|      simulateResult.value = data.data
   429|      ElMessage.success('模拟完成')
   430|    } else {
   431|      ElMessage.error(data.message || '模拟失败')
   432|    }
   433|  } catch (e: any) {
   434|    ElMessage.error('模拟请求失败: ' + (e.message || e))
   435|  } finally {
   436|    simulating.value = false
   437|  }
   438|}
   439|
   440|onMounted(() => { loadPolicy() })
   441|</script>
   442|
   443|<style scoped>
   444|
   445|.toolbar { margin-bottom: 16px; display: flex; gap: 8px; align-items: center; }
   446|.summary-card { margin-bottom: 16px; }
   447|.summary-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 16px; text-align: center; }
   448|.summary-item { padding: 8px 0; }
   449|.summary-label { font-size: 12px; color: #86909c; margin-bottom: 4px; }
   450|.summary-value { font-size: 15px; font-weight: 600; }
   451|
   452|.asset-info-box { margin: -8px 0 12px 89px; padding: 10px; background: #f7f8fa; border-radius: 6px; border: 1px solid #e5e6eb; }
   453|.metric-inputs { background: #f7f8fa; padding: 10px; border-radius: 4px; }
   454|.metric-row { display: flex; gap: 6px; align-items: center; margin-bottom: 6px; }
   455|
   456|.result-placeholder { min-height: 400px; display: flex; align-items: center; justify-content: center; }
   457|.simulating-box { text-align: center; padding: 60px 0; }
   458|.rotating { animation: rotate 1.5s linear infinite; }
   459|@keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
   460|
   461|.result-card { border-radius: 8px; transition: all 0.3s; }
   462|.result-card.matched { border-left: 4px solid #00b42a; }
   463|.result-card.unmatched { border-left: 4px solid #86909c; }
   464|.result-header { display: flex; gap: 16px; align-items: center; }
   465|.mini-stat { text-align: center; padding: 8px; background: #f7f8fa; border-radius: 6px; }
   466|.mini-value { font-size: 16px; font-weight: bold; color: #1d2129; }
   467|.mini-label { font-size: 12px; color: #86909c; margin-top: 2px; }
   468|
   469|.explanation-box { padding: 4px; }
   470|.reason-list { list-style: none; padding: 0; }
   471|.reason-list li { padding: 6px 0; border-bottom: 1px solid #f0f0f0; display: flex; align-items: center; gap: 8px; }
   472|
   473|.action-preview-card { background: #fafbfc; padding: 10px; border-radius: 6px; border: 1px solid #e5e6eb; }
   474|.action-preview-header { display: flex; align-items: center; }
   475|.action-params { margin-top: 6px; background: #f5f5f5; padding: 6px 8px; border-radius: 4px; }
   476|.action-params code { font-size: 12px; color: #4e5969; white-space: pre-wrap; }
   477|.action-meta { margin-top: 6px; display: flex; gap: 12px; color: #86909c; font-size: 12px; }
   478|.action-meta span { display: flex; align-items: center; gap: 4px; }
   479|
   480|.flow-chain { display: flex; flex-direction: column; align-items: center; gap: 0; padding: 16px; }
   481|.flow-step { display: flex; flex-direction: column; align-items: center; }
   482|.flow-step-box { border: 2px solid #165dff; border-radius: 8px; padding: 12px 20px; text-align: center; min-width: 180px; background: #fff; }
   483|.flow-step-num { font-size: 18px; font-weight: bold; color: #165dff; }
   484|.flow-step-name { font-size: 13px; font-weight: 600; margin-top: 2px; }
   485|.flow-step-target { font-size: 11px; color: #86909c; margin-top: 2px; }
   486|.flow-connector { display: flex; flex-direction: column; align-items: center; }
   487|.flow-line { width: 2px; height: 16px; background: #dcdfe6; }
   488|.flow-arrow-down { color: #dcdfe6; font-size: 10px; line-height: 1; }
   489|</style>
   490|