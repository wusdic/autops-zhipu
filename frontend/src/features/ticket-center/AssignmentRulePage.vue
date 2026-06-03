<template>
  <div class="assignment-rule-page">
    <!-- 搜索与筛选栏 -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="filterForm" @submit.prevent="handleSearch">
        <el-form-item label="规则名称">
          <el-input
            v-model="filterForm.keyword"
            placeholder="搜索规则名称"
            clearable
            style="width: 200px"
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item label="条件类型">
          <el-select
            v-model="filterForm.condition_type"
            placeholder="全部"
            clearable
            style="width: 140px"
            @change="handleSearch"
          >
            <el-option label="资产类型" value="asset_type" />
            <el-option label="优先级" value="priority" />
            <el-option label="关键词" value="keyword" />
            <el-option label="工单类型" value="ticket_type" />
            <el-option label="来源" value="source" />
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

    <!-- 规则表格 -->
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="title">自动分派规则</span>
          <div class="actions">
            <el-button type="primary" :icon="Plus" @click="handleCreate">新建规则</el-button>
            <el-button :icon="Sort" @click="handleReorder">调整优先级顺序</el-button>
          </div>
        </div>
      </template>

      <el-table v-loading="loading" :data="tableData" border stripe row-key="id">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="name" label="规则名称" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">{{ row.name }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="conditions" label="匹配条件" min-width="220">
          <template #default="{ row }">
            <div class="condition-tags">
              <template v-if="row.conditions?.length">
                <el-tag
                  v-for="(cond, idx) in row.conditions"
                  :key="idx"
                  :type="conditionTypeTagMap[cond.type] || 'info'"
                  size="small"
                  style="margin: 2px 4px 2px 0"
                >
                  {{ conditionTypeLabelMap[cond.type] || cond.type }}:
                  {{ cond.value }}
                </el-tag>
              </template>
              <span v-else class="text-muted">无条件</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="assign_to" label="分配给" min-width="140">
          <template #default="{ row }">
            <template v-if="row.assign_to_type === 'role'">
              <el-tag type="warning" size="small">
                <el-icon><User /></el-icon>
                {{ row.assign_to }}
              </el-tag>
            </template>
            <template v-else-if="row.assign_to_type === 'user'">
              <el-tag type="success" size="small">
                <el-icon><Avatar /></el-icon>
                {{ row.assign_to }}
              </el-tag>
            </template>
            <template v-else>
              <el-tag size="small">{{ row.assign_to }}</el-tag>
            </template>
          </template>
        </el-table-column>
        <el-table-column prop="assign_to_type" label="分配类型" width="100" align="center">
          <template #default="{ row }">
            {{ row.assign_to_type === 'role' ? '角色' : row.assign_to_type === 'user' ? '人员' : row.assign_to_type }}
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="规则优先级" width="100" align="center" sortable>
          <template #default="{ row }">
            <el-badge :value="row.priority" :type="row.priority <= 3 ? 'danger' : row.priority <= 6 ? 'warning' : 'info'" />
          </template>
        </el-table-column>
        <el-table-column prop="match_count" label="匹配次数" width="100" align="center">
          <template #default="{ row }">
            {{ row.match_count ?? 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.status === 'enabled'"
              active-text="启用"
              inactive-text="禁用"
              inline-prompt
              @change="(val: boolean) => handleToggleStatus(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="170" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="info" link size="small" @click="handleDuplicate(row)">复制</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
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
      :title="isEditing ? '编辑分派规则' : '新建分派规则'"
      width="680px"
      destroy-on-close
      @closed="resetDialogForm"
    >
      <el-form
        ref="dialogFormRef"
        :model="dialogForm"
        :rules="dialogRules"
        label-width="110px"
      >
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="dialogForm.name" placeholder="输入规则名称" maxlength="60" show-word-limit />
        </el-form-item>

        <!-- 条件配置 -->
        <el-form-item label="匹配条件" prop="conditions">
          <div class="conditions-editor">
            <div
              v-for="(cond, index) in dialogForm.conditions"
              :key="index"
              class="condition-row"
            >
              <el-select
                v-model="cond.type"
                placeholder="条件类型"
                style="width: 140px"
                @change="() => cond.value = ''"
              >
                <el-option label="资产类型" value="asset_type" />
                <el-option label="优先级" value="priority" />
                <el-option label="关键词" value="keyword" />
                <el-option label="工单类型" value="ticket_type" />
                <el-option label="来源" value="source" />
              </el-select>

              <el-select
                v-if="cond.type === 'asset_type'"
                v-model="cond.value"
                placeholder="选择资产类型"
                style="width: 160px"
              >
                <el-option label="服务器" value="server" />
                <el-option label="网络设备" value="network" />
                <el-option label="安全设备" value="security" />
                <el-option label="数据库" value="database" />
                <el-option label="中间件" value="middleware" />
              </el-select>
              <el-select
                v-else-if="cond.type === 'priority'"
                v-model="cond.value"
                placeholder="选择优先级"
                style="width: 160px"
              >
                <el-option label="紧急" value="critical" />
                <el-option label="高" value="high" />
                <el-option label="中" value="medium" />
                <el-option label="低" value="low" />
              </el-select>
              <el-select
                v-else-if="cond.type === 'ticket_type'"
                v-model="cond.value"
                placeholder="选择工单类型"
                style="width: 160px"
              >
                <el-option label="事件" value="incident" />
                <el-option label="问题" value="problem" />
                <el-option label="变更" value="change" />
                <el-option label="服务请求" value="request" />
                <el-option label="安全事件" value="security" />
              </el-select>
              <el-input
                v-else
                v-model="cond.value"
                placeholder="输入匹配值"
                style="width: 160px"
              />

              <el-button
                type="danger"
                :icon="Delete"
                circle
                size="small"
                @click="removeCondition(index)"
              />
            </div>

            <el-button :icon="Plus" size="small" @click="addCondition">添加条件</el-button>
            <div class="condition-tip">
              多个条件之间为 AND 关系，全部满足时触发规则
            </div>
          </div>
        </el-form-item>

        <!-- 分配目标 -->
        <el-form-item label="分配类型" prop="assign_to_type">
          <el-radio-group v-model="dialogForm.assign_to_type">
            <el-radio value="role">角色</el-radio>
            <el-radio value="user">指定人员</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="分配给" prop="assign_to">
          <el-select
            v-if="dialogForm.assign_to_type === 'role'"
            v-model="dialogForm.assign_to"
            placeholder="选择角色"
            style="width: 100%"
            filterable
          >
            <el-option label="运维工程师" value="ops_engineer" />
            <el-option label="安全工程师" value="security_engineer" />
            <el-option label="网络工程师" value="network_engineer" />
            <el-option label="DBA" value="dba" />
            <el-option label="系统管理员" value="sysadmin" />
            <el-option label="值班人员" value="oncall" />
          </el-select>
          <el-select
            v-else
            v-model="dialogForm.assign_to"
            placeholder="选择人员"
            style="width: 100%"
            filterable
            remote
            :remote-method="searchUsers"
            :loading="userSearchLoading"
          >
            <el-option
              v-for="u in userOptions"
              :key="u.id"
              :label="u.display_name || u.username"
              :value="u.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="规则优先级" prop="priority">
          <el-input-number
            v-model="dialogForm.priority"
            :min="1"
            :max="100"
            controls-position="right"
            style="width: 160px"
          />
          <span class="priority-hint">数值越小优先级越高，优先匹配</span>
        </el-form-item>

        <el-form-item label="描述">
          <el-input
            v-model="dialogForm.description"
            type="textarea"
            :rows="2"
            placeholder="规则描述（可选）"
            maxlength="200"
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
          {{ isEditing ? '保存修改' : '创建规则' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 优先级排序弹窗 -->
    <el-dialog v-model="reorderVisible" title="调整规则优先级顺序" width="500px" destroy-on-close>
      <p class="reorder-tip">拖拽调整规则执行优先级，排在前面的规则优先匹配</p>
      <draggable-container v-model="reorderList" item-key="id" handle=".drag-handle">
        <template #item="{ element }">
          <div class="reorder-item">
            <el-icon class="drag-handle"><Rank /></el-icon>
            <span class="reorder-name">{{ element.name }}</span>
            <el-tag size="small" :type="element.status === 'enabled' ? 'success' : 'info'">
              {{ element.status === 'enabled' ? '启用' : '禁用' }}
            </el-tag>
          </div>
        </template>
      </draggable-container>
      <template #footer>
        <el-button @click="reorderVisible = false">取消</el-button>
        <el-button type="primary" :loading="reorderLoading" @click="handleSaveReorder">保存顺序</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Search, Refresh, Plus, Delete, Sort, User, Avatar, Rank } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

// ─── 类型定义 ────────────────────────────────────────
interface Condition {
  type: string
  value: string
}

interface AssignmentRule {
  id: number | string
  name: string
  conditions: Condition[]
  assign_to: string
  assign_to_type: 'role' | 'user'
  priority: number
  status: 'enabled' | 'disabled'
  match_count?: number
  description?: string
  updated_at?: string
  [key: string]: unknown
}

interface DialogFormData {
  id?: number | string
  name: string
  conditions: Condition[]
  assign_to: string
  assign_to_type: 'role' | 'user'
  priority: number
  status: 'enabled' | 'disabled'
  description: string
}

// ─── 映射表 ──────────────────────────────────────────
const conditionTypeLabelMap: Record<string, string> = {
  asset_type: '资产类型',
  priority: '优先级',
  keyword: '关键词',
  ticket_type: '工单类型',
  source: '来源',
}

const conditionTypeTagMap: Record<string, string> = {
  asset_type: '',
  priority: 'danger',
  keyword: 'warning',
  ticket_type: 'success',
  source: 'info',
}

// ─── 响应式状态 ──────────────────────────────────────
const loading = ref(false)
const tableData = ref<AssignmentRule[]>([])

const filterForm = reactive({
  keyword: '',
  condition_type: '',
  status: '',
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

const userSearchLoading = ref(false)
const userOptions = ref<{ id: number | string; username: string; display_name?: string }[]>([])

const reorderVisible = ref(false)
const reorderLoading = ref(false)
const reorderList = ref<AssignmentRule[]>([])

const defaultDialogForm = (): DialogFormData => ({
  name: '',
  conditions: [{ type: '', value: '' }],
  assign_to: '',
  assign_to_type: 'role',
  priority: 10,
  status: 'enabled',
  description: '',
})

const dialogForm = reactive<DialogFormData>(defaultDialogForm())

const dialogRules = reactive<FormRules<DialogFormData>>({
  name: [
    { required: true, message: '请输入规则名称', trigger: 'blur' },
    { max: 60, message: '规则名称不超过 60 个字符', trigger: 'blur' },
  ],
  assign_to: [{ required: true, message: '请选择分配目标', trigger: 'change' }],
  assign_to_type: [{ required: true, message: '请选择分配类型', trigger: 'change' }],
  priority: [{ required: true, message: '请设置优先级', trigger: 'blur' }],
})

// ─── 数据获取 ────────────────────────────────────────
const ruleApiUrl = API.TICKETS + '/assignment-rules'

async function fetchData() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: pagination.page,
      page_size: pagination.page_size,
    }
    if (filterForm.keyword) params.keyword = filterForm.keyword
    if (filterForm.condition_type) params.condition_type = filterForm.condition_type
    if (filterForm.status) params.status = filterForm.status

    const res = await client.get(ruleApiUrl, { params })
    const data = res.data?.data ?? res.data
    if (Array.isArray(data)) {
      tableData.value = data
      pagination.total = data.length
    } else {
      tableData.value = data?.items ?? data?.results ?? data?.list ?? []
      pagination.total = data?.total ?? tableData.value.length
    }
  } catch {
    tableData.value = []
    pagination.total = 0
    ElMessage.warning('暂无派单规则数据，请检查后端工单服务是否已启动')
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
  filterForm.condition_type = ''
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

// ─── 条件编辑器 ──────────────────────────────────────
function addCondition() {
  dialogForm.conditions.push({ type: '', value: '' })
}

function removeCondition(index: number) {
  dialogForm.conditions.splice(index, 1)
  if (!dialogForm.conditions.length) {
    dialogForm.conditions.push({ type: '', value: '' })
  }
}

// ─── 用户搜索 ────────────────────────────────────────
async function searchUsers(query: string) {
  if (!query) return
  userSearchLoading.value = true
  try {
    const res = await client.get(API.USERS ?? '/api/users', { params: { keyword: query, page_size: 20 } })
    const data = res.data?.data ?? res.data
    userOptions.value = Array.isArray(data) ? data : data?.items ?? []
  } catch {
    userOptions.value = []
  } finally {
    userSearchLoading.value = false
  }
}

// ─── 新建/编辑 ──────────────────────────────────────
function handleCreate() {
  isEditing.value = false
  Object.assign(dialogForm, defaultDialogForm())
  dialogVisible.value = true
}

function handleEdit(row: AssignmentRule) {
  isEditing.value = true
  Object.assign(dialogForm, {
    id: row.id,
    name: row.name,
    conditions: row.conditions?.length ? row.conditions.map(c => ({ ...c })) : [{ type: '', value: '' }],
    assign_to: row.assign_to,
    assign_to_type: row.assign_to_type,
    priority: row.priority,
    status: row.status,
    description: row.description || '',
  })
  dialogVisible.value = true
}

async function handleDialogSubmit() {
  const valid = await dialogFormRef.value?.validate().catch(() => false)
  if (!valid) return

  // Validate conditions
  const validConditions = dialogForm.conditions.filter(c => c.type && c.value)
  if (!validConditions.length) {
    ElMessage.warning('请至少设置一个有效的匹配条件')
    return
  }

  dialogLoading.value = true
  try {
    const payload = {
      ...dialogForm,
      conditions: validConditions,
    }
    if (isEditing.value) {
      await client.put(ruleApiUrl + '/' + dialogForm.id, payload)
      ElMessage.success('规则更新成功')
    } else {
      await client.post(ruleApiUrl, payload)
      ElMessage.success('规则创建成功')
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

// ─── 复制规则 ────────────────────────────────────────
async function handleDuplicate(row: AssignmentRule) {
  try {
    await client.post(ruleApiUrl, {
      ...row,
      id: undefined,
      name: row.name + ' (副本)',
      match_count: 0,
    })
    ElMessage.success('规则复制成功')
    fetchData()
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '复制失败'
    ElMessage.error(msg)
  }
}

// ─── 状态切换 ────────────────────────────────────────
async function handleToggleStatus(row: AssignmentRule, enabled: boolean) {
  const newStatus = enabled ? 'enabled' : 'disabled'
  try {
    await client.patch(ruleApiUrl + '/' + row.id, { status: newStatus })
    row.status = newStatus
    ElMessage.success(enabled ? '已启用' : '已禁用')
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '状态切换失败'
    ElMessage.error(msg)
  }
}

// ─── 删除 ────────────────────────────────────────────
async function handleDelete(row: AssignmentRule) {
  try {
    await ElMessageBox.confirm(
      '确定删除规则「' + row.name + '」？此操作不可撤销。',
      '删除确认',
      { type: 'warning' }
    )
    await client.delete(ruleApiUrl + '/' + row.id)
    ElMessage.success('规则已删除')
    fetchData()
  } catch (err: unknown) {
    if (err !== 'cancel') {
      const msg = err instanceof Error ? err.message : '删除失败'
      ElMessage.error(msg)
    }
  }
}

// ─── 优先级排序 ──────────────────────────────────────
function handleReorder() {
  reorderList.value = tableData.value.map(r => ({ ...r }))
  reorderVisible.value = true
}

async function handleSaveReorder() {
  reorderLoading.value = true
  try {
    const orders = reorderList.value.map((r, idx) => ({ id: r.id, priority: idx + 1 }))
    await client.put(ruleApiUrl + '/reorder', { orders })
    ElMessage.success('优先级顺序已更新')
    reorderVisible.value = false
    fetchData()
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '更新顺序失败'
    ElMessage.error(msg)
  } finally {
    reorderLoading.value = false
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
.assignment-rule-page {
  padding: 20px;
}

.filter-card {
  margin-bottom: 16px;
}

.filter-card :deep(.el-card__body) {
  padding-bottom: 2px;
}

.table-card .card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.table-card .card-header .title {
  font-size: 16px;
  font-weight: 600;
}

.table-card .card-header .actions {
  display: flex;
  gap: 8px;
}

.condition-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
}

.text-muted {
  color: #c0c4cc;
}

.conditions-editor {
  width: 100%;
}

.condition-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.condition-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.priority-hint {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}

.reorder-tip {
  font-size: 13px;
  color: #909399;
  margin-bottom: 12px;
}

.reorder-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 6px;
  background: #fff;
  cursor: move;
}

.reorder-item .drag-handle {
  cursor: grab;
  color: #c0c4cc;
}

.reorder-item .reorder-name {
  flex: 1;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding: 4px 0;
}
</style>
