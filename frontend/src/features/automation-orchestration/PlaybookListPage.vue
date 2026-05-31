<template>
  <div class="playbook-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Playbook 列表</span>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon><Plus /></el-icon> 新建 Playbook
          </el-button>
        </div>
      </template>

      <!-- Filters -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="搜索">
          <el-input v-model="filters.search" placeholder="Playbook 名称搜索" clearable @clear="loadPlaybooks" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadPlaybooks">查询</el-button>
        </el-form-item>
      </el-form>

      <!-- Table -->
      <el-table :data="playbooks" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" min-width="180" />
        <el-table-column prop="step_count" label="步骤数" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.step_count ?? (row.steps?.length ?? 0) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="240" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-popconfirm title="确认删除该 Playbook?" @confirm="deletePlaybook(row.id)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @change="loadPlaybooks"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="showFormDialog" :title="isEditing ? '编辑 Playbook' : '新建 Playbook'" width="700px">
      <el-form :model="formData" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="formData.name" placeholder="请输入 Playbook 名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="Playbook 用途说明" />
        </el-form-item>
        <el-form-item label="步骤定义">
          <el-input
            v-model="formData.steps_json"
            type="textarea"
            :rows="12"
            placeholder='请输入 JSON 格式步骤定义，例如: [{"action":"run_script","script_id":"xxx","params":{}}]'
            style="font-family: monospace"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button type="primary" @click="savePlaybook" :loading="saving">{{ isEditing ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const loading = ref(false)
const saving = ref(false)
const playbooks = ref<any[]>([])
const showFormDialog = ref(false)
const isEditing = ref(false)
const editingId = ref('')

const filters = reactive({ search: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const defaultForm = {
  name: '',
  description: '',
  steps_json: '',
}
const formData = reactive({ ...defaultForm })

async function loadPlaybooks() {
  loading.value = true
  try {
    const params: any = { page: pagination.page, page_size: pagination.pageSize }
    if (filters.search) params.search = filters.search
    const { data } = await api.get(API.PLAYBOOKS, { params })
    if (data.code === 0) {
      playbooks.value = data.data.items || []
      pagination.total = data.data.total || 0
    }
  } catch (e: any) {
    ElMessage.error('加载 Playbook 失败: ' + (e.message || e))
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  isEditing.value = false
  editingId.value = ''
  Object.assign(formData, { ...defaultForm })
  showFormDialog.value = true
}

function openEditDialog(row: any) {
  isEditing.value = true
  editingId.value = row.id
  Object.assign(formData, {
    name: row.name,
    description: row.description || '',
    steps_json: row.steps ? JSON.stringify(row.steps, null, 2) : '',
  })
  showFormDialog.value = true
}

function buildPayload() {
  const payload: any = {
    name: formData.name,
    description: formData.description,
  }
  if (formData.steps_json.trim()) {
    try {
      payload.steps = JSON.parse(formData.steps_json)
    } catch {
      ElMessage.error('步骤定义 JSON 格式错误')
      return null
    }
  }
  return payload
}

async function savePlaybook() {
  if (!formData.name) {
    ElMessage.warning('名称为必填项')
    return
  }
  const payload = buildPayload()
  if (!payload) return

  saving.value = true
  try {
    if (isEditing.value) {
      const { data } = await api.put(API.PLAYBOOKS + '/' + editingId.value, payload)
      if (data.code === 0) {
        ElMessage.success('保存成功')
        showFormDialog.value = false
        loadPlaybooks()
      } else {
        ElMessage.error(data.message || '保存失败')
      }
    } else {
      const { data } = await api.post(API.PLAYBOOKS, payload)
      if (data.code === 0) {
        ElMessage.success('创建成功')
        showFormDialog.value = false
        Object.assign(formData, { ...defaultForm })
        loadPlaybooks()
      } else {
        ElMessage.error(data.message || '创建失败')
      }
    }
  } catch (e: any) {
    ElMessage.error((isEditing.value ? '保存' : '创建') + '失败: ' + (e.message || e))
  } finally {
    saving.value = false
  }
}

async function deletePlaybook(id: string) {
  try {
    await api.delete(API.PLAYBOOKS + '/' + id)
    ElMessage.success('删除成功')
    loadPlaybooks()
  } catch (e: any) {
    ElMessage.error('删除失败: ' + (e.message || e))
  }
}

onMounted(() => loadPlaybooks())
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filter-form { margin-bottom: 16px; }
</style>
