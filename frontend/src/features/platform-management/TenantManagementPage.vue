<template>
  <div class="page-container">
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">租户管理</div>
        <div class="autops-page-desc">多租户资源与配额管理</div>
      </div>
      <div class="header-actions">
        <el-button @click="loadTenants" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon> 新建租户
        </el-button>
      </div>
    </div>

    <!-- ── Filters ──────────────────────────────────────── -->
    <div class="filter-bar">
      <el-input
        v-model="keyword"
        placeholder="搜索租户名称/编码..."
        clearable
        prefix-icon="Search"
        style="width: 260px"
        @keyup.enter="loadTenants"
      />
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px">
        <el-option label="正常" value="active" />
        <el-option label="停用" value="disabled" />
        <el-option label="已过期" value="expired" />
      </el-select>
      <el-button type="primary" @click="loadTenants">查询</el-button>
    </div>

    <!-- ── Table ────────────────────────────────────────── -->
    <el-table stripe
 :data="tenants"
 v-loading="loading"border
 row-key="id"
 empty-text="暂无租户"
 style="width: 100%"
 >
      <el-table-column prop="name" label="租户名称" min-width="160" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="tenant-name">{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="code" label="租户编码" width="130" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag
            :type="tenantStatusMap[row.status] ?? 'info'"
            size="small"
            effect="dark"
          >
            {{ tenantStatusLabel[row.status] ?? row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="admin" label="管理员" width="110" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="text-secondary">{{ row.admin || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="资源配额" min-width="200">
        <template #default="{ row }">
          <div class="quota-cell">
            <div class="quota-item">
              <span class="quota-label">用户</span>
              <span class="quota-value">{{ row.used_users ?? 0 }} / {{ row.max_users ?? '∞' }}</span>
            </div>
            <div class="quota-item">
              <span class="quota-label">资产</span>
              <span class="quota-value">{{ row.used_assets ?? 0 }} / {{ row.max_assets ?? '∞' }}</span>
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="expire_at" label="过期时间" width="170">
        <template #default="{ row }">
          <span :class="{ 'text-danger': isExpired(row.expire_at) }">
            {{ formatTime(row.expire_at) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">
          <span class="text-secondary">{{ formatTime(row.created_at) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right" align="center">
        <template #default="{ row }">
          <el-button plain type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button
            v-if="row.status === 'active'"
            plain
            type="warning"
            size="small"
            @click="toggleTenant(row, 'disabled')"
          >
            停用
          </el-button>
          <el-button
            v-else
            plain
            type="success"
            size="small"
            @click="toggleTenant(row, 'active')"
          >
            启用
          </el-button>
          <el-button plain type="danger" size="small" @click="deleteTenant(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadTenants"
        @size-change="loadTenants"
      />
    </div>

    <!-- ── Create / Edit Dialog ──────────────────────────── -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑租户' : '新建租户'"
      width="600px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="租户名称" prop="name">
          <el-input v-model="form.name" placeholder="如：某某公司" />
        </el-form-item>
        <el-form-item label="租户编码" prop="code">
          <el-input
            v-model="form.code"
            placeholder="唯一标识，如 company-a"
            :disabled="isEditing"
          />
        </el-form-item>
        <el-form-item label="管理员" prop="admin">
          <el-input v-model="form.admin" placeholder="管理员邮箱或用户名" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact" placeholder="联系人姓名" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.phone" placeholder="联系电话" />
        </el-form-item>
        <el-divider content-position="left">资源配额</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="用户上限">
              <el-input-number v-model="form.max_users" :min="1" :max="100000" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="资产上限">
              <el-input-number v-model="form.max_assets" :min="1" :max="1000000" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="策略上限">
              <el-input-number v-model="form.max_policies" :min="1" :max="10000" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Playbook上限">
              <el-input-number v-model="form.max_playbooks" :min="1" :max="10000" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="过期时间">
          <el-date-picker
            v-model="form.expire_at"
            type="datetime"
            placeholder="选择过期时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DDTHH:mm:ssZ"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="可选备注" />
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
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Refresh, Plus } from '@element-plus/icons-vue'
import { platformService } from '@/shared/api'

// ── Maps ─────────────────────────────────────────────────
const tenantStatusMap: Record<string, string> = {
  active: 'success',
  disabled: 'info',
  expired: 'danger',
}
const tenantStatusLabel: Record<string, string> = {
  active: '正常',
  disabled: '停用',
  expired: '已过期',
}

// ── State ────────────────────────────────────────────────
const loading = ref(false)
const submitting = ref(false)
const tenants = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const keyword = ref('')
const filterStatus = ref('')

const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref('')
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  code: '',
  admin: '',
  contact: '',
  phone: '',
  max_users: 100,
  max_assets: 1000,
  max_policies: 100,
  max_playbooks: 50,
  expire_at: '',
  remark: '',
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入租户名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入租户编码', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '仅支持字母、数字、下划线和短横线', trigger: 'blur' },
  ],
  admin: [{ required: true, message: '请输入管理员', trigger: 'blur' }],
}

// ── Helpers ──────────────────────────────────────────────
function formatTime(val: string | undefined): string {
  if (!val) return '-'
  try {
    return new Date(val).toLocaleString('zh-CN')
  } catch {
    return val
  }
}

function isExpired(val: string | undefined): boolean {
  if (!val) return false
  try {
    return new Date(val).getTime() < Date.now()
  } catch {
    return false
  }
}

// ── Data Loading ─────────────────────────────────────────
async function loadTenants() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize.value,
    }
    if (keyword.value) params.keyword = keyword.value
    if (filterStatus.value) params.status = filterStatus.value

    const res = await platformService.tenants(params)
    const data = res.data?.data ?? res.data
    if (Array.isArray(data)) {
      tenants.value = data
      total.value = data.length
    } else {
      tenants.value = data?.items ?? data?.list ?? []
      total.value = data?.total ?? tenants.value.length
    }
  } catch (err: any) {
    ElMessage.error(err.message || '加载租户列表失败')
  } finally {
    loading.value = false
  }
}

// ── Dialog ───────────────────────────────────────────────
function resetForm() {
  form.name = ''
  form.code = ''
  form.admin = ''
  form.contact = ''
  form.phone = ''
  form.max_users = 100
  form.max_assets = 1000
  form.max_policies = 100
  form.max_playbooks = 50
  form.expire_at = ''
  form.remark = ''
}

function openCreateDialog() {
  isEditing.value = false
  editingId.value = ''
  resetForm()
  dialogVisible.value = true
}

function openEditDialog(row: any) {
  isEditing.value = true
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    code: row.code,
    admin: row.admin ?? '',
    contact: row.contact ?? '',
    phone: row.phone ?? '',
    max_users: row.max_users ?? 100,
    max_assets: row.max_assets ?? 1000,
    max_policies: row.max_policies ?? 100,
    max_playbooks: row.max_playbooks ?? 50,
    expire_at: row.expire_at ?? '',
    remark: row.remark ?? '',
  })
  dialogVisible.value = true
}

async function submitForm() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload = { ...form }
    if (isEditing.value) {
      await platformService.tenantUpdate(editingId.value, payload)
      ElMessage.success('租户已更新')
    } else {
      await platformService.tenantCreate(payload)
      ElMessage.success('租户已创建')
    }
    dialogVisible.value = false
    loadTenants()
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

// ── Toggle Status ────────────────────────────────────────
async function toggleTenant(row: any, newStatus: string) {
  const label = newStatus === 'active' ? '启用' : '停用'
  try {
    await ElMessageBox.confirm(
      `确定${label}租户「${row.name}」吗？`,
      `${label}确认`,
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
    await platformService.tenantUpdate(row.id, { status: newStatus })
    ElMessage.success(`已${label}租户 ${row.name}`)
    loadTenants()
  } catch {
    // cancelled
  }
}

// ── Delete ───────────────────────────────────────────────
async function deleteTenant(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定删除租户「${row.name}」吗？此操作不可恢复！`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'error' },
    )
    // Use tenantUpdate with status deleted or a direct delete if available
    await platformService.tenantUpdate(row.id, { status: 'deleted' })
    ElMessage.success('租户已删除')
    loadTenants()
  } catch {
    // cancelled
  }
}

// ── Init ─────────────────────────────────────────────────
onMounted(() => {
  loadTenants()
})
</script>

<style scoped>
.autops-page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.tenant-name {
  font-weight: 500;
}

.text-secondary {
  color: #86909c;
  font-size: 12px;
}
.quota-cell {
  display: flex;
  gap: 16px;
}
.quota-item {
  display: flex;
  gap: 4px;
  font-size: 12px;
}
.quota-label {
  color: #86909c;
}
.quota-value {
  color: #4e5969;
  font-weight: 500;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
