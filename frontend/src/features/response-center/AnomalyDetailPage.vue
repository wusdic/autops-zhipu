<template>
  <div class="p-6">
    <div class="autops-page-header">
      <div class="autops-page-title-row">
        <el-button plain @click="router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <span class="autops-page-title">异常详情</span>
      </div>
      <div class="autops-page-desc">查看异常详细信息、处置时间线和关联告警</div>
    </div>

    <div v-loading="loading" class="mt-lg">
      <el-row :gutter="16">
        <!-- 左侧：异常信息 + 时间线 + 关联告警 -->
        <el-col :span="16">
          <!-- 异常基本信息 -->
          <div class="autops-card">
            <div class="autops-card-header">
              <div class="autops-card-title">异常信息</div>
              <el-tag :type="(severityType(anomaly.severity)) as TagType" size="large">
                {{ severityLabel(anomaly.severity) }}
              </el-tag>
            </div>
            <div class="autops-card-body">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="异常标题" :span="2">
                  {{ anomaly.title }}
                </el-descriptions-item>
                <el-descriptions-item label="严重级别">
                  <el-tag :type="(severityType(anomaly.severity)) as TagType" size="small">
                    {{ severityLabel(anomaly.severity) }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="状态">
                  <el-tag :type="(statusType(anomaly.status)) as TagType" size="small">
                    {{ statusLabel(anomaly.status) }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="关联资产">
                  {{ anomaly.asset_name || anomaly.asset_id || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="发现时间">
                  {{ anomaly.discovered_at || anomaly.created_at || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="来源">
                  {{ anomaly.source || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="负责人">
                  {{ anomaly.assignee_name || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="描述" :span="2">
                  {{ anomaly.description || '-' }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>

          <!-- 处置时间线 -->
          <div class="autops-card mt-lg" >
            <div class="autops-card-header">
              <div class="autops-card-title">处置时间线</div>
            </div>
            <div class="autops-card-body">
              <el-timeline v-if="timeline.length">
                <el-timeline-item
                  v-for="(item, idx) in timeline"
                  :key="idx"
                  :timestamp="item.time"
                  :type="(timelineType(item.type)) as TagType"
                  placement="top"
                >
                  <div style="font-weight: 500">{{ item.action }}</div>
                  <div class="text-tertiary">{{ item.detail || '' }}</div>
                </el-timeline-item>
              </el-timeline>
              <el-empty v-else description="暂无处置记录" :image-size="60" />
            </div>
          </div>

          <!-- 关联告警 -->
          <div class="autops-card mt-lg" >
            <div class="autops-card-header">
              <div class="autops-card-title">关联告警</div>
            </div>
            <div class="autops-card-body p-0">
              <el-table stripe
 :data="relatedAlerts"size="small"
 v-loading="alertsLoading"
 empty-text="暂无关联告警"
 >
                <el-table-column prop="title" label="告警标题" min-width="200" show-overflow-tooltip />
                <el-table-column prop="severity" label="级别" width="80">
                  <template #default="{ row }">
                    <el-tag :type="(severityType(row.severity)) as TagType" size="small">
                      {{ severityLabel(row.severity) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="asset_name" label="资产" width="140" show-overflow-tooltip />
                <el-table-column prop="status" label="状态" width="90">
                  <template #default="{ row }">
                    <el-tag :type="(alertStatusType(row.status)) as TagType" size="small">
                      {{ alertStatusLabel(row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="时间" width="160">
                  <template #default="{ row }">
                    <span class="text-tertiary">{{ row.created_at }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="100" fixed="right">
                  <template #default="{ row }">
                    <el-button plain type="primary" size="small" @click="router.push('/response/alerts/' + row.id)">
                      查看
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </el-col>

        <!-- 右侧：操作面板 -->
        <el-col :span="8">
          <div class="autops-card">
            <div class="autops-card-header">
              <div class="autops-card-title">操作</div>
            </div>
            <div class="autops-card-body" style="display: flex; flex-direction: column; gap: 10px">
              <el-button
                type="primary"
                :disabled="anomaly.status !== 'open'"
                :loading="actionLoading === 'ack'"
                @click="handleAcknowledge"
              >
                确认异常
              </el-button>
              <el-button
                :disabled="!['open', 'acknowledged'].includes(anomaly.status)"
                :loading="actionLoading === 'assign'"
                @click="showAssignDialog = true"
              >
                分配处理人
              </el-button>
              <el-button
                type="warning"
                :disabled="!['open', 'acknowledged', 'assigned'].includes(anomaly.status)"
                :loading="actionLoading === 'escalate'"
                @click="handleEscalate"
              >
                升级处理
              </el-button>
              <el-button
                :disabled="!['acknowledged', 'assigned'].includes(anomaly.status)"
                :loading="actionLoading === 'ticket'"
                @click="handleConvertTicket"
              >
                转工单
              </el-button>
              <el-button
                type="danger"
                :disabled="anomaly.status === 'closed'"
                :loading="actionLoading === 'close'"
                @click="handleClose"
              >
                关闭异常
              </el-button>
            </div>
          </div>

          <!-- 快速信息 -->
          <div class="autops-card mt-lg" >
            <div class="autops-card-header">
              <div class="autops-card-title">快速信息</div>
            </div>
            <div class="autops-card-body">
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="异常ID">{{ anomalyId }}</el-descriptions-item>
                <el-descriptions-item label="创建时间">{{ anomaly.created_at || '-' }}</el-descriptions-item>
                <el-descriptions-item label="更新时间">{{ anomaly.updated_at || '-' }}</el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
        </el-col>
      </el-row>
      <!-- 工作流导航 -->
      <el-card class="mt-lg" shadow="never">
        <template #header>
          <span style="font-weight: 600">工作流导航</span>
        </template>
        <div style="display: flex; gap: 12px; flex-wrap: wrap">
          <el-button type="primary" @click="navToAIFromAnomaly(anomalyId)">AI 诊断</el-button>
          <el-button type="warning" @click="navToRemediationFromAnomaly(anomalyId)">故障处置</el-button>
          <el-button type="success" @click="navToTicketFromAnomaly(anomalyId)">创建工单</el-button>
          <el-button type="info" @click="navToPolicyFromAnomaly(anomalyId)">匹配策略</el-button>
        </div>
      </el-card>

   </div>
   <!-- 分配对话框 -->
   <el-dialog v-model="showAssignDialog" title="分配处理人" width="480px">
     <el-form label-width="80px">
       <el-form-item label="处理人ID">
         <el-input v-model="assigneeId" placeholder="输入处理人用户ID" />
       </el-form-item>
     </el-form>
     <template #footer>
       <el-button @click="showAssignDialog = false">取消</el-button>
       <el-button type="primary" :loading="actionLoading === 'assign'" @click="handleAssign">确定</el-button>
     </template>
   </el-dialog>
 </div>
</template>
<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { anomalyService, alertService } from '@/shared/api'
import { useWorkflowNav } from '@/shared/composables/useWorkflowNav'
const route = useRoute()
const router = useRouter()
const anomalyId = route.params.id as string

const { navToAIFromAnomaly, navToRemediationFromAnomaly, navToTicketFromAnomaly, navToPolicyFromAnomaly } = useWorkflowNav()

const loading = ref(false)
const alertsLoading = ref(false)
const actionLoading = ref('')
const anomaly = ref<Record<string, any>>({})
const relatedAlerts = ref<any[]>([])
const timeline = ref<any[]>([])
const showAssignDialog = ref(false)
const assigneeId = ref('')

// Severity helpers
const severityMap: Record<string, string> = { critical: '严重', high: '高', medium: '中', low: '低' }
const severityLabel = (s: string) => severityMap[s] || s
const severityType = (s: string): '' | 'success' | 'warning' | 'danger' | 'info' =>
  ({ critical: 'danger', high: 'warning', medium: 'primary', low: 'info' } as any)[s] || 'info'

// Status helpers
const statusMap: Record<string, string> = { open: '新建', acknowledged: '已确认', assigned: '已分配', closed: '已关闭' }
const statusLabel = (s: string) => statusMap[s] || s
const statusType = (s: string): '' | 'success' | 'warning' | 'danger' | 'info' =>
  ({ open: 'danger', acknowledged: 'warning', assigned: 'primary', closed: 'success' } as any)[s] || 'info'

// Alert status helpers
const alertStatusLabel = (s: string) => ({ firing: '告警中', resolved: '已恢复', acknowledged: '已确认', suppressed: '已抑制' } as any)[s] || s
const alertStatusType = (s: string): '' | 'success' | 'warning' | 'danger' | 'info' =>
  ({ firing: 'danger', resolved: 'success', acknowledged: 'warning', suppressed: 'info' } as any)[s] || 'info'

// Timeline type
const timelineType = (t: string): '' | 'success' | 'warning' | 'danger' | 'info' =>
  ({ created: 'primary', acknowledged: 'warning', assigned: 'primary', escalated: 'danger', closed: 'success' } as any)[t] || 'info'

// Fetch anomaly detail
async function fetchAnomaly() {
  loading.value = true
  try {
    const res = await anomalyService.get(anomalyId)
    const data = res.data?.data || res.data
    anomaly.value = data
    buildTimeline(data)
    // Also fetch related alerts
    await fetchRelatedAlerts(data)
  } catch (e: any) {
    ElMessage.error(e.message || '获取异常详情失败')
  } finally {
    loading.value = false
  }
}

// Fetch related alerts for this anomaly
async function fetchRelatedAlerts(detail: Record<string, any>) {
  alertsLoading.value = true
  try {
    const params: Record<string, any> = { page_size: 20 }
    if (detail.asset_id) params.asset_id = detail.asset_id
    const res = await alertService.list(params)
    const items = res.data?.data?.items || res.data?.data || []
    relatedAlerts.value = items
  } catch {
    relatedAlerts.value = []
  } finally {
    alertsLoading.value = false
  }
}

// Build timeline from anomaly data
function buildTimeline(data: Record<string, any>) {
  const items: any[] = []
  if (data.created_at) items.push({ time: data.created_at, action: '异常创建', type: 'created', detail: data.source ? '来源: ' + data.source : 'primary'})
  if (data.acknowledged_at) items.push({ time: data.acknowledged_at, action: '已确认', type: 'acknowledged', detail: data.acknowledged_by ? '操作人: ' + data.acknowledged_by : 'primary'})
  if (data.assigned_at) items.push({ time: data.assigned_at, action: '已分配', type: 'assigned', detail: data.assignee_name ? '处理人: ' + data.assignee_name : 'primary'})
  if (data.escalated_at) items.push({ time: data.escalated_at, action: '已升级', type: 'escalated', detail: 'primary'})
  if (data.closed_at) items.push({ time: data.closed_at, action: '已关闭', type: 'closed', detail: data.close_reason || '' })
  // Sort by time desc
  items.sort((a, b) => (b.time || '').localeCompare(a.time || ''))
  timeline.value = items
}

// Actions
async function handleAcknowledge() {
  try {
    await ElMessageBox.confirm('确认该异常？', '确认操作')
    actionLoading.value = 'ack'
    await anomalyService.acknowledge(anomalyId)
    ElMessage.success('已确认')
    await fetchAnomaly()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e.message || '操作失败')
  } finally {
    actionLoading.value = ''
  }
}

async function handleAssign() {
  if (!assigneeId.value) {
    ElMessage.warning('请输入处理人ID')
    return
  }
  try {
    actionLoading.value = 'assign'
    await anomalyService.assign(anomalyId, { assignee_id: assigneeId.value })
    ElMessage.success('分配成功')
    showAssignDialog.value = false
    assigneeId.value = ''
    await fetchAnomaly()
  } catch (e: any) {
    ElMessage.error(e.message || '分配失败')
  } finally {
    actionLoading.value = ''
  }
}

async function handleEscalate() {
  try {
    await ElMessageBox.confirm('确认升级该异常？升级后将通知更高级别处理人', '升级确认')
    actionLoading.value = 'escalate'
    await anomalyService.escalate(anomalyId)
    ElMessage.success('已升级')
    await fetchAnomaly()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e.message || '操作失败')
  } finally {
    actionLoading.value = ''
  }
}

async function handleClose() {
  try {
    const { value } = await ElMessageBox.prompt('请输入关闭原因', '关闭异常', { inputPattern: /.+/, inputErrorMessage: '请输入关闭原因' })
    actionLoading.value = 'close'
    await anomalyService.close(anomalyId, { reason: value })
    ElMessage.success('已关闭')
    await fetchAnomaly()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e.message || '操作失败')
  } finally {
    actionLoading.value = ''
  }
}

async function handleConvertTicket() {
  try {
    await ElMessageBox.confirm('将该异常转为工单？', '转工单')
    actionLoading.value = 'ticket'
    await anomalyService.convertToTicket(anomalyId)
    ElMessage.success('已转工单')
    await fetchAnomaly()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e.message || '操作失败')
  } finally {
    actionLoading.value = ''
  }
}

onMounted(() => fetchAnomaly())
</script>

<style scoped>
.text-tertiary { color: var(--autops-info); font-size: var(--autops-font-12); }
</style>
