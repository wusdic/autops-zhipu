<template>
  <div class="script-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>脚本库</span>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon><Plus /></el-icon> 新建脚本
          </el-button>
        </div>
      </template>

      <!-- Filters -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="搜索">
          <el-input v-model="filters.search" placeholder="脚本名称搜索" clearable @clear="loadScripts" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.script_type" placeholder="全部" clearable @change="loadScripts">
            <el-option label="Shell" value="shell" />
            <el-option label="Python" value="python" />
            <el-option label="PowerShell" value="powershell" />
            <el-option label="SQL" value="sql" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadScripts">查询</el-button>
        </el-form-item>
      </el-form>

      <!-- Table -->
      <el-table :data="scripts" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column prop="script_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.script_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-popconfirm title="确认删除该脚本?" @confirm="deleteScript(row.id)">
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
        @change="loadScripts"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="showFormDialog" :title="isEditing ? '编辑脚本' : '新建脚本'" width="700px">
      <el-form :model="formData" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="formData.name" placeholder="请输入脚本名称" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="formData.script_type" style="width: 100%">
            <el-option label="Shell" value="shell" />
            <el-option label="Python" value="python" />
            <el-option label="PowerShell" value="powershell" />
            <el-option label="SQL" value="sql" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" placeholder="脚本用途说明" />
        </el-form-item>
        <el-form-item label="脚本内容" required>
          <el-input
            v-model="formData.content"
            type="textarea"
            :rows="14"
            placeholder="请输入脚本代码"
            style="font-family: monospace"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button type="primary" @click="saveScript" :loading="saving">{{ isEditing ? '保存' : '创建' }}</el-button>
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
const scripts = ref<any[]>([])
const showFormDialog = ref(false)
const isEditing = ref(false)
const editingId = ref('')

const filters = reactive({ search: '', script_type: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const defaultForm = {
  name: '',
  script_type: 'shell',
  description: '',
  content: '',
}
const formData = reactive({ ...defaultForm })

async function loadScripts() {
  loading.value = true
  try {
    const params: any = { page: pagination.page, page_size: pagination.pageSize }
    if (filters.search) params.search = filters.search
    if (filters.script_type) params.script_type = filters.script_type
    const { data } = await api.get(API.SCRIPTS, { params })
    if (data.code === 0) {
      scripts.value = data.data.items || []
      pagination.total = data.data.total || 0
    }
  } catch (e: any) {
    ElMessage.error('加载脚本失败: ' + (e.message || e))
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
    script_type: row.script_type,
    description: row.description || '',
    content: row.content || '',
  })
  showFormDialog.value = true
}

async function saveScript() {
  if (!formData.name || !formData.content) {
    ElMessage.warning('名称和脚本内容为必填项')
    return
  }
  saving.value = true
  try {
    if (isEditing.value) {
      const { data } = await api.put(API.SCRIPTS + '/' + editingId.value, formData)
      if (data.code === 0) {
        ElMessage.success('保存成功')
        showFormDialog.value = false
        loadScripts()
      } else {
        ElMessage.error(data.message || '保存失败')
      }
    } else {
      const { data } = await api.post(API.SCRIPTS, formData)
      if (data.code === 0) {
        ElMessage.success('创建成功')
        showFormDialog.value = false
        Object.assign(formData, { ...defaultForm })
        loadScripts()
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

async function deleteScript(id: string) {
  try {
    await api.delete(API.SCRIPTS + '/' + id)
    ElMessage.success('删除成功')
    loadScripts()
  } catch (e: any) {
    ElMessage.error('删除失败: ' + (e.message || e))
  }
}

onMounted(() => loadScripts())
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filter-form { margin-bottom: 16px; }
</style>
