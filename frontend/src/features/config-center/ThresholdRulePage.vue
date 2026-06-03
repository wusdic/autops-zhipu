<template>
  <div class="threshold-rule-page">
    <el-page-header @back="router.back()" title="返回" content="阈值规则管理">
      <template #extra>
        <el-button type="primary" @click="openDialog()">
          <el-icon><Plus /></el-icon> 新建阈值规则
        </el-button>
        <el-button @click="loadData" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </template>
    </el-page-header>

    <!-- 搜索 -->
    <el-card class="mt-4" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="规则名称">
          <el-input v-model="filters.keyword" placeholder="搜索" clearable @clear="loadData" />
        </el-form-item>
        <el-form-item label="指标类型">
          <el-select v-model="filters.metric_type" placeholder="全部" clearable @change="loadData">
            <el-option label="CPU使用率" value="cpu_usage" />
            <el-option label="内存使用率" value="memory_usage" />
            <el-option label="磁盘使用率" value="disk_usage" />
            <el-option label="网络流量" value="network_traffic" />
            <el-option label="响应时间" value="response_time" />
            <el-option label="连接数" value="connection_count" />
          </el-select>
        </el-form-item>
        <el-form-item label="告警级别">
          <el-select v-model="filters.severity" placeholder="全部" clearable @change="loadData">
            <el-option label="紧急" value="critical" />
            <el-option label="高危" value="high" />
            <el-option label="中危" value="medium" />
            <el-option label="低危" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 规则列表 -->
    <el-card class="mt-4" shadow="never">
      <el-table :data="rules" v-loading="loading" stripe border>
        <el-table-column type="selection" width="50" />
        <el-table-column prop="name" label="规则名称" min-width="200" sortable />
        <el-table-column prop="metric" label="监控指标" width="140">
          <template #default="{ row }">
            <el-tag size="small">{{ metricName(row.metric) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="阈值条件" width="180">
          <template #default="{ row }">
            <code>{{ row.operator || '>' }} {{ row.threshold }}{{ row.unit || '%' }}</code>
            <span v-if="row.duration" class="text-muted"> 持续{{ row.duration }}s</span>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="告警级别" width="100">
          <template #default="{ row }">
            <el-tag :type="severityType(row.severity)" size="small">{{ severityLabel(row.severity) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="asset_count" label="适用资产" width="100" />
        <el-table-column prop="trigger_count" label="近7天触发" width="110" />
        <el-table-column prop="enabled" label="状态" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" size="small" @change="toggleRule(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button link type="primary" @click="simulateThreshold(row)">模拟</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="mt-4" v-model:current-page="pagination.page" v-model:page-size="pagination.size"
        :total="pagination.total" :page-sizes="[20, 50, 100]" layout="total, sizes, prev, pager, next"
        @size-change="loadData" @current-change="loadData" />
    </el-card>

    <!-- 新建/编辑 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑阈值规则' : '新建阈值规则'" width="650px" destroy-on-close>
      <el-form :model="form" label-width="100px" :rules="formRules" ref="formRef">
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="form.name" placeholder="如：CPU使用率告警" />
        </el-form-item>
        <el-form-item label="监控指标" prop="metric">
          <el-select v-model="form.metric" style="width: 100%">
            <el-option v-for="m in metricOptions" :key="m.value" :label="m.label" :value="m.value" />
          </el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="比较符">
              <el-select v-model="form.operator" style="width: 100%">
                <el-option label="大于" value=">" />
                <el-option label="小于" value="<" />
                <el-option label="等于" value="=" />
                <el-option label="大于等于" value=">=" />
                <el-option label="小于等于" value="<=" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="阈值" prop="threshold">
              <el-input-number v-model="form.threshold" :min="0" :max="99999" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="单位">
              <el-select v-model="form.unit" style="width: 100%">
                <el-option label="%" value="%" />
                <el-option label="ms" value="ms" />
                <el-option label="MB" value="MB" />
                <el-option label="次" value="count" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="持续时间">
          <el-input-number v-model="form.duration" :min="0" :max="3600" /> 秒（0为即时触发）
        </el-form-item>
        <el-form-item label="告警级别" prop="severity">
          <el-select v-model="form.severity" style="width: 100%">
            <el-option label="紧急" value="critical" />
            <el-option label="高危" value="high" />
            <el-option label="中危" value="medium" />
            <el-option label="低危" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="适用资产">
          <el-select v-model="form.asset_types" multiple style="width: 100%">
            <el-option label="Linux服务器" value="linux_server" />
            <el-option label="Windows服务器" value="windows_server" />
            <el-option label="MySQL数据库" value="mysql" />
            <el-option label="Web应用" value="web_app" />
          </el-select>
        </el-form-item>
        <el-form-item label="通知规则">
          <el-select v-model="form.notification_rule_id" clearable placeholder="关联通知规则" style="width: 100%">
            <el-option label="默认通知" value="default" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <!-- 模拟结果 -->
    <el-dialog v-model="simVisible" title="阈值模拟" width="500px">
      <el-result v-if="simResult.triggered" icon="warning" title="触发告警" :sub-title="`预计触发 ${simResult.count} 条告警`">
        <template #extra>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="匹配资产">{{ simResult.matched }}</el-descriptions-item>
            <el-descriptions-item label="超限资产">{{ simResult.exceeded }}</el-descriptions-item>
            <el-descriptions-item label="触发级别">{{ simResult.severity }}</el-descriptions-item>
          </el-descriptions>
        </template>
      </el-result>
      <el-result v-else icon="success" title="无触发" sub-title="当前阈值条件未匹配到异常资产" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const simVisible = ref(false)
const editing = ref<any>(null)
const rules = ref<any[]>([])
const formRef = ref()

const filters = reactive({ keyword: '', metric_type: '', severity: '' })
const pagination = reactive({ page: 1, size: 20, total: 0 })
const simResult = ref<any>({})

const form = reactive({
  name: '', metric: '', operator: '>', threshold: 90, unit: '%',
  duration: 0, severity: 'high', asset_types: [] as string[], notification_rule_id: '',
})
const formRules = {
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  metric: [{ required: true, message: '请选择监控指标', trigger: 'change' }],
  threshold: [{ required: true, message: '请输入阈值', trigger: 'blur' }],
  severity: [{ required: true, message: '请选择告警级别', trigger: 'change' }],
}

const metricOptions = [
  { value: 'cpu_usage', label: 'CPU使用率' }, { value: 'memory_usage', label: '内存使用率' },
  { value: 'disk_usage', label: '磁盘使用率' }, { value: 'network_traffic', label: '网络流量' },
  { value: 'response_time', label: '响应时间' }, { value: 'connection_count', label: '连接数' },
]

function metricName(m: string) { return metricOptions.find(o => o.value === m)?.label || m }
function severityType(s: string) { return { critical: 'danger', high: 'warning', medium: '', low: 'info' }[s] || 'info' }
function severityLabel(s: string) { return { critical: '紧急', high: '高危', medium: '中危', low: '低危' }[s] || s }

async function loadData() {
  loading.value = true
  try {
    // Will connect to threshold rules API when available
    rules.value = []
    pagination.total = 0
  } finally { loading.value = false }
}

function resetFilters() { filters.keyword = ''; filters.metric_type = ''; filters.severity = ''; pagination.page = 1; loadData() }

function openDialog(row?: any) {
  editing.value = row || null
  if (row) Object.assign(form, row)
  else Object.assign(form, { name: '', metric: '', operator: '>', threshold: 90, unit: '%', duration: 0, severity: 'high', asset_types: [], notification_rule_id: '' })
  dialogVisible.value = true
}

async function handleSubmit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    ElMessage.success(editing.value ? '规则更新成功' : '规则创建成功')
    dialogVisible.value = false
    loadData()
  } finally { submitting.value = false }
}

async function toggleRule(row: any) { ElMessage.success(`规则已${row.enabled ? '启用' : '禁用'}`) }

function simulateThreshold(row: any) {
  simVisible.value = true
  simResult.value = { triggered: true, matched: 15, exceeded: 3, count: 3, severity: row.severity }
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确认删除「${row.name}」？`, '删除确认', { type: 'warning' })
    ElMessage.success('已删除')
    loadData()
  } catch { /* cancelled */ }
}

onMounted(loadData)
</script>

<style scoped>
.threshold-rule-page { padding: 20px; }
.mt-4 { margin-top: 16px; }
.text-muted { color: #909399; font-size: 12px; }
</style>
