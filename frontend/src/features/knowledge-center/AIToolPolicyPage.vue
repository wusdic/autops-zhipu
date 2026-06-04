<template>
  <div class="ai-tool-policy-page">
    <!-- Page Header -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">
          <el-icon style="margin-right: 6px"><SetUp /></el-icon>
          AI 工具调用策略
        </div>
        <div class="autops-page-desc">管理 AI Agent 可调用的工具及其审批策略</div>
      </div>
      <div class="top-actions">
        <el-button type="primary" :icon="Plus" @click="openCreate">新增策略</el-button>
      </div>
    </div>

    <!-- Search -->
    <div class="autops-card filter-card">
      <el-row :gutter="16" align="middle">
        <el-col :span="8">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索工具名称..."
            :prefix-icon="Search"
            clearable
            @clear="loadList"
            @keyup.enter="loadList"
          />
        </el-col>
        <el-col :span="5">
          <el-select v-model="filterRisk" placeholder="风险等级" clearable @change="loadList" style="width: 100%">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterApproval" placeholder="审批状态" clearable @change="loadList" style="width: 100%">
            <el-option label="需要审批" :value="true" />
            <el-option label="无需审批" :value="false" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="loadList">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-col>
      </el-row>
    </div>

    <!-- Policy Table -->
    <div class="autops-card" style="margin-top: 16px">
      <el-table stripe
 v-loading="loading"
 :data="tableData"style="width: 100%"
 >
        <el-table-column prop="tool_name" label="工具名" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="tool-name">
              <el-icon style="margin-right: 6px" :size="16"><Monitor /></el-icon>
              <span>{{ row.tool_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ row.description || '-' }}</template>
        </el-table-column>
        <el-table-column label="允许范围" width="200">
          <template #default="{ row }">
            <div class="scope-tags">
              <el-tag
                v-for="scope in (row.allowed_scope || []).slice(0, 3)"
                :key="scope"
                size="small"
                type="info"
                style="margin: 2px"
              >
                {{ scope }}
              </el-tag>
              <el-tag v-if="(row.allowed_scope || []).length > 3" size="small" style="margin: 2px">
                +{{ row.allowed_scope.length - 3 }}
              </el-tag>
              <span v-if="!row.allowed_scope || row.allowed_scope.length === 0" class="text-muted">-</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="风险等级" width="110">
          <template #default="{ row }">
            <el-tag :type="riskTagType(row.risk_level)" size="small" effect="dark">
              {{ riskLabel(row.risk_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="需要审批" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.requires_approval"
              @change="toggleApproval(row)"
              :loading="row._toggling"
            />
          </template>
        </el-table-column>
        <el-table-column prop="max_calls_per_minute" label="频率限制" width="110" align="center">
          <template #default="{ row }">
            {{ row.max_calls_per_minute ? `${row.max_calls_per_minute}/min` : '无限制' }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="170">
          <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button plain type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button plain type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadList"
          @current-change="loadList"
        />
      </div>
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑策略' : '新增策略'"
      width="600px"
      destroy-on-close
      @close="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="工具名" prop="tool_name">
          <el-input v-model="form.tool_name" placeholder="例如: restart_service" :disabled="isEditing" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="工具用途说明" />
        </el-form-item>
        <el-form-item label="允许范围" prop="allowed_scope">
          <el-select
            v-model="form.allowed_scope"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入范围标签"
            style="width: 100%"
          >
            <el-option label="production" value="production" />
            <el-option label="staging" value="staging" />
            <el-option label="development" value="development" />
            <el-option label="database" value="database" />
            <el-option label="network" value="network" />
          </el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="风险等级" prop="risk_level">
              <el-select v-model="form.risk_level" style="width: 100%">
                <el-option label="高" value="high" />
                <el-option label="中" value="medium" />
                <el-option label="低" value="low" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="频率限制">
              <el-input-number
                v-model="form.max_calls_per_minute"
                :min="0"
                :max="1000"
                placeholder="0 = 无限制"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="需要审批">
          <el-switch v-model="form.requires_approval" />
        </el-form-item>
        <el-form-item label="审批人" v-if="form.requires_approval">
          <el-select
            v-model="form.approvers"
            multiple
            filterable
            allow-create
            placeholder="输入审批人"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus, Search, SetUp, Monitor } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

// ─── Constants ───────────────────────────────────────────────────────
const TOOL_POLICY_API = '/api/v1/aiops/tool-policies'

// ─── State ───────────────────────────────────────────────────────────
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref('')

const searchKeyword = ref('')
const filterRisk = ref('')
const filterApproval = ref<boolean | string>('')

const tableData = ref<any[]>([])

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const formRef = ref<FormInstance>()

const form = reactive({
  tool_name: '',
  description: '',
  allowed_scope: [] as string[],
  risk_level: 'medium',
  requires_approval: false,
  max_calls_per_minute: 0,
  approvers: [] as string[],
})

const formRules: FormRules = {
  tool_name: [{ required: true, message: '请输入工具名', trigger: 'blur' }],
  risk_level: [{ required: true, message: '请选择风险等级', trigger: 'change' }],
}

// ─── Helpers ─────────────────────────────────────────────────────────
function riskLabel(level: string): string {
  const map: Record<string, string> = { high: '高', medium: '中', low: '低' }
  return map[level] || level || '-'
}

function riskTagType(level: string): string {
  const map: Record<string, string> = { high: 'danger', medium: 'warning', low: 'info' }
  return map[level] || 'info'
}

function formatTime(t: string): string {
  return t ? new Date(t).toLocaleString('zh-CN') : '-'
}

// ─── Data Loading ────────────────────────────────────────────────────
async function loadList() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (filterRisk.value) params.risk_level = filterRisk.value
    if (filterApproval.value !== '') params.requires_approval = filterApproval.value

    const { data } = await client.get(TOOL_POLICY_API, { params })
    if (data.code === 0) {
      const result = data.data
      tableData.value = (result.items || result || []).map((item: any) => ({
        ...item,
        _toggling: false,
      }))
      pagination.total = result.total || tableData.value.length
    }
  } catch (e: any) {
    ElMessage.error('加载策略列表失败: ' + (e.message || e))
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  searchKeyword.value = ''
  filterRisk.value = ''
  filterApproval.value = ''
  pagination.page = 1
  loadList()
}

// ─── Toggle Approval ────────────────────────────────────────────────
async function toggleApproval(row: any) {
  row._toggling = true
  try {
    const { data } = await client.put(`${TOOL_POLICY_API}/${row.id}`, {
      requires_approval: row.requires_approval,
    })
    if (data.code === 0) {
      ElMessage.success(row.requires_approval ? '已开启审批要求' : '已关闭审批要求')
    } else {
      row.requires_approval = !row.requires_approval
      ElMessage.error(data.message || '操作失败')
    }
  } catch (e: any) {
    row.requires_approval = !row.requires_approval
    ElMessage.error('操作失败: ' + (e.message || e))
  } finally {
    row._toggling = false
  }
}

// ─── CRUD ────────────────────────────────────────────────────────────
function openCreate() {
  isEditing.value = false
  editingId.value = ''
  Object.assign(form, {
    tool_name: '',
    description: '',
    allowed_scope: [],
    risk_level: 'medium',
    requires_approval: false,
    max_calls_per_minute: 0,
    approvers: [],
  })
  dialogVisible.value = true
}

function openEdit(row: any) {
  isEditing.value = true
  editingId.value = row.id
  Object.assign(form, {
    tool_name: row.tool_name || '',
    description: row.description || '',
    allowed_scope: row.allowed_scope || [],
    risk_level: row.risk_level || 'medium',
    requires_approval: row.requires_approval || false,
    max_calls_per_minute: row.max_calls_per_minute || 0,
    approvers: row.approvers || [],
  })
  dialogVisible.value = true
}

async function handleSave() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const payload = { ...form }
    let res: any
    if (isEditing.value) {
      res = await client.put(`${TOOL_POLICY_API}/${editingId.value}`, payload)
    } else {
      res = await client.post(TOOL_POLICY_API, payload)
    }
    if (res.data.code === 0) {
      ElMessage.success(isEditing.value ? '策略已更新' : '策略已创建')
      dialogVisible.value = false
      loadList()
    } else {
      ElMessage.error(res.data.message || '保存失败')
    }
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.message || e))
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定删除工具「${row.tool_name}」的调用策略？`,
      '确认删除',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }
    )
    const { data } = await client.delete(`${TOOL_POLICY_API}/${row.id}`)
    if (data.code === 0) {
      ElMessage.success('已删除')
      loadList()
    } else {
      ElMessage.error(data.message || '删除失败')
    }
  } catch {
    // cancelled
  }
}

function resetForm() {
  formRef.value?.resetFields()
}

// ─── Init ────────────────────────────────────────────────────────────
onMounted(() => {
  loadList()
})
</script>

<style scoped>
.ai-tool-policy-page {
  padding: 0;
}
.autops-page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.top-actions {
  display: flex;
  gap: 8px;
}
.filter-card {
  margin-bottom: 0;
}
.tool-name {
  display: flex;
  align-items: center;
  font-weight: 500;
}
.scope-tags {
  display: flex;
  flex-wrap: wrap;
}
.text-muted {
  color: #c9cdd4;
}
.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
