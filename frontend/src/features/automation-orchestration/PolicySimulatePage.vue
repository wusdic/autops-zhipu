<template>
  <div class="policy-simulate">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>策略模拟 — {{ policyName }}</span>
          <el-button @click="$router.back()">返回</el-button>
        </div>
      </template>

      <!-- Simulate Input -->
      <el-form :model="simParams" label-width="100px" style="max-width: 600px">
        <el-form-item label="资产 ID" required>
          <el-input v-model="simParams.asset_id" placeholder="请输入目标资产 ID" />
        </el-form-item>
        <el-form-item label="告警类型">
          <el-input v-model="simParams.alert_type" placeholder="可选，如 cpu_high" />
        </el-form-item>
        <el-form-item label="严重等级">
          <el-select v-model="simParams.severity" placeholder="可选" clearable>
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="严重" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="扩展参数">
          <el-input
            v-model="simParams.extra_json"
            type="textarea"
            :rows="4"
            placeholder="可选 JSON 扩展参数，如 {\"cpu_usage\": 95}"
            style="font-family: monospace"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="runSimulate" :loading="simulating">执行模拟</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Simulate Results -->
    <el-card v-if="simulateResult" style="margin-top: 16px">
      <template #header>
        <span>模拟结果</span>
      </template>

      <el-descriptions :column="2" border style="margin-bottom: 20px">
        <el-descriptions-item label="是否匹配">
          <el-tag :type="simulateResult.matched ? 'success' : 'info'">
            {{ simulateResult.matched ? '匹配' : '未匹配' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="匹配策略">
          {{ simulateResult.policy_name || policyName }}
        </el-descriptions-item>
        <el-descriptions-item label="风险等级" v-if="simulateResult.risk_level">
          <el-tag :type="riskTagType(simulateResult.risk_level)" size="small">{{ simulateResult.risk_level }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="触发条件" v-if="simulateResult.trigger_condition">
          {{ simulateResult.trigger_condition }}
        </el-descriptions-item>
      </el-descriptions>

      <div v-if="simulateResult.actions && simulateResult.actions.length > 0">
        <h4 style="margin-bottom: 12px">预期执行动作</h4>
        <el-table :data="simulateResult.actions" stripe border>
          <el-table-column type="index" label="#" width="60" />
          <el-table-column prop="action_type" label="动作类型" width="160" />
          <el-table-column prop="target" label="目标" min-width="180" show-overflow-tooltip />
          <el-table-column prop="params" label="参数" min-width="220">
            <template #default="{ row }">
              <span style="font-family: monospace; font-size: 12px">
                {{ typeof row.params === 'object' ? JSON.stringify(row.params) : row.params }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <el-empty v-else-if="simulateResult && !simulateResult.matched" description="未匹配任何策略，无预期执行动作" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const route = useRoute()
const policyId = route.params.id as string

const policyName = ref('加载中...')
const simulating = ref(false)
const simulateResult = ref<any>(null)

const simParams = reactive({
  asset_id: '',
  alert_type: '',
  severity: '',
  extra_json: '',
})

function riskTagType(level: string) {
  const map: Record<string, string> = { low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }
  return map[level] || 'info'
}

async function loadPolicy() {
  try {
    const { data } = await api.get(API.POLICY_DETAIL(policyId))
    if (data.code === 0) {
      policyName.value = data.data.name || data.data.id
    }
  } catch {
    policyName.value = policyId
  }
}

async function runSimulate() {
  if (!simParams.asset_id) {
    ElMessage.warning('资产 ID 为必填项')
    return
  }

  const payload: any = {
    asset_id: simParams.asset_id,
  }
  if (simParams.alert_type) payload.alert_type = simParams.alert_type
  if (simParams.severity) payload.severity = simParams.severity
  if (simParams.extra_json.trim()) {
    try {
      payload.extra = JSON.parse(simParams.extra_json)
    } catch {
      ElMessage.error('扩展参数 JSON 格式错误')
      return
    }
  }

  simulating.value = true
  simulateResult.value = null
  try {
    const { data } = await api.post(API.POLICY_SIMULATE(policyId), payload)
    if (data.code === 0) {
      simulateResult.value = data.data
    } else {
      ElMessage.error(data.message || '模拟失败')
    }
  } catch (e: any) {
    ElMessage.error('模拟请求失败: ' + (e.message || e))
  } finally {
    simulating.value = false
  }
}

onMounted(() => loadPolicy())
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
