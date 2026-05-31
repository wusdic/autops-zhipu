<template>
  <div class="policy-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>策略管理</span>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon><Plus /></el-icon> 新建策略
          </el-button>
        </div>
      </template>

      <!-- Filters -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="搜索">
          <el-input v-model="filters.search" placeholder="策略名称搜索" clearable @clear="loadPolicies" />
        </el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="filters.risk_level" placeholder="全部" clearable @change="loadPolicies">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="严重" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用状态">
          <el-select v-model="filters.enabled" placeholder="全部" clearable @change="loadPolicies">
            <el-option label="已启用" :value="true" />
            <el-option label="已禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadPolicies">查询</el-button>
        </el-form-item>
      </el-form>

      <!-- Table -->
      <el-table :data="policies" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column prop="trigger_condition" label="触发条件" min-width="220" show-overflow-tooltip />
        <el-table-column prop="risk_level" label="风险等级" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="riskTagType(row.risk_level)" size="small">{{ riskLabel(row.risk_level) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="启用状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.enabled"
              @change="(val: boolean) => togglePolicy(row, val)"
              :loading="row._toggling"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button size="small" type="success" @click="goSimulate(row)">模拟</el-button>
            <el-popconfirm title="确认删除该策略?" @confirm="deletePolicy(row.id)">
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
        @change="loadPolicies"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="showFormDialog" :title="isEditing ? '编辑策略' : '新建策略'" width="650px">
      <el-form :model="formData" label-width="90px">
        <el-form-item label="名称" required>
          <el-input v-model="formData.name" placeholder="请输入策略名称" />
        </el-form-item>
        <el-form-item label="触发条件" required>
          <el-input
            v-model="formData.trigger_condition"
            type="textarea"
            :rows="4"
            placeholder="请输入触发条件表达式，例如: alert.severity >= 'high' AND asset.type == 'linux_server'"
            style="font-family: monospace"
          />
        </el-form-item>
        <el-form-item label="风险等级" required>
          <el-select v-model="formData.risk_level" style="width: 100%">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="严重" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联Playbook">
          <el-input v-model="formData.playbook_id" placeholder="关联的 Playbook ID（可选）" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="策略用途说明" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="formData.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button type="primary" @click="savePolicy" :loading="saving">{{ isEditing ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()

const loading = ref(false)
const saving = ref(false)
const policies = ref<any[]>([])
const showFormDialog = ref(false)
const isEditing = ref(false)
const editingId = ref('')

const filters = reactive({ search: '', risk_level: '', enabled: '' as string | boolean | number })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const defaultForm = {
  name: '',
  trigger_condition: '',
  risk_level: 'medium',
  playbook_id: '',
  description: '',
  enabled: true,
}
const formData = reactive({ ...defaultForm })

function riskTagType(level: string) {
  const map: Record<string, string> = { low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }
  return map[level] || 'info'
}

function riskLabel(level: string) {
  const map: Record<string, string> = { low: '低', medium: '中', high: '高', critical: '严重' }
  return map[level] || level
}

async function loadPolicies() {
  loading.value = true
  try {
    const params: any = { page: pagination.page, page_size: pagination.pageSize }
    if (filters.search) params.search = filters.search
    if (filters.risk_level) params.risk_level = filters.risk_level
    if (filters.enabled !== '' && filters.enabled !== null) params.enabled = filters.enabled
    const { data } = await api.get(API.POLICIES, { params })
    if (data.code === 0) {
      policies.value = (data.data.items || []).map((p: any) => ({ ...p, _toggling: false }))
      pagination.total = data.data.total || 0
    }
  } catch (e: any) {
    ElMessage.error('加载策略失败: ' + (e.message || e))
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
    trigger_condition: row.trigger_condition || '',
    risk_level: row.risk_level || 'medium',
    playbook_id: row.playbook_id || '',
    description: row.description || '',
    enabled: row.enabled ?? true,
  })
  showFormDialog.value = true
}

async function savePolicy() {
  if (!formData.name || !formData.trigger_condition) {
    ElMessage.warning('名称和触发条件为必填项')
    return
  }
  saving.value = true
  try {
    const payload: any = { ...formData }
    if (!payload.playbook_id) delete payload.playbook_id

    if (isEditing.value) {
      const { data } = await api.put(API.POLICY_DETAIL(editingId.value), payload)
      if (data.code === 0) {
        ElMessage.success('保存成功')
        showFormDialog.value = false
        loadPolicies()
      } else {
        ElMessage.error(data.message || '保存失败')
      }
    } else {
      const { data } = await api.post(API.POLICIES, payload)
      if (data.code === 0) {
        ElMessage.success('创建成功')
        showFormDialog.value = false
        Object.assign(formData, { ...defaultForm })
        loadPolicies()
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

async function togglePolicy(row: any, val: boolean) {
  row._toggling = true
  try {
    const { data } = await api.patch(API.POLICY_DETAIL(row.id), { enabled: val })
    if (data.code === 0) {
      ElMessage.success(val ? '已启用' : '已禁用')
    } else {
      row.enabled = !val
      ElMessage.error(data.message || '操作失败')
    }
  } catch (e: any) {
    row.enabled = !val
    ElMessage.error('操作失败: ' + (e.message || e))
  } finally {
    row._toggling = false
  }
}

function goSimulate(row: any) {
  router.push({ name: 'policy-simulate', params: { id: row.id } })
}

async function deletePolicy(id: string) {
  try {
    await api.delete(API.POLICY_DETAIL(id))
    ElMessage.success('删除成功')
    loadPolicies()
  } catch (e: any) {
    ElMessage.error('删除失败: ' + (e.message || e))
  }
}

onMounted(() => loadPolicies())
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filter-form { margin-bottom: 16px; }
</style>
