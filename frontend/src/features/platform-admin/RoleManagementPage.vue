<template>
  <div class="page-container">
    <div class="page-header">
      <h2>角色管理</h2>
      <el-button type="primary" @click="showCreateDialog">新建角色</el-button>
    </div>

    <el-table :data="roles" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="name" label="角色名称" width="160" />
      <el-table-column prop="description" label="描述" min-width="200" />
      <el-table-column label="权限" min-width="260">
        <template #default="{ row }">
          <el-tag v-for="p in (row.permissions || [])" :key="p" size="small" style="margin-right:4px">
            {{ permissionLabels[p] || p }}
          </el-tag>
          <span v-if="!row.permissions?.length" class="text-muted">—</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="editRole(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="editingRole ? '编辑角色' : '新建角色'" width="560px">
      <el-form :model="formData" label-width="80px">
        <el-form-item label="角色名称" required>
          <el-input v-model="formData.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="2" placeholder="请输入角色描述" />
        </el-form-item>
        <el-form-item label="权限">
          <el-checkbox-group v-model="formData.permissions">
            <el-checkbox v-for="opt in permissionOptions" :key="opt.value" :label="opt.value">
              {{ opt.label }}
            </el-checkbox>
          </el-checkbox-group>
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

// 权限选项列表
const permissionOptions = [
  { value: 'asset:read', label: '资产查看' },
  { value: 'asset:write', label: '资产编辑' },
  { value: 'alert:read', label: '告警查看' },
  { value: 'alert:write', label: '告警处理' },
  { value: 'policy:read', label: '策略查看' },
  { value: 'policy:write', label: '策略编辑' },
  { value: 'script:read', label: '脚本查看' },
  { value: 'script:write', label: '脚本编辑' },
  { value: 'execution:read', label: '执行查看' },
  { value: 'execution:write', label: '执行操作' },
  { value: 'admin:user', label: '用户管理' },
  { value: 'admin:role', label: '角色管理' },
  { value: 'admin:config', label: '系统配置' },
  { value: 'admin:audit', label: '审计日志' },
]

const permissionLabels: Record<string, string> = {}
permissionOptions.forEach(o => { permissionLabels[o.value] = o.label })

const loading = ref(false)
const saving = ref(false)
const roles = ref<any[]>([])
const dialogVisible = ref(false)
const editingRole = ref<any>(null)
const formData = ref<any>({
  name: '',
  description: '',
  permissions: [],
})

async function loadRoles() {
  loading.value = true
  try {
    const { data } = await api.get(R.GOVERNANCE.ROLES)
    if (data.code === 0) {
      roles.value = data.data.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载角色列表失败')
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  editingRole.value = null
  formData.value = { name: '', description: '', permissions: [] }
  dialogVisible.value = true
}

function editRole(row: any) {
  editingRole.value = row
  formData.value = {
    name: row.name,
    description: row.description || '',
    permissions: [...(row.permissions || [])],
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (!formData.value.name) { ElMessage.warning('请输入角色名称'); return }
  saving.value = true
  try {
    if (editingRole.value) {
      await api.put(R.GOVERNANCE.ROLES + '/' + editingRole.value.id, formData.value)
      ElMessage.success('更新成功')
    } else {
      await api.post(R.GOVERNANCE.ROLES, formData.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadRoles()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '操作失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm(`确定删除角色「${row.name}」？删除后不可恢复。`, '确认删除', { type: 'warning' })
  try {
    await api.delete(R.GOVERNANCE.ROLES + '/' + row.id)
    ElMessage.success('删除成功')
    loadRoles()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '删除失败')
  }
}

onMounted(() => { loadRoles() })
</script>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; color: #303133; }
.text-muted { color: #909399; }
</style>
