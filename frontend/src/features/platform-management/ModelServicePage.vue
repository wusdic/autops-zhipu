<template>
  <div class="autops-page-container">
    <PageHeader title="模型服务" desc="注册和管理 AI 模型服务，配置全局模型参数">
      <template #actions>
        <el-button type="primary" @click="openDialog()">
          <el-icon><Plus /></el-icon> 注册模型
        </el-button>
        <el-button @click="loadData" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </template>
    </PageHeader>

    <!-- 模型总览 -->
    <el-row :gutter="16" class="mt-lg">
      <el-col :span="6" v-for="stat in overviewStats" :key="stat.label">
        <el-card shadow="hover" class="autops-metric-card">
          <div class="stat-value" :style="{ color: stat.color }">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 模型列表 -->
    <el-card class="mt-lg" shadow="never">
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
    <el-card class="mt-lg" shadow="never">
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
          <div class="form-tip">仅用于标识来源，不影响调用方式；所有模型均按 OpenAI 兼容协议调用。</div>
        </el-form-item>
        <el-form-item label="模型ID" prop="model_id">
          <el-input v-model="form.model_id" placeholder="如：glm-4-plus" />
        </el-form-item>
        <el-form-item label="API地址" prop="endpoint">
          <el-input v-model="form.endpoint" placeholder="https://api.example.com/v1/chat/completions" />
          <div class="form-tip">须为 OpenAI 兼容地址（通常以 /v1 结尾，如 http://localhost:11434/v1）。本地模型首次测试加载较慢，超时阈值为 60 秒。</div>
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
      <el-result v-if="testing" icon="info" title="正在测试连接…">
        <template #sub-title>
          <span>正向「{{ testResultData.name }}」发送一次探测请求，本地模型首次加载可能较慢，请稍候。</span>
        </template>
        <template #extra>
          <el-icon class="is-loading" :size="22"><Loading /></el-icon>
        </template>
      </el-result>
      <el-result v-else-if="testResultData.success" icon="success" title="连接成功">
        <template #extra>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="模型">{{ testResultData.name }}</el-descriptions-item>
            <el-descriptions-item label="响应时间">{{ testResultData.latency }}ms</el-descriptions-item>
            <el-descriptions-item label="模型回复">{{ testResultData.response || '-' }}</el-descriptions-item>
          </el-descriptions>
          <div class="form-tip" style="margin-top: 8px">「模型回复」为该模型对探测语句的真实生成结果，内容每次不同属正常现象，仅用于验证模型可正常应答。</div>
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
        <el-button type="primary" :disabled="testing" @click="testResultVisible = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Loading } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { serviceStatusLabel } from '@/shared/utils/labels'
import { API } from '@/shared/api/routes'
import PageHeader from '@/shared/components/PageHeader.vue'

const loading = ref(false)
const submitting = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const metricsVisible = ref(false)
const testResultVisible = ref(false)
const testing = ref(false)
const editing = ref<any>(null)
const models = ref<any[]>([])
const metricsData = ref<any>({})
const testResultData = ref<any>({ success: false, name: '', latency: 0, response: '', error: ''})
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

const statusLabel = (s: string): string => serviceStatusLabel(s)

async function loadData() {
  loading.value = true
  try {
    const res = await client.get(API.AIOPS.MODEL_AGENTS)
    const data = res.data?.data ?? res.data
    // 后端返回裸数组（success([...])）；兼容分页 {items} 结构
    models.value = Array.isArray(data) ? data : (data?.items || [])
  } catch { models.value = [] } finally { loading.value = false }
}

async function loadConfig() {
  try {
    const res = await client.get(API.AIOPS.MODEL_CONFIG)
    const cfg = res.data?.data ?? res.data
    if (cfg && typeof cfg === 'object') {
      globalConfig.default_model = cfg.default_model || ''
      if (cfg.timeout) globalConfig.timeout = cfg.timeout
      if (cfg.max_tokens) globalConfig.max_tokens = cfg.max_tokens
      if (cfg.temperature != null) globalConfig.temperature = Math.round(cfg.temperature * 100)
    }
  } catch { /* 无配置时保持默认 */ }
}

function openDialog(row?: any) {
  editing.value = row || null
  if (row) Object.assign(form, row)
  else Object.assign(form, { name: '', provider: 'zhipu', model_id: '', endpoint: '', api_key: '', max_tokens: 4096, description: ''})
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
  // 先进入「测试中」态，避免在请求返回前闪现失败结果界面
  testResultData.value = { success: false, name: row.name, latency: 0, response: '', error: '' }
  testing.value = true
  testResultVisible.value = true
  try {
    const startTime = Date.now()
    const res = await client.post(API.AIOPS.MODEL_AGENT_TEST(row.id))
    const elapsed = Date.now() - startTime
    const result = res.data?.data || res.data
    // 后端测试失败时以 HTTP 200 返回 { success:false, error }，需按内层标志判定
    const ok = result?.success !== false
    testResultData.value = {
      success: ok,
      name: row.name,
      latency: result?.latency ?? elapsed,
      response: ok ? (result?.response || result?.content || '（无内容）') : '',
      error: ok ? '' : (result?.error || '连接失败'),
    }
    if (ok) ElMessage.success('连接成功')
    else ElMessage.error('连接失败')
  } catch (e: any) {
    testResultData.value = {
      success: false,
      name: row.name,
      latency: 0,
      response: '',
      error: e.response?.data?.message || e.message || '连接失败',
    }
    ElMessage.error('连接失败')
  } finally {
    testing.value = false
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

onMounted(() => { loadData(); loadConfig() })
</script>

<style scoped>
.model-service-page { padding: var(--autops-space-xl); }
.mt-4 { margin-top: var(--autops-space-lg); }
.text-xs { font-size: var(--autops-font-12); }
.form-tip { margin-top: 4px; font-size: var(--autops-font-12); color: var(--autops-text-tertiary); line-height: 1.5; }
</style>
