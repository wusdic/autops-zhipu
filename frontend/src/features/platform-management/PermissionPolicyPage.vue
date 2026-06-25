<template>
  <div class="autops-page-container">
    <!-- 页面头部 -->
    <div class="autops-page-header">
      <div class="autops-page-title">权限策略</div>
      <div class="autops-page-desc">管理系统访问权限策略</div>
    </div>

    <!-- 搜索筛选区 -->
    <el-card class="filter-card" shadow="never">
      <el-form :model="queryParams" inline @submit.prevent="handleSearch">
        <el-form-item label="策略名">
          <el-input
            v-model="queryParams.name"
            placeholder="搜索策略名称"
            clearable
            style="width: 220px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="资源类型">
          <el-select v-model="queryParams.resource_type" placeholder="全部资源" clearable style="width: 160px">
            <el-option v-for="rt in resourceTypes" :key="rt.value" :label="rt.label" :value="rt.value" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="queryParams.enabled" placeholder="全部状态" clearable style="width: 120px">
            <el-option label="已启用" value="true" />
            <el-option label="已禁用" value="false" />
          </el-select>
        </el-form-item>

        <el-form-item label="角色">
          <el-select
            v-model="queryParams.role_id"
            placeholder="全部角色"
            clearable
            style="width: 160px"
          >
            <el-option
              v-for="role in roleOptions"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 策略列表表格 -->
    <el-card class="table-card" shadow="never">
      <template #header>
        <div class="autops-card-header">
          <span>权限策略</span>
          <el-button type="primary" :icon="Plus" @click="handleCreate">新建策略</el-button>
        </div>
      </template>

      <el-table stripe
 v-loading="loading"
 :data="policyList"border
 style="width: 100%"
 row-key="id"
 >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-content">
              <h4 style="margin: 0 0 12px 0">权限详情</h4>
              <el-table stripe  :data="row.permissions || []" size="small" border>
                <el-table-column prop="resource_type" label="资源类型" width="140">
                  <template #default="{ row: perm }">
                    {{ resourceTypeLabel(perm.resource_type) }}
                  </template>
                </el-table-column>
                <el-table-column prop="actions" label="操作权限" min-width="300">
                  <template #default="{ row: perm }">
                    <el-tag
                      v-for="action in (perm.actions || [])"
                      :key="action"
                      :type="(actionTagType(action)) as TagType"
                      size="small"
                      style="margin-right: 6px"
                    >
                      {{ actionLabel(action) }}
                    </el-tag>
                    <span v-if="!perm.actions?.length" class="text-muted">无权限</span>
                  </template>
                </el-table-column>
                <el-table-column prop="condition" label="条件约束" min-width="200">
                  <template #default="{ row: perm }">
                    {{ perm.condition || '无' }}
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="name" label="策略名" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="policy-name">{{ row.name }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="resource_type" label="资源类型" width="140" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ resourceTypeLabel(row.resource_type) }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="actions" label="操作权限" width="280" align="center">
          <template #default="{ row }">
            <el-tag
              v-for="action in (row.actions || [])"
              :key="action"
              :type="(actionTagType(action)) as TagType"
              size="small"
              style="margin: 2px"
            >
              {{ actionLabel(action) }}
            </el-tag>
            <span v-if="!row.actions?.length" class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="role" label="关联角色" width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <template v-if="row.roles?.length">
              <el-tag
                v-for="role in row.roles"
                :key="role.id || role"
                size="small"
                style="margin-right: 4px"
              >
                {{ role.name || role }}
              </el-tag>
            </template>
            <template v-else-if="row.role">
              <el-tag size="small">{{ row.role.name || row.role }}</el-tag>
            </template>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="enabled" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.enabled"
              size="small"
              @change="(val: string | number | boolean) => handleToggleEnabled(row, val as boolean)"
            />
          </template>
        </el-table-column>

        <el-table-column prop="updated_at" label="更新时间" width="170" align="center">
          <template #default="{ row }">
            {{ formatTime(row.updated_at || row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" plain size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="info" plain size="small" @click="handleClone(row)">克隆</el-button>
            <el-popconfirm
              title="确定删除该策略吗？此操作不可恢复。"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button type="danger" plain size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="fetchPolicyList"
          @current-change="fetchPolicyList"
        />
      </div>
    </el-card>

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑策略' : '新建策略'"
      width="780px"
      destroy-on-close
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="policyForm"
        :rules="formRules"
        label-width="100px"
        label-suffix=":"
      >
        <el-form-item label="策略名" prop="name">
          <el-input v-model="policyForm.name" placeholder="请输入策略名称" maxlength="64" show-word-limit />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="policyForm.description"
            type="textarea"
            :rows="2"
            placeholder="策略描述（选填）"
            maxlength="256"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="资源类型" prop="resource_type">
          <el-select v-model="policyForm.resource_type" placeholder="请选择资源类型" style="width: 100%">
            <el-option
              v-for="rt in resourceTypes"
              :key="rt.value"
              :label="rt.label"
              :value="rt.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="操作权限" prop="actions">
          <el-checkbox-group v-model="policyForm.actions">
            <el-checkbox label="create">
              <el-tag type="success" size="small">创建 (C)</el-tag>
            </el-checkbox>
            <el-checkbox label="read">
              <el-tag type="primary" size="small">读取 (R)</el-tag>
            </el-checkbox>
            <el-checkbox label="update">
              <el-tag type="warning" size="small">更新 (U)</el-tag>
            </el-checkbox>
            <el-checkbox label="delete">
              <el-tag type="danger" size="small">删除 (D)</el-tag>
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="关联角色" prop="role_ids">
          <el-select
            v-model="policyForm.role_ids"
            multiple
            placeholder="选择关联角色"
            style="width: 100%"
          >
            <el-option
              v-for="role in roleOptions"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="条件约束">
          <el-input
            v-model="policyForm.condition"
            placeholder="如：resource.owner = {{ user.id }}（选填）"
          />
        </el-form-item>

        <el-form-item label="启用">
          <el-switch v-model="policyForm.enabled" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { API } from '@/shared/api/routes'
import client from '@/shared/api/client'
import type { AxiosResponse } from 'axios'

// ---------- 类型定义 ----------
interface RoleOption {
  id: string | number
  name: string
  [key: string]: unknown
}

interface Permission {
  resource_type: string
  actions: string[]
  condition?: string
}

interface PolicyEntry {
  id: string | number
  name: string
  description?: string
  resource_type: string
  actions: string[]
  roles?: Array<RoleOption | string>
  role?: RoleOption | string
  role_ids?: Array<string | number>
  enabled: boolean
  condition?: string
  permissions?: Permission[]
  created_at?: string
  updated_at?: string
  [key: string]: unknown
}

interface QueryParams {
  name: string
  resource_type: string
  enabled: string
  role_id: string
  page: number
  pageSize: number
}

interface PolicyForm {
  id?: string | number
  name: string
  description: string
  resource_type: string
  actions: string[]
  role_ids: Array<string | number>
  condition: string
  enabled: boolean
}

// ---------- 常量 ----------
const resourceTypes = [
  { label: '主机', value: 'host' },
  { label: '应用', value: 'application' },
  { label: '数据库', value: 'database' },
  { label: '中间件', value: 'middleware' },
  { label: '网络设备', value: 'network' },
  { label: '存储', value: 'storage' },
  { label: '容器', value: 'container' },
  { label: '用户', value: 'user' },
  { label: '角色', value: 'role' },
  { label: '自动化任务', value: 'automation' },
  { label: '巡检任务', value: 'inspection' },
  { label: '报表', value: 'report' },
]

// ---------- 状态 ----------
const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const policyList = ref<PolicyEntry[]>([])
const roleOptions = ref<RoleOption[]>([])
const total = ref(0)
const formRef = ref<FormInstance>()

const queryParams = reactive<QueryParams>({
  name: '',
  resource_type: '',
  enabled: '',
  role_id: '',
  page: 1,
  pageSize: 20,
})

const policyForm = reactive<PolicyForm>({
  name: '',
  description: '',
  resource_type: '',
  actions: [],
  role_ids: [],
  condition: '',
  enabled: true,
})

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' },
    { min: 2, max: 64, message: '长度在 2 到 64 个字符', trigger: 'blur' },
  ],
  resource_type: [
    { required: true, message: '请选择资源类型', trigger: 'change' },
  ],
  actions: [
    { required: true, type: 'array', min: 1, message: '请至少选择一个操作权限', trigger: 'change' },
  ],
  role_ids: [
    { required: true, type: 'array', min: 1, message: '请至少选择一个角色', trigger: 'change' },
  ],
}

// ---------- 工具函数 ----------
const formatTime = (ts?: string): string => {
  if (!ts) return '-'
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ts
  return d.toLocaleString('zh-CN', { hour12: false })
}

const resourceTypeLabel = (type?: string): string => {
  const found = resourceTypes.find(rt => rt.value === type)
  return found?.label || type || '-'
}

const actionLabel = (action: string): string => {
  const map: Record<string, string> = {
    create: '创建 (C)',
    read: '读取 (R)',
    update: '更新 (U)',
    delete: '删除 (D)',
  }
  return map[action] || action
}

const actionTagType = (action: string): TagType => {
  const map: Record<string, TagType> = {
    create: 'success',
    read: '',
    update: 'warning',
    delete: 'danger',
  }
  return (map[action] || 'info') as TagType
}

// ---------- 数据请求 ----------
const buildParams = (): Record<string, unknown> => {
  const params: Record<string, unknown> = {
    page: queryParams.page,
    page_size: queryParams.pageSize,
  }
  if (queryParams.name) params.name = queryParams.name
  if (queryParams.resource_type) params.resource_type = queryParams.resource_type
  if (queryParams.enabled) params.enabled = queryParams.enabled
  if (queryParams.role_id) params.role_id = queryParams.role_id
  return params
}

const fetchPolicyList = async () => {
  loading.value = true
  try {
    const res: AxiosResponse = await client.get(API.GOVERNANCE.ROLES, { params: buildParams() })
    const data = res.data?.data ?? res.data
    policyList.value = data?.items ?? data?.results ?? data?.list ?? []
    total.value = data?.total ?? data?.count ?? 0
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '获取策略列表失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

const fetchRoleOptions = async () => {
  try {
    const res: AxiosResponse = await client.get(API.GOVERNANCE.ROLES, {
      params: { page_size: 200 },
    })
    const data = res.data?.data ?? res.data
    roleOptions.value = data?.items ?? data?.results ?? data?.list ?? []
  } catch {
    // Silently fail — roles dropdown will be empty
  }
}

// ---------- 事件处理 ----------
const handleSearch = () => {
  queryParams.page = 1
  fetchPolicyList()
}

const handleReset = () => {
  queryParams.name = ''
  queryParams.resource_type = ''
  queryParams.enabled = ''
  queryParams.role_id = ''
  queryParams.page = 1
  queryParams.pageSize = 20
  fetchPolicyList()
}

const resetForm = () => {
  policyForm.id = undefined
  policyForm.name = ''
  policyForm.description = ''
  policyForm.resource_type = ''
  policyForm.actions = []
  policyForm.role_ids = []
  policyForm.condition = ''
  policyForm.enabled = true
  isEdit.value = false
  formRef.value?.resetFields()
}

const handleCreate = () => {
  resetForm()
  isEdit.value = false
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  resetForm()
  isEdit.value = true
  policyForm.id = row.id
  policyForm.name = row.name
  policyForm.description = row.description || ''
  policyForm.resource_type = row.resource_type
  policyForm.actions = [...(row.actions || [])]
  policyForm.role_ids = row.role_ids || (row.roles || []).map((r: RoleOption | string) => typeof r === 'object' ? r.id : r)
  policyForm.condition = row.condition || ''
  policyForm.enabled = row.enabled
  dialogVisible.value = true
}

const handleClone = (row: any) => {
  resetForm()
  isEdit.value = false
  policyForm.name = row.name + ' (副本)'
  policyForm.description = row.description || ''
  policyForm.resource_type = row.resource_type
  policyForm.actions = [...(row.actions || [])]
  policyForm.role_ids = row.role_ids || []
  policyForm.condition = row.condition || ''
  policyForm.enabled = true
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitLoading.value = true
  try {
    if (isEdit.value && policyForm.id) {
      await client.put(API.GOVERNANCE.ROLES + policyForm.id + '/', policyForm)
      ElMessage.success('策略更新成功')
    } else {
      await client.post(API.GOVERNANCE.ROLES, policyForm)
      ElMessage.success('策略创建成功')
    }
    dialogVisible.value = false
    fetchPolicyList()
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '操作失败'
    ElMessage.error(msg)
  } finally {
    submitLoading.value = false
  }
}

const handleToggleEnabled = async (row: any, val: boolean) => {
  try {
    await client.patch(API.GOVERNANCE.ROLES + row.id + '/', { enabled: val })
    row.enabled = val
    ElMessage.success(val ? '策略已启用' : '策略已禁用')
  } catch {
    ElMessage.error('状态切换失败')
  }
}

const handleDelete = async (row: any) => {
  try {
    await client.delete(API.GOVERNANCE.ROLES + row.id + '/')
    ElMessage.success('策略已删除')
    fetchPolicyList()
  } catch {
    ElMessage.error('删除失败')
  }
}

// ---------- 生命周期 ----------
onMounted(() => {
  fetchPolicyList()
  fetchRoleOptions()
})
</script>

<style scoped lang="scss">
.permission-policy-page {
  padding: var(--autops-space-lg);

  .filter-card {
    margin-bottom: var(--autops-space-lg);
  }

  .table-card {
    
    .policy-name {
      font-weight: 500;
      color: var(--autops-text-1);
    }

    .expand-content {
      padding: var(--autops-space-md) 20px;

      h4 {
        font-size: var(--autops-font-14);
        color: var(--autops-text-2);
      }
    }

    .pagination-wrapper {
      display: flex;
      justify-content: flex-end;
      margin-top: var(--autops-space-lg);
    }
  }

  .text-muted {
    color: var(--autops-text-4);
    font-size: var(--autops-font-13);
  }
}
</style>
