<template>
  <div class="autops-page-container">
    <PageHeader title="通知规则" desc="配置告警和事件的通知规则和发送渠道">
      <template #actions>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon> 新建规则
        </el-button>
      </template>
    </PageHeader>

    <!-- Filters -->
    <el-card class="mb-md">
      <el-row :gutter="16">
        <el-col :span="8">
          <el-select v-model="filters.event_type" placeholder="事件类型" clearable @change="fetchData">
            <el-option v-for="e in eventTypes" :key="e" :label="e" :value="e" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-select v-model="filters.target_type" placeholder="目标类型" clearable @change="fetchData">
            <el-option label="用户" value="user" />
            <el-option label="角色" value="role" />
            <el-option label="渠道" value="channel" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-select v-model="filters.enabled" placeholder="状态" clearable @change="fetchData">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <!-- Table -->
    <el-card v-loading="loading">
      <el-table stripe :data="items"empty-text="暂无通知规则" style="width: 100%">
        <el-table-column prop="name" label="规则名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="event_type" label="事件类型" width="180" show-overflow-tooltip />
        <el-table-column prop="target_type" label="目标类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.target_type === 'user' ? undefined : row.target_type === 'role' ? 'warning' : 'info'">
              {{ targetText(row.target_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="通知渠道" width="200">
          <template #default="{ row }">
            <template v-if="row.channels">
              <el-tag v-for="ch in parseJSON(row.channels)" :key="ch" size="small" type="info" style="margin: 2px">{{ ch }}</el-tag>
            </template>
          </template>
        </el-table-column>
        <el-table-column prop="severity_filter" label="严重级别过滤" width="140">
          <template #default="{ row }">{{ row.severity_filter || '全部' }}</template>
        </el-table-column>
        <el-table-column label="静默时段" width="140">
          <template #default="{ row }">
            {{ row.quiet_hours_start && row.quiet_hours_end ? row.quiet_hours_start + '-' + row.quiet_hours_end : '无' }}
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="状态" width="80">
          <template #default="{ row }">
            <el-switch :model-value="row.enabled" @change="toggleRule(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button plain type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-popconfirm title="确定删除此规则？" @confirm="deleteRule(row)">
              <template #reference>
                <el-button plain type="danger" size="small">删除</el-button>
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
    <el-dialog v-model="dialogVisible" :title="editingRule ? '编辑规则' : '新建规则'" width="600px" destroy-on-close>
      <el-form :model="formData" label-width="100px">
        <el-form-item label="规则名称" required>
          <el-input v-model="formData.name" placeholder="如：严重告警通知" />
        </el-form-item>
        <el-form-item label="事件类型" required>
          <el-select v-model="formData.event_type" placeholder="选择事件类型" style="width: 100%" filterable>
            <el-option v-for="e in eventTypes" :key="e" :label="e" :value="e" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标类型" required>
          <el-radio-group v-model="formData.target_type">
            <el-radio value="user">用户</el-radio>
            <el-radio value="role">角色</el-radio>
            <el-radio value="channel">渠道</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="目标ID" required>
          <el-input v-model="formData.target_ids" placeholder='如：["user-id-1","user-id-2"]' />
        </el-form-item>
        <el-form-item label="通知渠道" required>
          <el-checkbox-group v-model="selectedChannels">
            <el-checkbox value="in_app">站内</el-checkbox>
            <el-checkbox value="email">邮件</el-checkbox>
            <el-checkbox value="sms">短信</el-checkbox>
            <el-checkbox value="webhook">Webhook</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="严重级别过滤">
          <el-input v-model="formData.severity_filter" placeholder='如：["critical","high"] 留空=全部' />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="静默开始">
              <el-time-select v-model="formData.quiet_hours_start" start="00:00" step="00:30" end="23:30" placeholder="开始时间" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="静默结束">
              <el-time-select v-model="formData.quiet_hours_end" start="00:00" step="00:30" end="23:30" placeholder="结束时间" />
            </el-form-item>
          </el-col>
        </el-row>
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
import PageHeader from '@/shared/components/PageHeader.vue'
import { notificationRuleService } from '@/shared/api'

const loading = ref(false)
const items = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

const filters = reactive({ event_type: '', target_type: '', enabled: null as boolean | null })

const eventTypes = [
  'alert.created', 'alert.escalated', 'alert.resolved',
  'execution.completed', 'execution.failed', 'execution.approval_required',
  'ticket.created', 'ticket.assigned', 'ticket.closed',
  'anomaly.detected', 'inspection.completed', 'inspection.failed',
  'discovery.completed', 'knowledge.created',
]

async function fetchData() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: currentPage.value, page_size: pageSize }
    if (filters.event_type) params.event_type = filters.event_type
    if (filters.target_type) params.target_type = filters.target_type
    if (filters.enabled !== null) params.enabled = filters.enabled

    const resp = await notificationRuleService.list(params)
    if (resp.data?.code === 0) {
      items.value = resp.data.data?.items || []
      total.value = resp.data.data?.total || 0
    }
  } catch (e) {
    console.error('Failed to fetch notification rules:', e)
  } finally {
    loading.value = false
  }
}

const dialogVisible = ref(false)
const editingRule = ref<any>(null)
const submitting = ref(false)
const selectedChannels = ref<string[]>(['in_app'])
const formData = reactive({
  name: '', event_type: '', target_type: 'user', target_ids: '[]',
  channels: '["in_app"]', severity_filter: '', quiet_hours_start: '', quiet_hours_end: '', description: '',
})

function openCreateDialog() {
  editingRule.value = null
  Object.assign(formData, { name: '', event_type: '', target_type: 'user', target_ids: '[]', channels: '["in_app"]', severity_filter: '', quiet_hours_start: '', quiet_hours_end: '', description: ''})
  selectedChannels.value = ['in_app']
  dialogVisible.value = true
}

function openEditDialog(row: any) {
  editingRule.value = row
  Object.assign(formData, { name: row.name, event_type: row.event_type, target_type: row.target_type, target_ids: row.target_ids, channels: row.channels, severity_filter: row.severity_filter || '', quiet_hours_start: row.quiet_hours_start || '', quiet_hours_end: row.quiet_hours_end || '', description: row.description || '' })
  selectedChannels.value = parseJSON(row.channels)
  dialogVisible.value = true
}

async function submitForm() {
  if (!formData.name || !formData.event_type) {
    ElMessage.warning('请填写必填项')
    return
  }
  submitting.value = true
  try {
    const data = { ...formData, channels: JSON.stringify(selectedChannels.value) }
    if (editingRule.value) {
      await notificationRuleService.update(editingRule.value.id, data)
      ElMessage.success('规则已更新')
    } else {
      await notificationRuleService.create(data)
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
    await notificationRuleService.toggle(row.id)
    fetchData()
  } catch { ElMessage.error('操作失败') }
}

async function deleteRule(row: any) {
  try {
    await notificationRuleService.delete(row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch { ElMessage.error('删除失败') }
}

function targetText(t: string) {
  const map: Record<string, string> = { user: '用户', role: '角色', channel: '渠道' }
  return map[t] || t
}

function parseJSON(s: string): string[] {
  try { return JSON.parse(s) } catch { return [] }
}

onMounted(fetchData)
</script>

<style scoped>

.mb-md { margin-bottom: var(--autops-space-lg); }
</style>
