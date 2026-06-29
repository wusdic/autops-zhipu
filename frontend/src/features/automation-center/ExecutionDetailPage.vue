<template>
  <div class="autops-page-container">
    <PageHeader title="执行详情" back desc="查看单次执行的详细信息、步骤和日志" />

    <!-- Basic Info -->
    <div class="autops-card" v-loading="loading">
      
        <div class="autops-card-header">
          <span>基本信息</span>
          <div class="autops-card-header-actions">
            <el-button
              type="success"
              @click="navToReportFromExecution(executionId)"
            >
              生成执行报告
            </el-button>
            <el-button
              v-if="execution && (execution.status === 'running' || execution.status === 'pending')"
              type="warning"
              @click="handleCancel"
              :loading="cancelling"
            >
              取消执行
            </el-button>
            <el-button
              v-if="execution && execution.status === 'failed'"
              type="danger"
              @click="showRollbackDialog = true"
            >
              回滚
            </el-button>
          </div>
        </div>
      
      <el-descriptions v-if="execution" :column="3" border>
        <el-descriptions-item label="执行ID">{{ execution.id }}</el-descriptions-item>
        <el-descriptions-item label="策略名称">{{ execution.policy_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="(statusType(execution.status)) as TagType">{{ statusLabel(execution.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ execution.started_at || '-' }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ execution.finished_at || '-' }}</el-descriptions-item>
        <el-descriptions-item label="耗时">{{ execution.duration ? execution.duration + 's' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="触发资产">{{ execution.asset_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="触发人">{{ execution.triggered_by || '-' }}</el-descriptions-item>
        <el-descriptions-item label="结果">
          <span v-if="execution.result">{{ execution.result }}</span>
          <span v-else>-</span>
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- Steps -->
    <div class="autops-card mt-lg">
      <div class="autops-card-header">
                <span>执行步骤</span>
      </div>
      <el-table stripe
 :data="steps"v-if="steps.length > 0"
        row-key="id"
        @row-click="toggleStepExpand"
        :row-class-name="stepRowClass"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="step-log-container" v-loading="stepLogsLoading[row.id]">
              <pre v-if="stepLogs[row.id] && stepLogs[row.id].length > 0" class="log-content">{{
                stepLogs[row.id].join('\n')
              }}</pre>
              <el-empty v-else description="该步骤暂无日志" :image-size="40" />
            </div>
          </template>
        </el-table-column>
        <el-table-column type="index" label="#" width="60" />
        <el-table-column prop="name" label="步骤名称" min-width="160" />
        <el-table-column prop="action_type" label="动作类型" width="140" />
        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="(statusType(row.status)) as TagType" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="180" />
        <el-table-column prop="finished_at" label="结束时间" width="180" />
        <el-table-column prop="result" label="结果" min-width="200" show-overflow-tooltip />
      </el-table>
      <el-empty v-else description="暂无步骤数据" />
    </div>

    <!-- Realtime Logs -->
    <div class="autops-card mt-lg">
      
        <div class="autops-card-header">
          <span>实时日志</span>
          <div>
            <el-button size="small" @click="downloadLogs" :disabled="logs.length === 0">下载日志</el-button>
            <el-button size="small" @click="loadLogs" :loading="logsLoading">刷新日志</el-button>
          </div>
        </div>
      
      <div class="log-container" v-loading="logsLoading">
        <pre v-if="logs.length > 0" class="log-content">{{ logs.join('\n') }}</pre>
        <el-empty v-else description="暂无日志" :image-size="60" />
      </div>
    </div>

    <!-- Approve Action -->
    <div v-if="execution && execution.status === 'pending'" class="autops-card mt-lg">
      <div class="autops-card-header">
                <span>审批操作</span>
      </div>
      <el-form :inline="true">
        <el-form-item label="审批备注">
          <el-input v-model="approveComment" placeholder="可选填写审批意见" style="width: 360px" />
        </el-form-item>
        <el-form-item>
          <el-button type="success" @click="approveExecution(true)" :loading="approving">通过并执行</el-button>
          <el-button type="danger" @click="approveExecution(false)" :loading="approving">驳回</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- Execution Result Summary -->
    <div v-if="execution && (execution.status === 'completed' || execution.status === 'failed')" class="autops-card mt-lg">
      <div class="autops-card-header">
                <span>执行结果</span>
      </div>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="执行结果">
          <el-tag :type="execution.status === 'completed' ? 'success' : 'danger'" size="large">
            {{ execution.status === 'completed' ? '执行成功' : '执行失败' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="结果详情" v-if="execution.result_detail">
          <pre class="result-detail-pre">{{ execution.result_detail }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="错误信息" v-if="execution.error_message">
          <span class="text-danger">{{ execution.error_message }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- Verification Result Section -->
    <div v-if="execution && (execution.status === 'completed' || execution.status === 'failed')" class="autops-card mt-lg" v-loading="verificationLoading">
      
        <div class="autops-card-header">
          <span>验证结果</span>
          <el-button size="small" @click="loadVerification" :loading="verificationLoading">刷新验证</el-button>
        </div>
      
      <template v-if="verification">
        <el-descriptions :column="2" border class="mb-lg">
          <el-descriptions-item label="验证状态">
            <el-tag
              :type="verification.passed ? 'success' : 'danger'"
              size="large"
            >
              {{ verification.passed ? '验证通过' : '验证失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="检查项数">
            {{ verification.checks?.length || 0 }}
          </el-descriptions-item>
        </el-descriptions>
        <el-table stripe
          v-if="verification.checks && verification.checks.length > 0"
          :data="verification.checks"
          border
        >
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="name" label="检查项" min-width="180" />
          <el-table-column prop="status" label="状态" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'pass' ? 'success' : 'danger'" size="small">
                {{ row.status === 'pass' ? '通过' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="详情" min-width="260" show-overflow-tooltip />
        </el-table>
        <el-empty v-else description="暂无验证检查数据" :image-size="60" />
      </template>
      <el-empty v-else-if="!verificationLoading" description="暂无验证结果" :image-size="60" />
    </div>

    <!-- Rollback Dialog -->
    <el-dialog v-model="showRollbackDialog" title="选择回滚脚本/Playbook" width="600px" destroy-on-close>
      <el-form label-width="100px">
        <el-form-item label="回滚类型">
          <el-radio-group v-model="rollbackType">
            <el-radio value="script">脚本</el-radio>
            <el-radio value="playbook">Playbook</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="选择项目">
          <el-select
            v-model="rollbackItemId"
            placeholder="请选择"
            filterable
            style="width: 100%"
            v-loading="rollbackItemsLoading"
          >
            <el-option
              v-for="item in rollbackItems"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="rollbackComment"
            type="textarea"
            :rows="3"
            placeholder="可选填写回滚原因"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRollbackDialog = false">取消</el-button>
        <el-button
          type="danger"
          @click="submitRollback"
          :loading="rollbackSubmitting"
          :disabled="!rollbackItemId"
        >
          确认回滚
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import type { TagType } from '@/shared/types'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/shared/api/client'
import PageHeader from '@/shared/components/PageHeader.vue'
import { API as R } from '@/shared/api/routes'
import { execStatusTag, execStatusLabel } from '@/shared/utils/labels'
import { useWorkflowNav } from '@/shared/composables/useWorkflowNav'

const route = useRoute()
const executionId = route.params.id as string

const { navToReportFromExecution } = useWorkflowNav()

const loading = ref(false)
const logsLoading = ref(false)
const approving = ref(false)
const cancelling = ref(false)
const verificationLoading = ref(false)
const execution = ref<any>(null)
const logs = ref<string[]>([])
const approveComment = ref('')

// Verification result
const verification = ref<any>(null)

// Per-step logs
const stepLogs = reactive<Record<string, string[]>>({})
const stepLogsLoading = reactive<Record<string, boolean>>({})

// Rollback dialog
const showRollbackDialog = ref(false)
const rollbackType = ref<'script' | 'playbook'>('script')
const rollbackItemId = ref('')
const rollbackComment = ref('')
const rollbackItems = ref<any[]>([])
const rollbackItemsLoading = ref(false)
const rollbackSubmitting = ref(false)

const steps = computed(() => execution.value?.steps || [])

let logTimer: ReturnType<typeof setInterval> | null = null

// 执行状态统一取自 labels.ts（覆盖全部 canonical 状态）
const statusType = (s: string): TagType => execStatusTag(s) as TagType
const statusLabel = (s: string): string => execStatusLabel(s)

async function loadExecution() {
  loading.value = true
  try {
    const { data } = await api.get(R.EXECUTION_DETAIL(executionId))
    if (data.code === 0) {
      execution.value = data.data
    }
  } catch (e: any) {
    ElMessage.error('加载执行详情失败: ' + (e.message || e))
  } finally {
    loading.value = false
  }
}

async function loadLogs() {
  logsLoading.value = true
  try {
    const { data } = await api.get(R.LOGS.EXECUTION(executionId))
    if (data.code === 0) {
      logs.value = data.data.items || data.data.lines || []
    }
  } catch (e: any) {
    ElMessage.error('加载日志失败: ' + (e.message || e))
  } finally {
    logsLoading.value = false
  }
}

async function loadStepLogs(stepId: string) {
  stepLogsLoading[stepId] = true
  try {
    const { data } = await api.get(R.LOGS.STEP(executionId, stepId))
    if (data.code === 0) {
      stepLogs[stepId] = data.data.items || data.data.lines || []
    }
  } catch (e: any) {
    ElMessage.error('加载步骤日志失败: ' + (e.message || e))
  } finally {
    stepLogsLoading[stepId] = false
  }
}

function toggleStepExpand(row: any) {
  if (!row.id) return
  if (!stepLogs[row.id]) {
    loadStepLogs(row.id)
  }
}

function stepRowClass({ row }: { row: any }) {
  return 'step-row--clickable'
}

async function approveExecution(approved: boolean) {
  approving.value = true
  try {
    const { data } = await api.post(R.EXECUTION_APPROVE(executionId), {
      approved,
      comment: approveComment.value,
    })
    if (data.code === 0) {
      ElMessage.success(approved ? '已通过，开始执行' : '已驳回')
      loadExecution()
    } else {
      ElMessage.error(data.message || '审批操作失败')
    }
  } catch (e: any) {
    ElMessage.error('审批操作失败: ' + (e.message || e))
  } finally {
    approving.value = false
  }
}

// --- Cancel Execution ---
async function handleCancel() {
  try {
    await ElMessageBox.confirm(
      '确定要取消此执行吗？此操作不可撤销。',
      '取消执行',
      { confirmButtonText: '确定取消', cancelButtonText: '返回', type: 'warning' },
    )
  } catch {
    return // user dismissed
  }

  cancelling.value = true
  try {
    const { data } = await api.post(R.EXECUTION_CANCEL(executionId))
    if (data.code === 0) {
      ElMessage.success('执行已取消')
      loadExecution()
    } else {
      ElMessage.error(data.message || '取消执行失败')
    }
  } catch (e: any) {
    ElMessage.error('取消执行失败: ' + (e.message || e))
  } finally {
    cancelling.value = false
  }
}

// --- Verification Results ---
async function loadVerification() {
  verificationLoading.value = true
  try {
    const { data } = await api.get(R.EXECUTION_VERIFICATION(executionId))
    if (data.code === 0) {
      verification.value = data.data
    }
  } catch (e: any) {
    // Verification endpoint may not exist for all executions — silently ignore 404
    if (e?.response?.status !== 404) {
      ElMessage.error('加载验证结果失败: ' + (e.message || e))
    }
  } finally {
    verificationLoading.value = false
  }
}

// --- Rollback ---
async function loadRollbackItems() {
  rollbackItemsLoading.value = true
  try {
    const url = rollbackType.value === 'script' ? R.SCRIPTS : R.PLAYBOOKS
    const { data } = await api.get(url)
    if (data.code === 0) {
      rollbackItems.value = data.data.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载回滚项目列表失败: ' + (e.message || e))
  } finally {
    rollbackItemsLoading.value = false
  }
}

async function submitRollback() {
  if (!rollbackItemId.value) return

  rollbackSubmitting.value = true
  try {
    const payload: any = {
      type: rollbackType.value === 'script' ? 'script_execution' : 'playbook_execution',
      ref_id: rollbackItemId.value,
      comment: rollbackComment.value || '回滚执行 ' + executionId,
      rollback_for: executionId,
      asset_id: execution.value?.asset_id,
    }
    const { data } = await api.post(R.EXECUTIONS, payload)
    if (data.code === 0) {
      ElMessage.success('回滚执行已创建')
      showRollbackDialog.value = false
      rollbackItemId.value = ''
      rollbackComment.value = ''
    } else {
      ElMessage.error(data.message || '创建回滚执行失败')
    }
  } catch (e: any) {
    ElMessage.error('创建回滚执行失败: ' + (e.message || e))
  } finally {
    rollbackSubmitting.value = false
  }
}

// --- Download Logs ---
function downloadLogs() {
  if (logs.value.length === 0) return
  const content = logs.value.join('\n')
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'execution-' + executionId + '-logs.txt'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// --- Watch rollback type change to reload items ---
import { watch } from 'vue'
watch(rollbackType, () => {
  rollbackItemId.value = ''
  rollbackItems.value = []
  loadRollbackItems()
})

// Auto-refresh logs when execution is running
function startLogPolling() {
  logTimer = setInterval(() => {
    if (execution.value?.status === 'running') {
      loadLogs()
      loadExecution()
    }
  }, 5000)
}

onMounted(() => {
  loadExecution()
  loadLogs()
  startLogPolling()
})

// Load verification when execution finishes (and on mount if already finished)
watch(
  () => execution.value?.status,
  (status) => {
    if (status === 'completed' || status === 'failed') {
      loadVerification()
    }
  },
)
</script>

<style scoped>
.result-detail-pre {
  margin: 0;
  font-family: monospace;
  font-size: 13px;
  white-space: pre-wrap;
}

.log-container {
  max-height: 400px;
  overflow-y: auto;
  background: var(--autops-terminal-bg);
  border-radius: var(--autops-radius-sm);
  padding: var(--autops-space-md);
}
.log-content {
  margin: 0;
  font-family: 'Courier New', Courier, monospace;
  font-size: var(--autops-font-13);
  color: var(--autops-text-4);
  white-space: pre-wrap;
  word-break: break-all;
}
.step-log-container {
  padding: var(--autops-space-sm) 16px;
  max-height: 300px;
  overflow-y: auto;
  background: var(--autops-terminal-bg);
  border-radius: var(--autops-radius-sm);
  margin: 4px 0;
}
:deep(.step-row--clickable) {
  cursor: pointer;
}
</style>
