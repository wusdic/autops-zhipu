<template>
  <div class="autops-page-container">
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">用户管理</div>
        <div class="autops-page-desc">管理系统用户账号</div>
      </div>
      <div class="top-actions">
        <el-button type="primary" @click="showCreateDialog">新建用户</el-button>
      </div>
    </div>

    <!-- Filters -->
    <div class="autops-toolbar">
      <el-input
        v-model="filters.search"
        placeholder="搜索用户名/邮箱"
        clearable
        prefix-icon="Search"
        style="width: 240px"
        @keyup.enter="handleSearch"
        @clear="handleSearch"
      />
      <el-select v-model="filters.role" placeholder="角色筛选" clearable style="width: 160px" @change="handleSearch">
        <el-option v-for="r in roles" :key="r.id" :label="r.name" :value="r.id" />
      </el-select>
      <el-select v-model="filters.status" placeholder="状态筛选" clearable style="width: 130px" @change="handleSearch">
        <el-option label="启用" value="active" />
        <el-option label="禁用" value="disabled" />
        <el-option label="锁定" value="locked" />
      </el-select>
      <el-button @click="handleSearch">查询</el-button>
      <el-button @click="resetFilters">重置</el-button>
    </div>

    <el-table stripe :data="users" v-loading="loading"border style="width: 100%">
      <el-table-column prop="username" label="用户名" width="140" />
      <el-table-column prop="display_name" label="显示名" width="140" />
      <el-table-column prop="email" label="邮箱" width="200" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : row.status === 'disabled' ? 'danger' : 'info'" size="small">
            {{ statusMap[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="角色" min-width="150">
        <template #default="{ row }">
          <el-tag v-for="r in (row.roles || [])" :key="r" size="small" style="margin-right:4px">{{ r }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="editUser(row)">编辑</el-button>
          <el-button size="small" @click="handleResetPassword(row)">重置密码</el-button>
          <el-switch
            size="small"
            :model-value="row.status === 'active'"
            active-text="启用"
            inactive-text="禁用"
            inline-prompt
            style="margin: 0 6px"
            @change="(val: string | number | boolean) => toggleUserStatus(row, val as boolean)"
          />
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-if="total > pageSize" layout="total, prev, pager, next" :total="total" :page-size="pageSize"
      v-model:current-page="currentPage" @current-change="loadUsers" style="margin-top: 16px; justify-content: flex-end" />

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="editingUser ? '编辑用户' : '新建用户'" width="480px">
      <el-form :model="formData" label-width="80px">
        <el-form-item label="用户名" required>
          <el-input v-model="formData.username" :disabled="!!editingUser" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="显示名">
          <el-input v-model="formData.display_name" placeholder="请输入显示名" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="formData.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" v-if="!editingUser">
          <el-input v-model="formData.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="formData.role_ids" multiple placeholder="选择角色" style="width:100%">
            <el-option v-for="r in roles" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" v-if="editingUser">
          <el-select v-model="formData.status">
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="disabled" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">确定</el-button>
      </template>
    </el-dialog>

    <!-- Reset Password Dialog -->
    <el-dialog v-model="resetPwdVisible" title="重置密码" width="480px">
      <el-form :model="resetPwdForm" label-width="80px">
        <el-form-item label="用户">
          <el-input :model-value="resetPwdTarget?.username" disabled />
        </el-form-item>
        <el-form-item label="新密码" required>
          <el-input v-model="resetPwdForm.new_password" type="password" show-password placeholder="请输入新密码" />
        </el-form-item>
        <el-form-item label="确认密码" required>
          <el-input v-model="resetPwdForm.confirm_password" type="password" show-password placeholder="请确认新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="resettingPwd" @click="submitResetPassword">确定重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

const statusMap: Record<string, string> = { active: '启用', disabled: '禁用', locked: '锁定' }
const loading = ref(false)
const saving = ref(false)
const users = ref<any[]>([])
const roles = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const dialogVisible = ref(false)
const editingUser = ref<any>(null)
const formData = ref<any>({
  username: '', display_name: '', email: '', password: '', role_ids: [], status: 'active'
})

// Filters
const filters = reactive({ search: '', role: '', status: ''})

function resetFilters() {
  filters.search = ''
  filters.role = ''
  filters.status = ''
  currentPage.value = 1
  loadUsers()
}

function handleSearch() {
  currentPage.value = 1
  loadUsers()
}

// Reset password
const resetPwdVisible = ref(false)
const resettingPwd = ref(false)
const resetPwdTarget = ref<any>(null)
const resetPwdForm = ref({ new_password: '', confirm_password: ''})

function handleResetPassword(row: any) {
  resetPwdTarget.value = row
  resetPwdForm.value = { new_password: '', confirm_password: ''}
  resetPwdVisible.value = true
}

async function submitResetPassword() {
  if (!resetPwdForm.value.new_password) { ElMessage.warning('请输入新密码'); return }
  if (resetPwdForm.value.new_password !== resetPwdForm.value.confirm_password) {
    ElMessage.warning('两次密码输入不一致'); return
  }
  resettingPwd.value = true
  try {
    await api.post(R.GOVERNANCE.USERS + '/' + resetPwdTarget.value.id + '/reset-password', {
      new_password: resetPwdForm.value.new_password,
    })
    ElMessage.success('密码重置成功')
    resetPwdVisible.value = false
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '密码重置失败')
  } finally {
    resettingPwd.value = false
  }
}

// Enable / Disable user toggle
async function toggleUserStatus(row: any, enabled: boolean) {
  const newStatus = enabled ? 'active' : 'disabled'
  const actionText = enabled ? '启用' : '禁用'
  try {
    await ElMessageBox.confirm('确定' + actionText + '用户 ' + row.username + '?', '确认', { type: 'warning' })
    await api.put(R.GOVERNANCE.USERS + '/' + row.id, { status: newStatus })
    ElMessage.success('已' + actionText + '用户 ' + row.username)
    loadUsers()
  } catch {
    // user cancelled or API error – revert is handled by re-fetch
  }
}

async function loadUsers() {
  loading.value = true
  try {
    const params: any = { page: currentPage.value, page_size: pageSize.value }
    if (filters.search) {
      params.search = filters.search
    }
    if (filters.role) {
      params.role_id = filters.role
    }
    if (filters.status) {
      params.status = filters.status
    }
    const { data } = await api.get(R.GOVERNANCE.USERS, { params })
    if (data.code === 0) {
      users.value = data.data.items || data.data || []
      total.value = data.data.total || users.value.length
    }
  } catch (e: any) {
    ElMessage.error('加载用户失败')
  } finally {
    loading.value = false
  }
}

async function loadRoles() {
  try {
    const { data } = await api.get(R.GOVERNANCE.ROLES)
    if (data.code === 0) {
      roles.value = data.data.items || data.data || []
    }
  } catch { /* ignore */ }
}

function showCreateDialog() {
  editingUser.value = null
  formData.value = { username: '', display_name: '', email: '', password: '', role_ids: [], status: 'active' }
  dialogVisible.value = true
}

function editUser(row: any) {
  editingUser.value = row
  formData.value = {
    username: row.username, display_name: row.display_name, email: row.email,
    password: '', role_ids: (row.roles || []).map((r: any) => typeof r === 'string' ? r : r.id),
    status: row.status
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (!formData.value.username) { ElMessage.warning('请输入用户名'); return }
  saving.value = true
  try {
    if (editingUser.value) {
      await api.put(R.GOVERNANCE.USERS + '/' + editingUser.value.id, formData.value)
      ElMessage.success('更新成功')
    } else {
      await api.post(R.GOVERNANCE.USERS, formData.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadUsers()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '操作失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm('确定删除用户 ' + row.username + '?', '确认', { type: 'warning' })
  try {
    await api.delete(R.GOVERNANCE.USERS + '/' + row.id)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '删除失败')
  }
}

onMounted(() => { loadUsers(); loadRoles() })
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--autops-space-lg); }
.page-header h2 { margin: 0; font-size: var(--autops-font-20); color: var(--autops-text-1); }

.filter-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: var(--autops-space-lg);
  padding: var(--autops-space-md) 16px;
  background: var(--autops-bg-2);
  border-radius: 6px;
}
</style>
