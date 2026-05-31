<template>
  <div class="alert-rules">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>告警规则管理</span>
          <el-button type="primary" :icon="Plus" @click="openCreate">新建规则</el-button>
        </div>
      </template>

      <el-table :data="rules" v-loading="loading" stripe>
        <el-table-column prop="name" label="规则名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="condition" label="条件" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.condition?.metric || row.condition?.expression || row.condition || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="threshold" label="阈值" width="120">
          <template #default="{ row }">
            <code>{{ row.threshold ?? row.condition?.threshold ?? '-' }}</code>
          </template>
        </el-table-column>
        <el-table-column label="严重级别" width="100">
          <template #default="{ row }">
            <SeverityBadge :severity="row.severity" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="启用状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.enabled"
              @change="(val: boolean) => toggleRule(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="170">
          <template #default="{ row }">{{ formatTime(row.updated_at || row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-popconfirm title="确认删除此规则？" @confirm="deleteRule(row.id)">
              <template #reference>
                <el-button text type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑告警规则' : '新建告警规则'"
      width="580px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入规则名称" maxlength="100" />
        </el-form-item>

        <el-form-item label="条件" prop="condition">
          <el-input
            v-model="form.condition"
            placeholder="如: cpu_usage > 90"
            maxlength="500"
          />
        </el-form-item>

        <el-form-item label="阈值" prop="threshold">
          <el-input-number v-model="form.threshold" :precision="2" :step="1" style="width: 100%" />
        </el-form-item>

        <el-form-item label="严重级别" prop="severity">
          <el-select v-model="form.severity" placeholder="请选择严重级别" style="width: 100%">
            <el-option label="严重 (Critical)" value="critical" />
            <el-option label="高 (High)" value="high" />
            <el-option label="中 (Medium)" value="medium" />
            <el-option label="低 (Low)" value="low" />
            <el-option label="信息 (Info)" value="info" />
          </el-select>
        </el-form-item>

        <el-form-item label="启用状态">
          <el-switch v-model="form.enabled" />
        </el-form-item>

        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="规则描述（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import SeverityBadge from '@/shared/components/SeverityBadge.vue'

// ---- 列表 ----
const loading = ref(false)
const rules = ref<any[]>([])

async function loadRules() {
  loading.value = true
  try {
    const { data } = await api.get(R.ALERT_RULES)
    if (data.code === 0) {
      rules.value = data.data?.items || data.data || []
    }
  } catch {
    ElMessage.error('加载告警规则失败')
  } finally {
    loading.value = false
  }
}

async function deleteRule(id: string) {
  try {
    const { data } = await api.delete(`${R.ALERT_RULES}/${id}`)
    if (data.code === 0) {
      ElMessage.success('规则已删除')
      loadRules()
    }
  } catch {
    ElMessage.error('删除失败')
  }
}

async function toggleRule(row: any, enabled: boolean) {
  try {
    const { data } = await api.put(`${R.ALERT_RULES}/${row.id}`, { ...row, enabled })
    if (data.code === 0) {
      ElMessage.success(enabled ? '规则已启用' : '规则已禁用')
    } else {
      row.enabled = !enabled
    }
  } catch {
    row.enabled = !enabled
    ElMessage.error('操作失败')
  }
}

// ---- 弹窗表单 ----
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref('')
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  condition: '',
  threshold: 0,
  severity: 'medium',
  enabled: true,
  description: '',
})

const formRules = reactive<FormRules>({
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  condition: [{ required: true, message: '请输入告警条件', trigger: 'blur' }],
  threshold: [{ required: true, message: '请输入阈值', trigger: 'change' }],
  severity: [{ required: true, message: '请选择严重级别', trigger: 'change' }],
})

function resetForm() {
  form.name = ''
  form.condition = ''
  form.threshold = 0
  form.severity = 'medium'
  form.enabled = true
  form.description = ''
}

function openCreate() {
  isEdit.value = false
  editId.value = ''
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: any) {
  isEdit.value = true
  editId.value = row.id
  form.name = row.name || ''
  form.condition = row.condition?.metric || row.condition?.expression || row.condition || ''
  form.threshold = row.threshold ?? row.condition?.threshold ?? 0
  form.severity = row.severity || 'medium'
  form.enabled = row.enabled ?? true
  form.description = row.description || ''
  dialogVisible.value = true
}

async function submitForm() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload = {
      name: form.name,
      condition: form.condition,
      threshold: form.threshold,
      severity: form.severity,
      enabled: form.enabled,
      description: form.description,
    }

    let response: any
    if (isEdit.value) {
      response = await api.put(`${R.ALERT_RULES}/${editId.value}`, payload)
    } else {
      response = await api.post(R.ALERT_RULES, payload)
    }

    if (response.data.code === 0) {
      ElMessage.success(isEdit.value ? '规则已更新' : '规则已创建')
      dialogVisible.value = false
      loadRules()
    }
  } catch {
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

// ---- 工具 ----
function formatTime(t: string) {
  return t ? new Date(t).toLocaleString('zh-CN') : ''
}

// ---- 初始化 ----
onMounted(() => loadRules())
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
