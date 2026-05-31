<template>
  <div class="execution-detail">
    <!-- Back Button -->
    <el-page-header @back="$router.back()" style="margin-bottom: 16px">
      <template #content>
        <span>执行详情 — {{ executionId }}</span>
      </template>
    </el-page-header>

    <!-- Basic Info -->
    <el-card v-loading="loading">
      <template #header>
        <span>基本信息</span>
      </template>
      <el-descriptions v-if="execution" :column="3" border>
        <el-descriptions-item label="执行ID">{{ execution.id }}</el-descriptions-item>
        <el-descriptions-item label="策略名称">{{ execution.policy_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(execution.status)">{{ statusLabel(execution.status) }}</el-tag>
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
    </el-card>

    <!-- Steps -->
    <el-card style="margin-top: 16px">
      <template #header>
        <span>执行步骤</span>
      </template>
      <el-table :data="steps" stripe v-if="steps.length > 0">
        <el-table-column type="index" label="#" width="60" />
        <el-table-column prop="name" label="步骤名称" min-width="160" />
        <el-table-column prop="action_type" label="动作类型" width="140" />
        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="180" />
        <el-table-column prop="finished_at" label="结束时间" width="180" />
        <el-table-column prop="result" label="结果" min-width="200" show-overflow-tooltip />
      </el-table>
      <el-empty v-else description="暂无步骤数据" />
    </el-card>

    <!-- Realtime Logs -->
    <el-card style="margin-top: 16px">
      <template #header>
        <div class="card-header">
          <span>实时日志</span>
          <el-button size="small" @click="loadLogs" :loading="logsLoading">刷新日志</el-button>
        </div>
      </template>
      <div class="log-container" v-loading="logsLoading">
        <pre v-if="logs.length > 0" class="log-content">{{ logs.join('\n') }}</pre>
        <el-empty v-else description="暂无日志" :image-size="60" />
      </div>
    </el-card>

    <!-- Approve Action -->
    <el-card v-if="execution && execution.status === 'pending'" style="margin-top: 16px">
      <template #header>
        <span>审批操作</span>
      </template>
      <el-form :inline="true">
        <el-form-item label="审批备注">
          <el-input v-model="approveComment" placeholder="可选填写审批意见" style="width: 360px" />
        </el-form-item>
        <el-form-item>
          <el-button type="success" @click="approveExecution(true)" :loading="approving">通过并执行</el-button>
          <el-button type="danger" @click="approveExecution(false)" :loading="approving">驳回</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Execution Result Summary -->
    <el-card v-if="execution && (execution.status === 'completed' || execution.status === 'failed')" style="margin-top: 16px">
      <template #header>
        <span>执行结果</span>
      </template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="执行结果">
          <el-tag :type="execution.status === 'completed' ? 'success' : 'danger'" size="large">
            {{ execution.status === 'completed' ? '执行成功' : '执行失败' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="结果详情" v-if="execution.result_detail">
          <pre style="margin: 0; font-family: monospace; font-size: 13px; white-space: pre-wrap">{{ execution.result_detail }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="错误信息" v-if="execution.error_message">
          <span style="color: #f56c6c">{{ execution.error_message }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const route = useRoute()
const executionId = route.params.id as string

const loading = ref(false)
const logsLoading = ref(false)
const approving = ref(false)
const execution = ref<any>(null)
const logs = ref<string[]>([])
const approveComment = ref('')

const steps = computed(() => execution.value?.steps || [])

let logTimer: ReturnType<typeof setInterval> | null = null

function statusType(s: string) {
  const map: Record<string, string> = {
    pending: 'warning', running: '', completed: 'success', failed: 'danger', cancelled: 'info',
  }
  return map[s] || 'info'
}

function statusLabel(s: string) {
  const map: Record<string, string> = {
    pending: '待审批', running: '执行中', completed: '已完成', failed: '失败', cancelled: '已取消',
  }
  return map[s] || s
}

async function loadExecution() {
  loading.value = true
  try {
    const { data } = await api.get(API.EXECUTION_DETAIL(executionId))
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
    const { data } = await api.get(API.LOGS.EXECUTION(executionId))
    if (data.code === 0) {
      logs.value = data.data.items || data.data.lines || []
    }
  } catch (e: any) {
    ElMessage.error('加载日志失败: ' + (e.message || e))
  } finally {
    logsLoading.value = false
  }
}

async function approveExecution(approved: boolean) {
  approving.value = true
  try {
    const { data } = await api.post(API.EXECUTION_APPROVE(executionId), {
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

onUnmounted(() => {
  if (logTimer) clearInterval(logTimer)
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.log-container {
  max-height: 400px;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 4px;
  padding: 12px;
}
.log-content {
  margin: 0;
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
