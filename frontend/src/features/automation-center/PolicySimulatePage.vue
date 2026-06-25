<template>
  <div class="autops-page-container">
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">策略模拟</div>
        <div class="autops-page-desc">在沙箱中验证策略匹配结果</div>
      </div>
    </div>

    <!-- 顶部导航 -->
    <div class="autops-toolbar">
      <el-button @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回策略列表</el-button>
      <div style="flex:1" />
      <el-tag v-if="policyDetail" :type="(riskTagType(policyDetail.risk_level)) as TagType" size="large">
        风险: {{ policyDetail.risk_level || 'low' }}
      </el-tag>
    </div>

    <!-- 策略概要卡片 -->
    <div class="autops-card summary-card" v-if="policyDetail">
      <div class="summary-grid">
        <div class="summary-item">
          <div class="summary-label">策略名称</div>
          <div class="summary-value">{{ policyDetail.name }}</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">触发源</div>
          <div class="summary-value"><el-tag size="small">{{ triggerLabel(policyDetail.trigger_source) }}</el-tag></div>
        </div>
        <div class="summary-item">
          <div class="summary-label">状态</div>
          <div class="summary-value"><el-tag :type="policyDetail.status==='active'?'success':'info'" size="small">{{ statusLabel(policyDetail.status) }}</el-tag></div>
        </div>
        <div class="summary-item">
          <div class="summary-label">条件数</div>
          <div class="summary-value">{{ policyDetail.conditions?.length || 0 }}</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">动作数</div>
          <div class="summary-value">{{ policyDetail.actions?.length || 0 }}</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">需审批</div>
          <div class="summary-value">{{ policyDetail.requires_approval ? '是' : '否' }}</div>
        </div>
      </div>
    </div>

    <el-row :gutter="16" style="margin-top:16px">
      <!-- 左侧：模拟参数 -->
      <el-col :span="10">
        <div class="autops-card">
          <span style="font-weight:bold">模拟参数</span>
          <el-form :model="simParams" label-width="90px">
            <!-- 资产选择器 -->
            <el-form-item label="目标资产" required>
              <el-select v-model="simParams.asset_id" filterable remote reserve-keyword
                placeholder="搜索资产名称/IP"
                :remote-method="searchAssets"
                :loading="assetSearching"
                style="width:100%"
                value-key="id"
                @change="onAssetSelect">
                <el-option v-for="a in assetOptions" :key="a.id" :label="a.name + ' (' + a.ip || a.id + ')'" :value="a.id">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <span>{{ a.name }}</span>
                    <el-tag size="small" type="info">{{ a.asset_type || a.type }}</el-tag>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>

            <!-- 已选资产信息 -->
            <div v-if="selectedAsset" class="asset-info-box">
              <el-descriptions :column="2" size="small" border>
                <el-descriptions-item label="名称">{{ selectedAsset.name }}</el-descriptions-item>
                <el-descriptions-item label="IP">{{ selectedAsset.ip || '-' }}</el-descriptions-item>
                <el-descriptions-item label="类型">{{ selectedAsset.asset_type || selectedAsset.type }}</el-descriptions-item>
                <el-descriptions-item label="状态">
                  <el-tag :type="selectedAsset.health_status==='healthy'?'success':selectedAsset.health_status==='warning'?'warning':'danger'" size="small">
                    {{ selectedAsset.health_status || '未知' }}
                  </el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <el-form-item label="告警类型">
              <el-select v-model="simParams.alert_type" placeholder="选择告警类型" clearable style="width:100%">
                <el-option label="CPU过高" value="cpu_high" />
                <el-option label="内存过高" value="memory_high" />
                <el-option label="磁盘空间不足" value="disk_full" />
                <el-option label="服务不可达" value="service_down" />
                <el-option label="端口异常" value="port_error" />
                <el-option label="证书过期" value="cert_expiring" />
                <el-option label="连接数过高" value="conn_high" />
                <el-option label="响应超时" value="response_timeout" />
                <el-option label="自定义" value="custom" />
              </el-select>
            </el-form-item>

            <el-form-item label="严重等级">
              <el-radio-group v-model="simParams.severity">
                <el-radio-button value="">自动</el-radio-button>
                <el-radio-button value="low">低</el-radio-button>
                <el-radio-button value="medium">中</el-radio-button>
                <el-radio-button value="high">高</el-radio-button>
                <el-radio-button value="critical">严重</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <!-- 模拟指标值 -->
            <el-divider content-position="left">模拟指标</el-divider>
            <div class="metric-inputs">
              <div v-for="(m, idx) in simMetrics" :key="idx" class="metric-row">
                <el-select v-model="m.key" placeholder="指标" style="width:140px" size="small">
                  <el-option label="CPU使用率" value="cpu_usage" />
                  <el-option label="内存使用率" value="memory_usage" />
                  <el-option label="磁盘使用率" value="disk_usage" />
                  <el-option label="响应时间" value="response_time" />
                  <el-option label="连接数" value="connection_count" />
                  <el-option label="状态码" value="status_code" />
                </el-select>
                <el-input-number v-model="m.value" :min="0" :max="10000" placeholder="值" style="width:130px" size="small" />
                <el-input v-model="m.unit" placeholder="单位" style="width:70px" size="small" />
                <el-button size="small" type="danger" @click="simMetrics.splice(idx,1)"><el-icon><Delete /></el-icon></el-button>
              </div>
              <el-button size="small" @click="simMetrics.push({key:'',value:0,unit:'%'})">+ 添加指标</el-button>
            </div>

            <el-form-item label="扩展参数" style="margin-top:12px">
              <el-input v-model="simParams.extra_json" type="textarea" :rows="3"
                placeholder="可选 JSON，如 {&quot;duration&quot;: &quot;5m&quot;}"
                style="font-family:monospace" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="runSimulate" :loading="simulating" size="large">
                <el-icon><VideoPlay /></el-icon> 执行模拟
              </el-button>
              <el-button @click="resetParams">重置参数</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>

      <!-- 右侧：模拟结果 -->
      <el-col :span="14">
        <!-- 等待模拟 -->
        <div class="autops-card result-placeholder" v-if="!simulateResult && !simulating">
          <el-empty description="配置模拟参数后点击「执行模拟」查看结果" :image-size="100">
            <template #image>
              <el-icon :size="80" color="#c9cdd4"><VideoPlay /></el-icon>
            </template>
          </el-empty>
        </div>

        <!-- 模拟中 -->
        <div class="autops-card result-placeholder" v-if="simulating">
          <div class="simulating-box">
            <el-icon :size="48" class="rotating"><Loading /></el-icon>
            <p style="margin-top:16px;font-size:16px">正在模拟策略执行...</p>
            <p style="color:#86909c">分析条件匹配、计算影响范围、生成执行计划</p>
          </div>
        </div>

        <!-- 模拟结果 -->
        <template v-if="simulateResult && !simulating">
          <!-- 匹配结果总览 -->
          <div class="autops-card result-card" :class="simulateResult.matched ? 'matched' : 'unmatched'">
            <div class="result-header">
              <el-icon :size="32" :color="simulateResult.matched ? '#00b42a' : '#86909c'">
                <component :is="simulateResult.matched ? 'SuccessFilled' : 'CircleCloseFilled'" />
              </el-icon>
              <div>
                <h2 style="margin:0">{{ simulateResult.matched ? '策略命中' : '策略未命中' }}</h2>
                <p style="margin:4px 0 0;color:#86909c">{{ simulateResult.matched ? '模拟条件满足策略触发条件' : '当前条件不满足任何触发条件' }}</p>
              </div>
            </div>
            <el-row :gutter="12" style="margin-top:16px">
              <el-col :span="8">
                <div class="mini-stat">
                  <div class="mini-value">{{ simulateResult.risk_level || policyDetail?.risk_level || '-' }}</div>
                  <div class="mini-label">风险等级</div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="mini-stat">
                  <div class="mini-value">{{ simulateResult.actions?.length || 0 }}</div>
                  <div class="mini-label">预期动作</div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="mini-stat">
                  <div class="mini-value">{{ simulateResult.requires_approval ? '需要' : '不需要' }}</div>
                  <div class="mini-label">审批</div>
                </div>
              </el-col>
            </el-row>
          </div>

          <!-- 条件匹配详情 -->
          <div class="autops-card" v-if="simulateResult.condition_details?.length" style="margin-top:16px">
            <span style="font-weight:bold">条件匹配详情</span>
            <el-table stripe :data="simulateResult.condition_details">
              <el-table-column prop="field" label="条件字段" min-width="140">
                <template #default="{ row }">
                  <el-tag size="small">{{ row.field || row.metric }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="运算符" width="80" align="center">
                <template #default="{ row }">
                  <span style="font-weight:bold;color:#165dff">{{ row.operator }}</span>
                </template>
              </el-table-column>
              <el-table-column label="阈值" width="100" align="center">
                <template #default="{ row }">
                  <el-tag type="warning" size="small">{{ row.threshold }}{{ row.unit || '' }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="实际值" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.matched ? 'success' : 'danger'" size="small">{{ row.actual }}{{ row.unit || '' }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="匹配" width="80" align="center">
                <template #default="{ row }">
                  <el-icon :size="18" :color="row.matched ? '#00b42a' : '#f53f3f'">
                    <component :is="row.matched ? 'SuccessFilled' : 'CircleCloseFilled'" />
                  </el-icon>
                </template>
              </el-table-column>
              <el-table-column prop="explanation" label="说明" min-width="160" show-overflow-tooltip />
            </el-table>
            <div v-if="simulateResult.condition_logic" style="margin-top:8px;color:#86909c;font-size:13px">
              条件逻辑: <strong>{{ simulateResult.condition_logic }}</strong>
              ({{ simulateResult.matched_count || 0 }}/{{ simulateResult.total_conditions || simulateResult.condition_details.length }} 条件满足)
            </div>
          </div>

          <!-- 命中解释 -->
          <div class="autops-card" v-if="simulateResult.explanation" style="margin-top:16px">
            <span style="font-weight:bold">命中解释</span>
            <div class="explanation-box">
              <el-alert :title="simulateResult.explanation" :type="simulateResult.matched ? 'success' : 'info'" show-icon :closable="false" />
              <div v-if="simulateResult.hit_reasons?.length" style="margin-top:12px">
                <h4>命中原因：</h4>
                <ul class="reason-list">
                  <li v-for="(r, i) in simulateResult.hit_reasons" :key="i">
                    <el-tag :type="r.type === 'match' ? 'success' : r.type === 'scope' ? 'primary' : 'info'" size="small">{{ r.label }}</el-tag>
                    {{ r.description }}
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <!-- 执行动作预览 -->
          <div class="autops-card" v-if="simulateResult.actions?.length" style="margin-top:16px">
            <span style="font-weight:bold">预期执行动作链</span>
            <el-timeline>
              <el-timeline-item v-for="(act, idx) in simulateResult.actions" :key="idx"
                :type="(getActionColor(act.type)) as TagType" :hollow="false" size="large"
                :timestamp="'步骤 ' + idx+1">
                <div class="action-preview-card">
                  <div class="action-preview-header">
                    <el-tag :type="(getActionColor(act.type)) as TagType">{{ actionTypeLabel(act.type) }}</el-tag>
                    <span style="font-weight:bold;margin-left:8px">{{ act.target || act.name || '-' }}</span>
                  </div>
                  <div v-if="act.params" class="action-params">
                    <code>{{ typeof act.params === 'object' ? JSON.stringify(act.params, null, 2) : act.params }}</code>
                  </div>
                  <div v-if="act.description" style="color:#86909c;font-size:13px;margin-top:4px">{{ act.description }}</div>
                  <div class="action-meta">
                    <span v-if="act.timeout"><el-icon><Timer /></el-icon> 超时 {{ act.timeout }}s</span>
                    <span v-if="act.on_failure"><el-icon><Warning /></el-icon> 失败 {{ act.on_failure }}</span>
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>

            <!-- 执行顺序流程图 -->
            <el-divider content-position="left">执行流程预览</el-divider>
            <div class="flow-chain">
              <div v-for="(act, idx) in simulateResult.actions" :key="idx" class="flow-step">
                <div class="flow-step-box" :style="{borderColor: getActionColor(act.type) === 'danger' ? '#f53f3f' : getActionColor(act.type) === 'warning' ? '#ff7d00' : '#165dff'}">
                  <div class="flow-step-num">{{ Number(idx) + 1 }}</div>
                  <div class="flow-step-name">{{ actionTypeLabel(act.type) }}</div>
                  <div class="flow-step-target">{{ act.target || '-' }}</div>
                </div>
                <div v-if="Number(idx) < simulateResult.actions.length - 1" class="flow-connector">
                  <div class="flow-line"></div>
                  <div class="flow-arrow-down">▼</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 影响分析 -->
          <div class="autops-card" v-if="simulateResult.impact" style="margin-top:16px">
            <span style="font-weight:bold">影响分析</span>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="影响资产数">{{ simulateResult.impact.affected_assets || 1 }}</el-descriptions-item>
              <el-descriptions-item label="预估影响时间">{{ simulateResult.impact.estimated_duration || '未知' }}</el-descriptions-item>
              <el-descriptions-item label="影响等级">
                <el-tag :type="(riskTagType(simulateResult.impact.impact_level || 'low')) as TagType" size="small">
                  {{ simulateResult.impact.impact_level || 'low' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="可回滚">{{ simulateResult.impact.rollbackable ? '是' : '否' }}</el-descriptions-item>
              <el-descriptions-item label="说明" :span="2">{{ simulateResult.impact.description || '-' }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </template>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, VideoPlay, Delete, Loading, SuccessFilled,
  CircleCloseFilled, Timer, Warning
} from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const route = useRoute()
const policyId = route.params.id as string

const policyDetail = ref<any>(null)
const simulating = ref(false)
const simulateResult = ref<any>(null)
const assetSearching = ref(false)
const assetOptions = ref<any[]>([])
const selectedAsset = ref<any>(null)

const simParams = reactive({
  asset_id: '',
  alert_type: '',
  severity: '',
  extra_json: '',
})

const simMetrics = reactive<{ key: string; value: number; unit: string }[]>([
  { key: 'cpu_usage', value: 95, unit: '%' },
])

function riskTagType(level: string): TagType {
  const map: Record<string, string> = { low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }
  return (map[level] || 'info') as TagType
}

function triggerLabel(s: string) {
  return ({ event: '事件', alert: '告警', state_change: '状态变更', manual: '手动', schedule: '定时' })[s] || s
}

function statusLabel(s: string) {
  return ({ draft: '草稿', active: '已激活', deprecated: '已废弃' })[s] || s
}

function actionTypeLabel(t: string) {
  return ({ script: '执行脚本', playbook: '执行Playbook', notification: '发送通知', ticket: '创建工单', suppress: '抑制告警' })[t] || t
}

function getActionColor(t: string): TagType {
  return (({ script: 'warning', playbook: 'danger', notification: 'primary', ticket: 'success', suppress: 'info' } as Record<string, TagType>)[t] ?? 'primary') as TagType
}

async function loadPolicy() {
  try {
    const { data } = await api.get(API.POLICY_DETAIL(policyId))
    if (data.code === 0) policyDetail.value = data.data
  } catch {}
}

async function searchAssets(query: string) {
  if (!query) return
  assetSearching.value = true
  try {
    const res = await api.get(API.ASSETS, { params: { keyword: query, page_size: 20 } })
    if (res.data?.code === 0) {
      assetOptions.value = res.data.data?.items || res.data.data || []
    }
  } catch {}
  finally { assetSearching.value = false }
}

function onAssetSelect(id: string) {
  selectedAsset.value = assetOptions.value.find(a => a.id === id) || null
}

function resetParams() {
  simParams.asset_id = ''
  simParams.alert_type = ''
  simParams.severity = ''
  simParams.extra_json = ''
  simMetrics.splice(0, simMetrics.length, { key: 'cpu_usage', value: 95, unit: '%' })
  selectedAsset.value = null
  simulateResult.value = null
}

async function runSimulate() {
  if (!simParams.asset_id) return ElMessage.warning('请选择目标资产')

  const payload: any = { asset_id: simParams.asset_id }
  if (simParams.alert_type) payload.alert_type = simParams.alert_type
  if (simParams.severity) payload.severity = simParams.severity

  const metricsObj: Record<string, any> = {}
  for (const m of simMetrics) {
    if (m.key) metricsObj[m.key] = m.value
  }
  if (Object.keys(metricsObj).length) payload.metrics = metricsObj

  if (simParams.extra_json.trim()) {
    try { payload.extra = JSON.parse(simParams.extra_json) }
    catch { return ElMessage.error('扩展参数 JSON 格式错误') }
  }

  simulating.value = true
  simulateResult.value = null
  try {
    const { data } = await api.post(API.POLICY_SIMULATE(policyId), payload)
    if (data.code === 0) {
      simulateResult.value = data.data
      ElMessage.success('模拟完成')
    } else {
      ElMessage.error(data.message || '模拟失败')
    }
  } catch (e: any) {
    ElMessage.error('模拟请求失败: ' + (e.message || e))
  } finally {
    simulating.value = false
  }
}

onMounted(() => { loadPolicy() })
</script>

<style scoped>

.toolbar { margin-bottom: var(--autops-space-lg); display: flex; gap: 8px; align-items: center; }
.summary-card { margin-bottom: var(--autops-space-lg); }
.summary-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 16px; text-align: center; }
.summary-item { padding: var(--autops-space-sm) 0; }
.summary-label { font-size: var(--autops-font-12); color: var(--autops-info); margin-bottom: 4px; }
.summary-value { font-size: 15px; font-weight: 600; }

.asset-info-box { margin: -8px 0 12px 89px; padding: 10px; background: var(--autops-bg-2); border-radius: 6px; border: 1px solid var(--autops-bg-4); }
.metric-inputs { background: var(--autops-bg-2); padding: 10px; border-radius: var(--autops-radius-sm); }
.metric-row { display: flex; gap: 6px; align-items: center; margin-bottom: 6px; }

.result-placeholder { min-height: 400px; display: flex; align-items: center; justify-content: center; }
.simulating-box { text-align: center; padding: 60px 0; }
.rotating { animation: rotate 1.5s linear infinite; }
@keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.result-card { border-radius: var(--autops-radius-md); transition: all 0.3s; }
.result-card.matched { border-left: 4px solid var(--autops-success); }
.result-card.unmatched { border-left: 4px solid var(--autops-info); }
.result-header { display: flex; gap: 16px; align-items: center; }
.mini-stat { text-align: center; padding: var(--autops-space-sm); background: var(--autops-bg-2); border-radius: 6px; }
.mini-value { font-size: var(--autops-font-16); font-weight: bold; color: var(--autops-text-1); }
.mini-label { font-size: var(--autops-font-12); color: var(--autops-info); margin-top: 2px; }

.explanation-box { padding: var(--autops-space-xs); }
.reason-list { list-style: none; padding: 0; }
.reason-list li { padding: 6px 0; border-bottom: 1px solid var(--autops-bg-3); display: flex; align-items: center; gap: 8px; }

.action-preview-card { background: var(--autops-bg-1); padding: 10px; border-radius: 6px; border: 1px solid var(--autops-bg-4); }
.action-preview-header { display: flex; align-items: center; }
.action-params { margin-top: 6px; background: var(--autops-bg-3); padding: 6px 8px; border-radius: var(--autops-radius-sm); }
.action-params code { font-size: var(--autops-font-12); color: var(--autops-text-2); white-space: pre-wrap; }
.action-meta { margin-top: 6px; display: flex; gap: 12px; color: var(--autops-info); font-size: var(--autops-font-12); }
.action-meta span { display: flex; align-items: center; gap: 4px; }

.flow-chain { display: flex; flex-direction: column; align-items: center; gap: 0; padding: var(--autops-space-lg); }
.flow-step { display: flex; flex-direction: column; align-items: center; }
.flow-step-box { border: 2px solid var(--autops-primary); border-radius: var(--autops-radius-md); padding: var(--autops-space-md) 20px; text-align: center; min-width: 180px; background: var(--autops-bg-1); }
.flow-step-num { font-size: 18px; font-weight: bold; color: var(--autops-primary); }
.flow-step-name { font-size: var(--autops-font-13); font-weight: 600; margin-top: 2px; }
.flow-step-target { font-size: 11px; color: var(--autops-info); margin-top: 2px; }
.flow-connector { display: flex; flex-direction: column; align-items: center; }
.flow-line { width: 2px; height: 16px; background: var(--autops-bg-4); }
.flow-arrow-down { color: var(--autops-bg-4); font-size: 10px; line-height: 1; }
</style>
