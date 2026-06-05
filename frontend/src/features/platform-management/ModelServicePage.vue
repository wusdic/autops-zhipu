<template>
  <div class="model-service-page">
    <div class="autops-page-header">
      <div class="autops-page-title-row">
        <el-button plain @click="router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <span class="autops-page-title">模型服务</span>
      </div>
      <div class="autops-page-desc">注册和管理 AI 模型服务，配置全局模型参数</div>
    </div>
    <div style="display: flex; gap: 8px; margin-bottom: 16px">
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon> 注册模型
      </el-button>
      <el-button @click="loadData" :loading="loading">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <!-- 模型总览 -->
    <el-row :gutter="16" class="mt-4">
      <el-col :span="6" v-for="stat in overviewStats" :key="stat.label">
        <el-card shadow="hover" class="autops-metric-card">
          <div class="stat-value" :style="{ color: stat.color }">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 模型列表 -->
    <el-card class="mt-4" shadow="never">
      <template #header><span>已注册模型</span></template>
      <el-table stripe :data="models" v-loading="loading"border>
        <el-table-column prop="name" label="模型名称" min-width="180" />
        <el-table-column prop="provider" label="提供商" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.provider }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model_id" label="模型ID" width="200">
          <template #default="{ row }">
            <code>{{ row.model_id }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="endpoint" label="API地址" min-width="200">
          <template #default="{ row }">
            <code class="text-xs">{{ row.endpoint }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : row.status === 'error' ? 'danger' : 'info'" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="latency" label="平均延迟" width="100" />
        <el-table-column prop="call_count" label="近7天调用" width="120" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button plain type="primary" @click="testModel(row)">测试</el-button>
            <el-button plain type="primary" @click="viewMetrics(row)">指标</el-button>
            <el-button plain type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button plain type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 模型配置 -->
    <el-card class="mt-4" shadow="never">
      <template #header><span>全局配置</span></template>
      <el-form :model="globalConfig" label-width="140px">
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="默认模型">
              <el-select v-model="globalConfig.default_model" style="width: 100%">
                <el-option v-for="m in models" :key="m.id" :label="m.name" :value="m.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="请求超时(秒)">
              <el-input-number v-model="globalConfig.timeout" :min="5" :max="300" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大Token">
              <el-input-number v-model="globalConfig.max_tokens" :min="100" :max="32000" style="width: 100%" />
            </el-form-item>
            <el-form-item label="温度">
              <el-slider v-model="globalConfig.temperature" :min="0" :max="200" :step="5" show-input />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <el-button type="primary" @click="saveConfig" :loading="saving">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 注册/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑模型' : '注册新模型'" width="600px" destroy-on-close>
      <el-form :model="form" label-width="100px" :rules="formRules" ref="formRef">
        <el-form-item label="模型名称" prop="name">
          <el-input v-model="form.name" placeholder="如：GLM-4-Plus" />
        </el-form-item>
        <el-form-item label="提供商" prop="provider">
          <el-select v-model="form.provider" style="width: 100%">
            <el-option label="智谱AI" value="zhipu" />
            <el-option label="OpenAI" value="openai" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="本地部署" value="local" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型ID" prop="model_id">
          <el-input v-model="form.model_id" placeholder="如：glm-4-plus" />
        </el-form-item>
        <el-form-item label="API地址" prop="endpoint">
          <el-input v-model="form.endpoint" placeholder="https://api.example.com/v1/chat/completions" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="form.api_key" type="password" show-password placeholder="sk-xxx" />
        </el-form-item>
        <el-form-item label="最大Token">
          <el-input-number v-model="form.max_tokens" :min="100" :max="128000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <!-- 指标对话框 -->
    <el-dialog v-model="metricsVisible" title="模型调用指标" width="600px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="模型">{{ metricsData.name }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(metricsData.status) }}</el-descriptions-item>
        <el-descriptions-item label="总调用">{{ metricsData.call_count }}</el-descriptions-item>
        <el-descriptions-item label="成功率">{{ metricsData.success_rate }}%</el-descriptions-item>
        <el-descriptions-item label="平均延迟">{{ metricsData.avg_latency }}ms</el-descriptions-item>
        <el-descriptions-item label="P99延迟">{{ metricsData.p99_latency }}ms</el-descriptions-item>
        <el-descriptions-item label="Token消耗">{{ metricsData.token_usage }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 连接测试结果对话框 -->
    <el-dialog v-model="testResultVisible" title="连接测试结果" width="500px">
      <el-result v-if="testResultData.success" icon="success" title="连接成功">
        <template #extra>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="模型">{{ testResultData.name }}</el-descriptions-item>
            <el-descriptions-item label="响应时间">{{ testResultData.latency }}ms</el-descriptions-item>
            <el-descriptions-item label="返回内容">{{ testResultData.response || '-' }}</el-descriptions-item>
          </el-descriptions>
        </template>
      </el-result>
      <el-result v-else icon="error" :title="'连接失败: ' + (testResultData.error || '未知错误')">
        <template #extra>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="模型">{{ testResultData.name }}</el-descriptions-item>
            <el-descriptions-item label="错误详情">{{ testResultData.error || '-' }}</el-descriptions-item>
          </el-descriptions>
        </template>
      </el-result>
      <template #footer>
        <el-button type="primary" @click="testResultVisible = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, ArrowLeft } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const metricsVisible = ref(false)
const testResultVisible = ref(false)
const editing = ref<any>(null)
const models = ref<any[]>([])
const metricsData = ref<any>({})
const testResultData = ref<any>({ success: false, name: '', latency: 0, response: '', error: '' })
const formRef = ref()

const overviewStats = computed(() => [
  { label: '注册模型', value: models.value.length, color: '#165dff' },
  { label: '活跃模型', value: models.value.filter(m => m.status === 'active').length, color: '#00b42a' },
  { label: '异常模型', value: models.value.filter(m => m.status === 'error').length, color: '#f53f3f' },
  { label: '今日调用', value: 0, color: '#ff7d00' },
])

const globalConfig = reactive({ default_model: '', timeout: 60, max_tokens: 4096, temperature: 70 })

const form = reactive({
  name: '', provider: 'zhipu', model_id: '', endpoint: '',
  api_key: '', max_tokens: 4096, description: '',
})
const formRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  provider: [{ required: true, message: '请选择提供商', trigger: 'change' }],
  model_id: [{ required: true, message: '请输入模型ID', trigger: 'blur' }],
  endpoint: [{ required: true, message: '请输入API地址', trigger: 'blur' }],
}

function statusLabel(s: string) { return { active: '正常', error: '异常', inactive: '未激活', testing: '测试中' }[s] || s }

async function loadData() {
  loading.value = true
  try {
    const res = await client.get(API.AIOPS.MODEL_AGENTS)
    const data = res.data?.data ?? res.data
    models.value = data?.items || []
  } catch { models.value = [] } finally { loading.value = false }
}

function openDialog(row?: any) {
  editing.value = row || null
  if (row) Object.assign(form, row)
  else Object.assign(form, { name: '', provider: 'zhipu', model_id: '', endpoint: '', api_key: '', max_tokens: 4096, description: '' })
  dialogVisible.value = true
}

async function handleSubmit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    if (editing.value) {
      await client.put(API.AIOPS.MODEL_AGENT_DETAIL(editing.value.id), form)
    } else {
      await client.post(API.AIOPS.MODEL_AGENTS, form)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadData()
  } catch { ElMessage.error('操作失败') } finally { submitting.value = false }
}

async function testModel(row: any) {
  testResultData.value = { success: false, name: row.name, latency: 0, response: '', error: '' }
  testResultVisible.value = true
  try {
    const startTime = Date.now()
    const res = await client.post(API.AIOPS.MODEL_AGENT_TEST(row.id))
    const elapsed = Date.now() - startTime
    const result = res.data?.data || res.data
    testResultData.value = {
      success: true,
      name: row.name,
      latency: elapsed,
      response: result?.response || result?.content || '测试连接成功',
      error: '',
    }
    ElMessage.success('测试完成')
  } catch (e: any) {
    testResultData.value = {
      success: false,
      name: row.name,
      latency: 0,
      response: '',
      error: e.response?.data?.message || e.message || '连接失败',
    }
  }
}

function viewMetrics(row: any) {
  // 后端暂无 metrics 端点，展示模型基础信息
  metricsData.value = { ...row, call_count: row.call_count ?? '-', success_rate: row.success_rate ?? '-', avg_latency: row.avg_latency ?? '-', p99_latency: row.p99_latency ?? '-', token_usage: row.token_usage ?? '-' }
  metricsVisible.value = true
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm('确认删除模型「' + row.name + '」？', '删除确认', { type: 'warning' })
    await client.delete(API.AIOPS.MODEL_AGENT_DETAIL(row.id))
    ElMessage.success('已删除'); loadData()
  } catch { /* cancelled */ }
}

async function saveConfig() {
  saving.value = true
  try {
    await client.post(API.AIOPS.MODEL_CONFIG, {
      default_model: globalConfig.default_model,
      timeout: globalConfig.timeout,
      max_tokens: globalConfig.max_tokens,
      temperature: globalConfig.temperature / 100,
    })
    ElMessage.success('全局配置已保存')
  } catch {
    ElMessage.error('配置保存失败')
  } finally { saving.value = false }
}

onMounted(loadData)
</script>

<style scoped>
.model-service-page { padding: var(--autops-space-xl); }
.mt-4 { margin-top: var(--autops-space-lg); }
.text-xs { font-size: var(--autops-font-12); }
</style>
