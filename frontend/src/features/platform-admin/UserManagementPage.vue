<template>
  <div class="page-container">
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="showCreateDialog">新建用户</el-button>
    </div>

    <el-table :data="users" v-loading="loading" stripe border style="width: 100%">
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
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="editUser(row)">编辑</el-button>
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
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

async function loadUsers() {
  loading.value = true
  try {
    const { data } = await api.get(R.GOVERNANCE.USERS, { params: { page: currentPage.value, page_size: pageSize.value } })
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
  await ElMessageBox.confirm(`确定删除用户 ${row.username}?`, '确认', { type: 'warning' })
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
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; color: #303133; }
</style>
