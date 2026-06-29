<template>
  <div class="autops-page-container">
    <PageHeader title="角色管理" desc="管理角色与权限">
      <template #actions>
        <el-button type="primary" @click="showCreateDialog">新建角色</el-button>
      </template>
    </PageHeader>

    <el-table stripe :data="roles" v-loading="loading"border style="width: 100%">
      <el-table-column prop="name" label="角色名称" width="160">
        <template #default="{ row }">
          {{ row.name }}
          <el-tag v-if="row.is_system" type="warning" size="small" style="margin-left:6px">系统</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="180" />
      <el-table-column label="用户数" width="100" align="center">
        <template #default="{ row }">
          <el-tag type="info" size="small">{{ row.user_count ?? '—' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="权限" min-width="260">
        <template #default="{ row }">
          <el-tag v-for="p in (row.permissions || []).slice(0, 5)" :key="p" size="small" style="margin-right:4px">
            {{ permissionLabels[p] || p }}
          </el-tag>
          <el-tag v-if="(row.permissions || []).length > 5" size="small" type="info" style="margin-right:4px">
            +{{ row.permissions.length - 5 }}
          </el-tag>
          <span v-if="!row.permissions?.length" class="text-muted">—</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="editRole(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)" :disabled="row.is_system">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Create/Edit Dialog with Permission Tree -->
    <el-dialog v-model="dialogVisible" :title="editingRole ? '编辑角色' : '新建角色'" width="600px">
      <el-form :model="formData" label-width="80px">
        <el-form-item label="角色名称" required>
          <el-input v-model="formData.name" placeholder="请输入角色名称" :disabled="editingRole?.is_system" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="2" placeholder="请输入角色描述" />
        </el-form-item>
        <el-form-item label="权限">
          <div class="permission-tree-wrapper">
            <el-tree
              ref="permTreeRef"
              :data="permissionTree"
              show-checkbox
              node-key="value"
              :default-checked-keys="formData.permissions"
              :props="{ label: 'label', children: 'children' }"
              @check="onPermissionCheck"
            />
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">确定</el-button>
      </template>
    </el-dialog>

    <!-- Delete with Reassign Dialog -->
    <el-dialog v-model="reassignVisible" title="删除角色并转移用户" width="480px">
      <el-alert
        type="warning"
        :closable="false"
        show-icon
        class="mb-lg"
      >
        <template #title>
          角色「{{ deleteTarget?.name }}」下有 <b>{{ deleteTarget?.user_count ?? 0 }}</b> 个用户，请选择转移目标角色
        </template>
      </el-alert>
      <el-form label-width="100px">
        <el-form-item label="转移至角色">
          <el-select v-model="reassignRoleId" placeholder="选择目标角色" style="width: 100%">
            <el-option
              v-for="r in roles.filter(x => x.id !== deleteTarget?.id)"
              :key="r.id"
              :label="r.name"
              :value="r.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reassignVisible = false">取消</el-button>
        <el-button type="danger" :loading="deleting" @click="confirmDeleteWithReassign">
          确认删除并转移
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { ElTree } from 'element-plus'
import api from '@/shared/api/client'
import PageHeader from '@/shared/components/PageHeader.vue'
import { API as R } from '@/shared/api/routes'

// Hierarchical permission tree
const permissionTree = [
  {
    label: '资产管理',
    children: [
      { label: '资产查看', value: 'asset:read' },
      { label: '资产编辑', value: 'asset:write' },
    ],
  },
  {
    label: '告警管理',
    children: [
      { label: '告警查看', value: 'alert:read' },
      { label: '告警处理', value: 'alert:write' },
    ],
  },
  {
    label: '策略管理',
    children: [
      { label: '策略查看', value: 'policy:read' },
      { label: '策略编辑', value: 'policy:write' },
    ],
  },
  {
    label: '脚本管理',
    children: [
      { label: '脚本查看', value: 'script:read' },
      { label: '脚本编辑', value: 'script:write' },
    ],
  },
  {
    label: '执行管理',
    children: [
      { label: '执行查看', value: 'execution:read' },
      { label: '执行操作', value: 'execution:write' },
    ],
  },
  {
    label: '系统管理',
    children: [
      { label: '用户管理', value: 'admin:user' },
      { label: '角色管理', value: 'admin:role' },
      { label: '系统配置', value: 'admin:config' },
      { label: '审计日志', value: 'admin:audit' },
    ],
  },
]

// Flat labels for table display
const permissionLabels: Record<string, string> = {}
function buildLabels(nodes: any[]) {
  nodes.forEach(n => {
    if (n.value) permissionLabels[n.value] = n.label
    if (n.children) buildLabels(n.children)
  })
}
buildLabels(permissionTree)

// State
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const roles = ref<any[]>([])
const dialogVisible = ref(false)
const editingRole = ref<any>(null)
const permTreeRef = ref<InstanceType<typeof ElTree>>()
const formData = ref<any>({
  name: '',
  description: '',
  permissions: [],
})

// Delete with reassign
const reassignVisible = ref(false)
const deleteTarget = ref<any>(null)
const reassignRoleId = ref('')

function onPermissionCheck() {
  if (permTreeRef.value) {
    const checked = permTreeRef.value.getCheckedKeys(true) as string[]
    formData.value.permissions = checked
  }
}

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
  // System role protection
  if (row.is_system || row.name === 'admin' || row.name === 'Administrator') {
    ElMessage.warning('系统内置角色不可删除')
    return
  }

  // Check if role has users
  const userCount = row.user_count ?? 0
  if (userCount > 0) {
    // Show reassign dialog
    deleteTarget.value = row
    reassignRoleId.value = ''
    reassignVisible.value = true
    return
  }

  // No users — simple delete
  await ElMessageBox.confirm('确定删除角色「' + row.name + '」？删除后不可恢复。', '确认删除', { type: 'warning' })
  try {
    await api.delete(R.GOVERNANCE.ROLES + '/' + row.id)
    ElMessage.success('删除成功')
    loadRoles()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '删除失败')
  }
}

async function confirmDeleteWithReassign() {
  if (!reassignRoleId.value) {
    ElMessage.warning('请选择转移目标角色')
    return
  }
  deleting.value = true
  try {
    await api.delete(R.GOVERNANCE.ROLES + '/' + deleteTarget.value.id, {
      data: { reassign_to_role_id: reassignRoleId.value },
    })
    ElMessage.success('删除成功，已转移用户')
    reassignVisible.value = false
    loadRoles()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '删除失败')
  } finally {
    deleting.value = false
  }
}

onMounted(() => { loadRoles() })
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--autops-space-xl); }
.page-header h2 { margin: 0; font-size: var(--autops-font-20); color: var(--autops-text-1); }
.text-muted { color: var(--autops-info); }

.permission-tree-wrapper {
  border: 1px solid var(--autops-bg-4);
  border-radius: var(--autops-radius-sm);
  padding: var(--autops-space-sm) 12px;
  max-height: 320px;
  overflow-y: auto;
  width: 100%;
}
</style>
