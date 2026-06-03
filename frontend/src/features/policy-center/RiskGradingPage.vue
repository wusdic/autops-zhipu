<template>
  <div class="risk-grading-page">
    <!-- Search & Filter -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="queryForm" @submit.prevent="handleSearch">
        <el-form-item label="策略名">
          <el-input v-model="queryForm.name" placeholder="搜索策略名" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="动作类型">
          <el-select v-model="queryForm.action_type" placeholder="全部" clearable style="width: 160px">
            <el-option label="通知" value="notify" />
            <el-option label="封禁" value="block" />
            <el-option label="隔离" value="isolate" />
            <el-option label="脚本" value="script" />
            <el-option label="工单" value="ticket" />
          </el-select>
        </el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="queryForm.risk_level" placeholder="全部" clearable style="width: 160px">
            <el-option label="严重" value="critical" />
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Data Table -->
    <el-card shadow="never" class="table-card">
      <el-table stripe v-loading="loading" :data="tableData"border style="width: 100%">
        <el-table-column prop="name" label="策略名" min-width="180" show-overflow-tooltip />
        <el-table-column prop="action_type" label="动作类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="actionTagType(row.action_type)" size="small">
              {{ actionLabel(row.action_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="当前风险等级" width="140" align="center">
          <template #default="{ row }">
            <el-tag :color="riskColor(row.risk_level)" effect="dark" size="small" style="border-color: transparent">
              {{ riskLabel(row.risk_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="require_approval" label="需要审批" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.require_approval ? 'danger' : 'info'" size="small">
              {{ row.require_approval ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="approver" label="审批人" width="120" align="center">
          <template #default="{ row }">
            {{ row.approver || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
              {{ row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">配置</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <!-- Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      destroy-on-close
    >
      <el-form
        ref="dialogFormRef"
        v-loading="dialogLoading"
        :model="dialogForm"
        :rules="dialogRules"
        label-width="100px"
      >
        <el-form-item label="策略名">
          <el-input :model-value="dialogForm.name" disabled />
        </el-form-item>

        <el-form-item label="动作类型">
          <el-input :model-value="actionLabel(dialogForm.action_type)" disabled />
        </el-form-item>

        <el-form-item label="风险等级" prop="risk_level">
          <el-select v-model="dialogForm.risk_level" placeholder="请选择风险等级" style="width: 100%">
            <el-option label="严重 (Critical)" value="critical">
              <div style="display: flex; align-items: center; gap: 8px">
                <el-tag color="#f53f3f" effect="dark" size="small" style="border-color: transparent">严重</el-tag>
                <span style="color: #86909c; font-size: 12px">需要立即响应</span>
              </div>
            </el-option>
            <el-option label="高 (High)" value="high">
              <div style="display: flex; align-items: center; gap: 8px">
                <el-tag color="#ff7d00" effect="dark" size="small" style="border-color: transparent">高</el-tag>
                <span style="color: #86909c; font-size: 12px">需要优先处理</span>
              </div>
            </el-option>
            <el-option label="中 (Medium)" value="medium">
              <div style="display: flex; align-items: center; gap: 8px">
                <el-tag color="#165dff" effect="dark" size="small" style="border-color: transparent">中</el-tag>
                <span style="color: #86909c; font-size: 12px">需要关注</span>
              </div>
            </el-option>
            <el-option label="低 (Low)" value="low">
              <div style="display: flex; align-items: center; gap: 8px">
                <el-tag color="#86909c" effect="dark" size="small" style="border-color: transparent">低</el-tag>
                <span style="color: #86909c; font-size: 12px">常规记录</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="需要审批" prop="require_approval">
          <el-switch
            v-model="dialogForm.require_approval"
            active-text="是"
            inactive-text="否"
            inline-prompt
          />
        </el-form-item>

        <el-form-item v-if="dialogForm.require_approval" label="审批人" prop="approver">
          <el-select
            v-model="dialogForm.approver"
            filterable
            allow-create
            placeholder="请选择或输入审批人"
            style="width: 100%"
          >
            <el-option label="安全管理员" value="security_admin" />
            <el-option label="运维主管" value="ops_manager" />
            <el-option label="CTO" value="cto" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogSaving" @click="handleDialogSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { policyService } from '@/shared/api'

interface PolicyRecord {
  id: string | number
  name: string
  action_type: string
  risk_level: string
  require_approval: boolean
  approver: string
  enabled: boolean
}

interface DialogForm {
  id: string | number
  name: string
  action_type: string
  risk_level: string
  require_approval: boolean
  approver: string
}

const loading = ref(false)
const tableData = ref<PolicyRecord[]>([])
const dialogVisible = ref(false)
const dialogLoading = ref(false)
const dialogSaving = ref(false)
const dialogFormRef = ref<FormInstance>()

const dialogForm = reactive<DialogForm>({
  id: '',
  name: '',
  action_type: '',
  risk_level: '',
  require_approval: false,
  approver: '',
})

const dialogRules: FormRules = {
  risk_level: [{ required: true, message: '请选择风险等级', trigger: 'change' }],
  approver: [
    {
      validator: (_rule, value, callback) => {
        if (dialogForm.require_approval && !value) {
          callback(new Error('启用审批时必须指定审批人'))
        } else {
          callback()
        }
      },
      trigger: 'change',
    },
  ],
}

const dialogTitle = computed(() => `风险等级配置 - ${dialogForm.name}`)

const queryForm = reactive({
  name: '',
  action_type: '',
  risk_level: '',
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

function actionTagType(type: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    notify: 'success',
    block: 'danger',
    isolate: 'warning',
    script: '',
    ticket: 'info',
  }
  return map[type] || ''
}

function actionLabel(type: string): string {
  const map: Record<string, string> = {
    notify: '通知',
    block: '封禁',
    isolate: '隔离',
    script: '脚本',
    ticket: '工单',
  }
  return map[type] || type || '-'
}

function riskColor(level: string): string {
  const map: Record<string, string> = {
    critical: '#f53f3f',
    high: '#ff7d00',
    medium: '#165dff',
    low: '#86909c',
  }
  return map[level] || '#86909c'
}

function riskLabel(level: string): string {
  const map: Record<string, string> = {
    critical: '严重',
    high: '高',
    medium: '中',
    low: '低',
  }
  return map[level] || level || '-'
}

function buildParams() {
  return {
    page: pagination.page,
    page_size: pagination.page_size,
    name: queryForm.name || undefined,
    action_type: queryForm.action_type || undefined,
    risk_level: queryForm.risk_level || undefined,
  }
}

async function fetchData() {
  loading.value = true
  try {
    const res = await policyService.list(buildParams())
    const data = res.data?.data ?? res.data ?? {}
    tableData.value = (data.items ?? data.records ?? data.list ?? []).map((item: any) => ({
      id: item.id,
      name: item.name ?? '',
      action_type: item.action_type ?? item.actions?.[0] ?? '',
      risk_level: item.risk_level ?? '',
      require_approval: item.require_approval ?? false,
      approver: item.approver ?? '',
      enabled: item.enabled ?? true,
    }))
    pagination.total = data.total ?? tableData.value.length
  } catch (e: any) {
    ElMessage.error('获取策略列表失败: ' + (e.message ?? '未知错误'))
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchData()
}

function handleReset() {
  queryForm.name = ''
  queryForm.action_type = ''
  queryForm.risk_level = ''
  handleSearch()
}

function handleEdit(row: PolicyRecord) {
  dialogForm.id = row.id
  dialogForm.name = row.name
  dialogForm.action_type = row.action_type
  dialogForm.risk_level = row.risk_level
  dialogForm.require_approval = row.require_approval
  dialogForm.approver = row.approver
  dialogVisible.value = true
}

async function handleDialogSave() {
  if (!dialogFormRef.value) return
  const valid = await dialogFormRef.value.validate().catch(() => false)
  if (!valid) return

  dialogSaving.value = true
  try {
    await policyService.update(dialogForm.id, {
      risk_level: dialogForm.risk_level,
      require_approval: dialogForm.require_approval,
      approver: dialogForm.require_approval ? dialogForm.approver : '',
    })
    ElMessage.success('风险等级配置已更新')
    dialogVisible.value = false
    fetchData()
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.message ?? '未知错误'))
  } finally {
    dialogSaving.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.risk-grading-page {
  padding: 16px;
}
.filter-card {
  margin-bottom: 16px;
}
.table-card {
  margin-bottom: 16px;
}
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
