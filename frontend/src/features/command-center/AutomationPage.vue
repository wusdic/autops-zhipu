<template>
  <div>
    <el-row :gutter="16">
      <!-- 脚本库 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>脚本库</span>
              <el-button type="primary" size="small" @click="showScriptDialog = true">新建脚本</el-button>
            </div>
          </template>
          <el-table :data="scripts" v-loading="loading" stripe size="small">
            <el-table-column prop="name" label="名称" min-width="150" />
            <el-table-column prop="script_type" label="类型" width="90">
              <template #default="{ row }">
                <el-tag size="small">{{ row.script_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="risk_level" label="风险" width="70">
              <template #default="{ row }">
                <el-tag :type="row.risk_level==='high'?'danger':row.risk_level==='medium'?'warning':'success'" size="small">
                  {{ row.risk_level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="timeout" label="超时" width="60" />
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="viewScript(row)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 策略列表 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>策略管理</span>
              <el-button type="primary" size="small" @click="showPolicyDialog = true">新建策略</el-button>
            </div>
          </template>
          <el-table :data="policies" v-loading="policyLoading" stripe size="small">
            <el-table-column prop="name" label="名称" min-width="150" />
            <el-table-column prop="risk_level" label="风险" width="70">
              <template #default="{ row }">
                <el-tag :type="row.risk_level==='high'?'danger':row.risk_level==='medium'?'warning':'success'" size="small">
                  {{ row.risk_level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="70">
              <template #default="{ row }">
                <el-switch v-model="row.enabled" size="small" @change="togglePolicy(row)" />
              </template>
            </el-table-column>
            <el-table-column prop="requires_approval" label="审批" width="60">
              <template #default="{ row }">{{ row.requires_approval ? '是' : '否' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="simulatePolicy(row)">模拟</el-button>
                <el-button size="small" type="danger" @click="deletePolicy(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 执行历史 -->
    <el-card style="margin-top:16px">
      <template #header><span>执行历史</span></template>
      <el-table :data="executions" v-loading="execLoading" stripe size="small">
        <el-table-column prop="id" label="执行ID" width="160" show-overflow-tooltip />
        <el-table-column prop="execution_type" label="类型" width="80" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="execStatusTag(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_dry_run" label="Dry-Run" width="70">
          <template #default="{ row }">{{ row.is_dry_run ? '是' : '否' }}</template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险" width="60" />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="error_message" label="错误" min-width="200" show-overflow-tooltip />
      </el-table>
    </el-card>

    <!-- 脚本详情 Drawer -->
    <el-drawer v-model="showScriptDetail" title="脚本详情" size="600px">
      <template v-if="currentScript">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ currentScript.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ currentScript.script_type }}</el-descriptions-item>
          <el-descriptions-item label="风险级别">{{ currentScript.risk_level }}</el-descriptions-item>
          <el-descriptions-item label="超时">{{ currentScript.timeout }}s</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin-top:16px">脚本内容</h4>
        <el-input type="textarea" :rows="15" :model-value="currentScript.content" readonly style="font-family:monospace" />
      </template>
    </el-drawer>

    <!-- 策略模拟结果 -->
    <el-dialog v-model="showSimResult" title="策略模拟结果" width="500px">
      <el-descriptions :column="1" border v-if="simResult">
        <el-descriptions-item label="策略">{{ simResult.policy_name }}</el-descriptions-item>
        <el-descriptions-item label="触发匹配">{{ simResult.trigger_matched ? '✅ 是' : '❌ 否' }}</el-descriptions-item>
        <el-descriptions-item label="风险级别">{{ simResult.risk_level }}</el-descriptions-item>
        <el-descriptions-item label="需要审批">{{ simResult.requires_approval ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="动作链">
          <pre>{{ JSON.stringify(simResult.action_chain, null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

const loading = ref(false)
const scripts = ref<any[]>([])
const policyLoading = ref(false)
const policies = ref<any[]>([])
const execLoading = ref(false)
const executions = ref<any[]>([])
const showScriptDetail = ref(false)
const currentScript = ref<any>(null)
const showSimResult = ref(false)
const simResult = ref<any>(null)
const showScriptDialog = ref(false)
const showPolicyDialog = ref(false)

function formatTime(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '' }
function execStatusTag(s: string) {
  const m: Record<string, string> = { completed: 'success', failed: 'danger', running: 'warning', pending: 'info', dry_run: 'info' }
  return m[s] || ''
}

async function loadScripts() {
  loading.value = true
  try {
    const { data } = await api.get(R.SCRIPTS, { params: { page: 1, page_size: 100 } })
    if (data.code === 0) scripts.value = data.data.items || []
  } finally { loading.value = false }
}

async function loadPolicies() {
  policyLoading.value = true
  try {
    const { data } = await api.get(R.POLICIES, { params: { page: 1, page_size: 100 } })
    if (data.code === 0) policies.value = data.data.items || []
  } finally { policyLoading.value = false }
}

async function loadExecutions() {
  execLoading.value = true
  try {
    const { data } = await api.get(R.EXECUTIONS, { params: { page: 1, page_size: 50 } })
    if (data.code === 0) executions.value = data.data.items || []
  } finally { execLoading.value = false }
}

function viewScript(row: any) { currentScript.value = row; showScriptDetail.value = true }

async function simulatePolicy(row: any) {
  const { data } = await api.post(`/api/v1/policies/${row.id}/simulate`, { trigger_event: 'test', asset_ids: [] })
  if (data.code === 0) { simResult.value = data.data; showSimResult.value = true }
}

async function togglePolicy(row: any) {
  const { data } = await api.put(`/api/v1/policies/${row.id}`, { enabled: row.enabled })
  if (data.code === 0) ElMessage.success(row.enabled ? '已启用' : '已禁用')
}

async function deletePolicy(row: any) {
  await ElMessageBox.confirm(`确定删除策略 "${row.name}"？`, '确认', { type: 'warning' })
  const { data } = await api.delete(`/api/v1/policies/${row.id}`)
  if (data.code === 0) { ElMessage.success('已删除'); loadPolicies() }
}

onMounted(() => { loadScripts(); loadPolicies(); loadExecutions() })
</script>
