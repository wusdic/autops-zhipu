<template>
  <div class="page-container">
    <div class="page-header">
      <h2>阈值规则</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon> 新建规则
      </el-button>
    </div>

    <!-- Filters -->
    <el-card class="mb-md">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-select v-model="filters.metric_name" placeholder="指标名称" clearable @change="fetchData">
            <el-option v-for="m in metricOptions" :key="m" :label="m" :value="m" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.severity" placeholder="严重级别" clearable @change="fetchData">
            <el-option label="严重" value="critical" />
            <el-option label="高" value="high" />
            <el-option label="警告" value="warning" />
            <el-option label="信息" value="info" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.asset_type" placeholder="资产类型" clearable @change="fetchData">
            <el-option label="Linux服务器" value="linux_server" />
            <el-option label="Windows服务器" value="windows_server" />
            <el-option label="数据库" value="database" />
            <el-option label="Web服务" value="web_service" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.enabled" placeholder="状态" clearable @change="fetchData">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <!-- Table -->
    <el-card v-loading="loading">
      <el-table :data="items" stripe empty-text="暂无阈值规则" style="width: 100%">
        <el-table-column prop="name" label="规则名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="metric_name" label="指标" width="140" />
        <el-table-column prop="asset_type" label="资产类型" width="120">
          <template #default="{ row }">{{ row.asset_type || '全部' }}</template>
        </el-table-column>
        <el-table-column label="条件" width="160">
          <template #default="{ row }">
            {{ conditionText(row.condition) }} {{ row.threshold_value }}{{ metricUnit(row.metric_name) }}
          </template>
        </el-table-column>
        <el-table-column prop="duration_seconds" label="持续时间" width="100">
          <template #default="{ row }">{{ row.duration_seconds > 0 ? row.duration_seconds + '秒' : '即时' }}</template>
        </el-table-column>
        <el-table-column prop="severity" label="严重级别" width="100">
          <template #default="{ row }">
            <el-tag :type="severityTag(row.severity)" size="small">{{ severityText(row.severity) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="状态" width="80">
          <template #default="{ row }">
            <el-switch :model-value="row.enabled" @change="toggleRule(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-popconfirm title="确定删除此规则？" @confirm="deleteRule(row)">
              <template #reference>
                <el-button text type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-if="total > pageSize"
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end"
        @current-change="fetchData"
      />
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="editingRule ? '编辑规则' : '新建规则'" width="560px" destroy-on-close>
      <el-form :model="formData" label-width="100px">
        <el-form-item label="规则名称" required>
          <el-input v-model="formData.name" placeholder="如：CPU高负载告警" />
        </el-form-item>
        <el-form-item label="指标名称" required>
          <el-select v-model="formData.metric_name" placeholder="选择指标" style="width: 100%">
            <el-option v-for="m in metricOptions" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="资产类型">
          <el-select v-model="formData.asset_type" placeholder="全部" clearable style="width: 100%">
            <el-option label="Linux服务器" value="linux_server" />
            <el-option label="Windows服务器" value="windows_server" />
            <el-option label="数据库" value="database" />
            <el-option label="Web服务" value="web_service" />
          </el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="条件" required>
              <el-select v-model="formData.condition" style="width: 100%">
                <el-option label="大于 (>)" value="gt" />
                <el-option label="大于等于 (>=)" value="gte" />
                <el-option label="小于 (<)" value="lt" />
                <el-option label="小于等于 (<=)" value="lte" />
                <el-option label="等于 (=)" value="eq" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="阈值" required>
              <el-input-number v-model="formData.threshold_value" :precision="1" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="持续时间">
          <el-input-number v-model="formData.duration_seconds" :min="0" :step="60" style="width: 100%" />
          <div class="text-tertiary font-12" style="margin-top: 4px">0 表示即时触发</div>
        </el-form-item>
        <el-form-item label="严重级别" required>
          <el-select v-model="formData.severity" style="width: 100%">
            <el-option label="严重" value="critical" />
            <el-option label="高" value="high" />
            <el-option label="警告" value="warning" />
            <el-option label="信息" value="info" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { thresholdService } from '@/shared/api'

const loading = ref(false)
const items = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

const filters = reactive({ metric_name: '', severity: '', asset_type: '', enabled: null as boolean | null })

const metricOptions = ['cpu_usage', 'memory_usage', 'disk_usage', 'disk_io', 'network_in', 'network_out', 'response_time', 'connection_count', 'process_count', 'load_avg']

async function fetchData() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: currentPage.value, page_size: pageSize }
    if (filters.metric_name) params.metric_name = filters.metric_name
    if (filters.severity) params.severity = filters.severity
    if (filters.asset_type) params.asset_type = filters.asset_type
    if (filters.enabled !== null) params.enabled = filters.enabled

    const resp = await thresholdService.list(params)
    if (resp.data?.code === 0) {
      items.value = resp.data.data?.items || []
      total.value = resp.data.data?.total || 0
    }
  } catch (e) {
    console.error('Failed to fetch threshold rules:', e)
  } finally {
    loading.value = false
  }
}

const dialogVisible = ref(false)
const editingRule = ref<any>(null)
const submitting = ref(false)
const formData = reactive({
  name: '', metric_name: '', asset_type: '', condition: 'gt',
  threshold_value: 90, duration_seconds: 0, severity: 'warning', description: '',
})

function openCreateDialog() {
  editingRule.value = null
  Object.assign(formData, { name: '', metric_name: '', asset_type: '', condition: 'gt', threshold_value: 90, duration_seconds: 0, severity: 'warning', description: '' })
  dialogVisible.value = true
}

function openEditDialog(row: any) {
  editingRule.value = row
  Object.assign(formData, { name: row.name, metric_name: row.metric_name, asset_type: row.asset_type || '', condition: row.condition, threshold_value: row.threshold_value, duration_seconds: row.duration_seconds, severity: row.severity, description: row.description || '' })
  dialogVisible.value = true
}

async function submitForm() {
  if (!formData.name || !formData.metric_name) {
    ElMessage.warning('请填写必填项')
    return
  }
  submitting.value = true
  try {
    const data = { ...formData, asset_type: formData.asset_type || null }
    if (editingRule.value) {
      await thresholdService.update(editingRule.value.id, data)
      ElMessage.success('规则已更新')
    } else {
      await thresholdService.create(data)
      ElMessage.success('规则已创建')
    }
    dialogVisible.value = false
    fetchData()
  } catch (e) {
    console.error('Submit failed:', e)
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

async function toggleRule(row: any) {
  try {
    await thresholdService.toggle(row.id)
    fetchData()
  } catch { ElMessage.error('操作失败') }
}

async function deleteRule(row: any) {
  try {
    await thresholdService.delete(row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch { ElMessage.error('删除失败') }
}

function conditionText(c: string) {
  const map: Record<string, string> = { gt: '>', gte: '>=', lt: '<', lte: '<=', eq: '=' }
  return map[c] || c
}

function metricUnit(m: string) {
  if (m.includes('usage') || m.includes('cpu') || m.includes('memory') || m.includes('disk_usage')) return '%'
  if (m.includes('time')) return 'ms'
  return ''
}

function severityText(s: string) {
  const map: Record<string, string> = { critical: '严重', high: '高', warning: '警告', info: '信息' }
  return map[s] || s
}

function severityTag(s: string) {
  const map: Record<string, string> = { critical: 'danger', high: 'warning', warning: '', info: 'info' }
  return map[s] || 'info'
}

onMounted(fetchData)
</script>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.mb-md { margin-bottom: 16px; }
.text-tertiary { color: #86909c; }
.font-12 { font-size: 12px; }
</style>
