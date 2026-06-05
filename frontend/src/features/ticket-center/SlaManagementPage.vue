<template>
  <div class="autops-page-container">
    <!-- 页面头部 -->
    <div class="autops-page-header">
      <div class="autops-page-title">SLA 管理</div>
      <div class="autops-page-desc">配置工单服务级别协议</div>
    </div>

    <!-- 搜索与操作栏 -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="filterForm" @submit.prevent="handleSearch">
        <el-form-item label="策略名称">
          <el-input
            v-model="filterForm.keyword"
            placeholder="搜索策略名称"
            clearable
            style="width: 200px"
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item label="工单类型">
          <el-select
            v-model="filterForm.ticket_type"
            placeholder="全部类型"
            clearable
            style="width: 150px"
            @change="handleSearch"
          >
            <el-option label="事件" value="incident" />
            <el-option label="问题" value="problem" />
            <el-option label="变更" value="change" />
            <el-option label="服务请求" value="request" />
            <el-option label="安全事件" value="security" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="filterForm.status"
            placeholder="全部"
            clearable
            style="width: 120px"
            @change="handleSearch"
          >
            <el-option label="已启用" value="enabled" />
            <el-option label="已禁用" value="disabled" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- SLA 策略表格 -->
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="autops-card-header">
          <span class="title">SLA 策略管理</span>
          <el-button type="primary" :icon="Plus" @click="handleCreate">新建策略</el-button>
        </div>
      </template>

      <el-table stripe v-loading="loading" :data="tableData" border>
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column prop="name" label="策略名称" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <el-button type="primary" plain @click="handleEdit(row)">{{ row.name }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="ticket_type" label="工单类型" min-width="110">
          <template #default="{ row }">
            <el-tag :type="(ticketTypeTagMap[row.ticket_type] || 'info') as TagType" size="small">
              {{ ticketTypeLabelMap[row.ticket_type] || row.ticket_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="response_hours" label="响应时间(h)" width="120" align="center">
          <template #default="{ row }">
            <span class="time-cell">{{ row.response_hours }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="resolve_hours" label="解决时间(h)" width="120" align="center">
          <template #default="{ row }">
            <span class="time-cell">{{ row.resolve_hours }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="priority_scope" label="优先级范围" min-width="140">
          <template #default="{ row }">
            <template v-if="row.priority_scope?.length">
              <el-tag
                v-for="p in row.priority_scope"
                :key="p"
                :type="(priorityTagMap[p]) as TagType"
                size="small"
                style="margin-right: 4px"
              >
                {{ priorityLabelMap[p] || p }}
              </el-tag>
            </template>
            <span v-else>全部</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.description || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.status === 'enabled'"
              active-text="启用"
              inactive-text="禁用"
              inline-prompt
              @change="(val: string | number | boolean) => handleToggleStatus(row, val as boolean)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" plain size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" plain size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑 SLA 策略' : '新建 SLA 策略'"
      width="600px"
      destroy-on-close
      @closed="resetDialogForm"
    >
      <el-form
        ref="dialogFormRef"
        :model="dialogForm"
        :rules="dialogRules"
        label-width="120px"
      >
        <el-form-item label="策略名称" prop="name">
          <el-input v-model="dialogForm.name" placeholder="输入策略名称" maxlength="60" show-word-limit />
        </el-form-item>

        <el-form-item label="工单类型" prop="ticket_type">
          <el-select v-model="dialogForm.ticket_type" placeholder="选择工单类型" style="width: 100%">
            <el-option
              v-for="(label, value) in ticketTypeLabelMap"
              :key="value"
              :label="label"
              :value="value"
            />
          </el-select>
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="响应时间" prop="response_hours">
              <el-input-number
                v-model="dialogForm.response_hours"
                :min="0"
                :max="9999"
                :step="1"
                controls-position="right"
                style="width: 100%"
              />
              <div class="form-item-tip">单位：小时</div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="解决时间" prop="resolve_hours">
              <el-input-number
                v-model="dialogForm.resolve_hours"
                :min="0"
                :max="9999"
                :step="1"
                controls-position="right"
                style="width: 100%"
              />
              <div class="form-item-tip">单位：小时</div>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="优先级范围" prop="priority_scope">
          <el-checkbox-group v-model="dialogForm.priority_scope">
            <el-checkbox label="critical">紧急</el-checkbox>
            <el-checkbox label="high">高</el-checkbox>
            <el-checkbox label="medium">中</el-checkbox>
            <el-checkbox label="low">低</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="工作时间" prop="work_hours_only">
          <el-switch
            v-model="dialogForm.work_hours_only"
            active-text="仅计算工作时间"
            inactive-text="全天计算"
          />
        </el-form-item>

        <el-form-item label="通知设置">
          <el-checkbox-group v-model="dialogForm.notify_on">
            <el-checkbox label="approaching">即将到期提醒</el-checkbox>
            <el-checkbox label="breached">已超时通知</el-checkbox>
            <el-checkbox label="escalate">自动升级</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="升级策略" v-if="dialogForm.notify_on.includes('escalate')">
          <el-row :gutter="8" align="middle">
            <el-col :span="12">
              <el-select v-model="dialogForm.escalate_to" placeholder="升级给" style="width: 100%">
                <el-option label="上级主管" value="supervisor" />
                <el-option label="部门负责人" value="department_head" />
                <el-option label="管理员" value="admin" />
              </el-select>
            </el-col>
            <el-col :span="12">
              <el-input-number
                v-model="dialogForm.escalate_after_hours"
                :min="1"
                :max="999"
                controls-position="right"
                style="width: 100%"
              />
              <div class="form-item-tip">超时 N 小时后升级</div>
            </el-col>
          </el-row>
        </el-form-item>

        <el-form-item label="描述">
          <el-input
            v-model="dialogForm.description"
            type="textarea"
            :rows="3"
            placeholder="策略描述（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="状态">
          <el-radio-group v-model="dialogForm.status">
            <el-radio value="enabled">启用</el-radio>
            <el-radio value="disabled">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="handleDialogSubmit">
          {{ isEditing ? '保存修改' : '创建策略' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

// ─── 类型定义 ────────────────────────────────────────
interface SlaPolicy {
  id: number | string
  name: string
  ticket_type: string
  response_hours: number
  resolve_hours: number
  priority_scope: string[]
  status: 'enabled' | 'disabled'
  description?: string
  work_hours_only?: boolean
  notify_on?: string[]
  escalate_to?: string
  escalate_after_hours?: number
  updated_at?: string
  created_at?: string
  [key: string]: unknown
}

interface DialogFormData {
  id?: number | string
  name: string
  ticket_type: string
  response_hours: number
  resolve_hours: number
  priority_scope: string[]
  status: 'enabled' | 'disabled'
  description: string
  work_hours_only: boolean
  notify_on: string[]
  escalate_to: string
  escalate_after_hours: number
}

// ─── 映射表 ──────────────────────────────────────────
const ticketTypeLabelMap: Record<string, string> = {
  incident: '事件',
  problem: '问题',
  change: '变更',
  request: '服务请求',
  security: '安全事件',
}

const ticketTypeTagMap: Record<string, TagType> = {
  incident: 'danger',
  problem: 'warning',
  change: 'primary',
  request: 'success',
  security: 'danger',
}

const priorityLabelMap: Record<string, string> = {
  critical: '紧急',
  high: '高',
  medium: '中',
  low: '低',
}

const priorityTagMap: Record<string, TagType> = {
  critical: 'danger',
  high: 'warning',
  medium: 'primary',
  low: 'info',
}

// ─── 响应式状态 ──────────────────────────────────────
const loading = ref(false)
const tableData = ref<SlaPolicy[]>([])

const filterForm = reactive({
  keyword: 'primary',
  ticket_type: 'primary',
  status: 'primary',
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

// ─── 弹窗状态 ────────────────────────────────────────
const dialogVisible = ref(false)
const dialogLoading = ref(false)
const isEditing = ref(false)
const dialogFormRef = ref<FormInstance>()

const defaultDialogForm = (): DialogFormData => ({
  name: 'primary',
  ticket_type: 'primary',
  response_hours: 4,
  resolve_hours: 24,
  priority_scope: ['critical', 'high', 'medium', 'low'],
  status: 'enabled',
  description: 'primary',
  work_hours_only: false,
  notify_on: ['approaching', 'breached'],
  escalate_to: 'supervisor',
  escalate_after_hours: 2,
})

const dialogForm = reactive<DialogFormData>(defaultDialogForm())

const dialogRules = reactive<FormRules<DialogFormData>>({
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' },
    { max: 60, message: '策略名称不超过 60 个字符', trigger: 'blur' },
  ],
  ticket_type: [{ required: true, message: '请选择工单类型', trigger: 'change' }],
  response_hours: [{ required: true, message: '请输入响应时间', trigger: 'blur' }],
  resolve_hours: [{ required: true, message: '请输入解决时间', trigger: 'blur' }],
  priority_scope: [
    {
      type: 'array',
      required: true,
      message: '请至少选择一个优先级',
      trigger: 'change',
    },
  ],
})

// ─── 数据获取 ────────────────────────────────────────
const slaApiUrl = API.TICKETS + '/sla-policies'

async function fetchData() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: pagination.page,
      page_size: pagination.page_size,
    }
    if (filterForm.keyword) params.keyword = filterForm.keyword
    if (filterForm.ticket_type) params.ticket_type = filterForm.ticket_type
    if (filterForm.status) params.status = filterForm.status

    let res
    try {
      res = await client.get(slaApiUrl, { params })
    } catch {
      // Fallback: try ticket stats endpoint and derive SLA data
      res = await client.get(API.TICKET_STATS ?? API.TICKETS + '/stats', { params })
    }

    const data = res.data?.data ?? res.data
    if (Array.isArray(data)) {
      tableData.value = data
      pagination.total = data.length
    } else {
      tableData.value = data?.items ?? data?.results ?? data?.list ?? []
      pagination.total = data?.total ?? tableData.value.length
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '获取 SLA 策略失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

// ─── 搜索 ────────────────────────────────────────────
function handleSearch() {
  pagination.page = 1
  fetchData()
}

function handleReset() {
  filterForm.keyword = ''
  filterForm.ticket_type = ''
  filterForm.status = ''
  pagination.page = 1
  fetchData()
}

// ─── 分页 ────────────────────────────────────────────
function handleSizeChange(size: number) {
  pagination.page_size = size
  pagination.page = 1
  fetchData()
}

function handlePageChange(page: number) {
  pagination.page = page
  fetchData()
}

// ─── 新建/编辑 ──────────────────────────────────────
function handleCreate() {
  isEditing.value = false
  Object.assign(dialogForm, defaultDialogForm())
  dialogVisible.value = true
}

function handleEdit(row: any) {
  isEditing.value = true
  Object.assign(dialogForm, {
    id: row.id,
    name: row.name,
    ticket_type: row.ticket_type,
    response_hours: row.response_hours,
    resolve_hours: row.resolve_hours,
    priority_scope: row.priority_scope?.length ? [...row.priority_scope] : ['critical', 'high', 'medium', 'low'],
    status: row.status,
    description: row.description || '',
    work_hours_only: row.work_hours_only ?? false,
    notify_on: row.notify_on ?? ['approaching', 'breached'],
    escalate_to: row.escalate_to || 'supervisor',
    escalate_after_hours: row.escalate_after_hours || 2,
  })
  dialogVisible.value = true
}

async function handleDialogSubmit() {
  const valid = await dialogFormRef.value?.validate().catch(() => false)
  if (!valid) return

  dialogLoading.value = true
  try {
    const payload = { ...dialogForm }
    if (isEditing.value) {
      await client.put(slaApiUrl + '/' + dialogForm.id, payload)
      ElMessage.success('策略更新成功')
    } else {
      await client.post(slaApiUrl, payload)
      ElMessage.success('策略创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '操作失败'
    ElMessage.error(msg)
  } finally {
    dialogLoading.value = false
  }
}

function resetDialogForm() {
  dialogFormRef.value?.resetFields()
  Object.assign(dialogForm, defaultDialogForm())
}

// ─── 状态切换 ────────────────────────────────────────
async function handleToggleStatus(row: any, enabled: boolean) {
  const newStatus = enabled ? 'enabled' : 'disabled'
  try {
    await client.patch(slaApiUrl + '/' + row.id, { status: newStatus })
    row.status = newStatus
    ElMessage.success(enabled ? '已启用' : '已禁用')
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '状态切换失败'
    ElMessage.error(msg)
  }
}

// ─── 删除 ────────────────────────────────────────────
async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(
      '确定删除策略「' + row.name + '」？此操作不可撤销。',
      '删除确认',
      { type: 'warning' }
    )
    await client.delete(slaApiUrl + '/' + row.id)
    ElMessage.success('策略已删除')
    fetchData()
  } catch (err: unknown) {
    if (err !== 'cancel') {
      const msg = err instanceof Error ? err.message : '删除失败'
      ElMessage.error(msg)
    }
  }
}

// ─── 工具函数 ────────────────────────────────────────
function formatTime(time: string | undefined): string {
  if (!time) return '-'
  try {
    return new Date(time).toLocaleString('zh-CN', { hour12: false })
  } catch {
    return time
  }
}

// ─── 初始化 ──────────────────────────────────────────
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.sla-management-page {
  padding: var(--autops-space-xl);
}

.filter-card {
  margin-bottom: var(--autops-space-lg);
}

.filter-card :deep(.el-card__body) {
  padding-bottom: 2px;
}

.table-card 
.time-cell {
  font-family: monospace;
  font-weight: 600;
}

.form-item-tip {
  font-size: var(--autops-font-12);
  color: var(--autops-info);
  line-height: 1.2;
  margin-top: 2px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--autops-space-lg);
  padding: var(--autops-space-xs) 0;
}
</style>
