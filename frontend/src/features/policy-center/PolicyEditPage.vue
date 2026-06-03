<template>
  <div class="policy-edit-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑策略' : '新建策略' }}</span>
          <el-button @click="handleBack">返回列表</el-button>
        </div>
      </template>

      <el-form
        ref="formRef"
        v-loading="loading"
        :model="formData"
        :rules="formRules"
        label-width="120px"
        style="max-width: 700px"
      >
        <el-form-item label="策略名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入策略名称" maxlength="100" show-word-limit />
        </el-form-item>

        <el-form-item label="策略描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入策略描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="触发类型" prop="trigger_type">
          <el-select v-model="formData.trigger_type" placeholder="请选择触发类型" style="width: 100%">
            <el-option label="实时告警" value="realtime" />
            <el-option label="定时任务" value="scheduled" />
            <el-option label="事件驱动" value="event" />
            <el-option label="手动触发" value="manual" />
          </el-select>
        </el-form-item>

        <el-form-item label="触发条件" prop="conditions">
          <el-input
            v-model="formData.conditions"
            type="textarea"
            :rows="6"
            placeholder='请输入触发条件 JSON，例如: {"field": "severity", "op": "eq", "value": "critical"}'
          />
          <div class="form-tip">请输入合法的 JSON 格式条件表达式</div>
        </el-form-item>

        <el-form-item label="执行动作" prop="actions">
          <el-input
            v-model="formData.actions"
            type="textarea"
            :rows="6"
            placeholder='请输入执行动作，每行一个动作指令，例如: notify=email:admin@example.com'
          />
          <div class="form-tip">每行一个动作，支持通知、封禁、隔离等动作类型</div>
        </el-form-item>

        <el-form-item label="风险等级" prop="risk_level">
          <el-select v-model="formData.risk_level" placeholder="请选择风险等级" style="width: 100%">
            <el-option label="严重 (Critical)" value="critical">
              <el-tag type="danger" effect="dark" size="small">Critical</el-tag>
            </el-option>
            <el-option label="高 (High)" value="high">
              <el-tag color="#e6a23c" effect="dark" size="small" style="border-color: #e6a23c">High</el-tag>
            </el-option>
            <el-option label="中 (Medium)" value="medium">
              <el-tag type="warning" effect="dark" size="small">Medium</el-tag>
            </el-option>
            <el-option label="低 (Low)" value="low">
              <el-tag type="info" effect="dark" size="small">Low</el-tag>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="是否启用" prop="enabled">
          <el-switch
            v-model="formData.enabled"
            active-text="启用"
            inactive-text="禁用"
            inline-prompt
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">
            <el-icon><Check /></el-icon> 保存
          </el-button>
          <el-button @click="handleCancel">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- JSON Preview -->
    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <span>策略预览 (JSON)</span>
      </template>
      <pre class="json-preview">{{ previewJson }}</pre>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Check } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { policyService } from '@/shared/api'

interface PolicyForm {
  name: string
  description: string
  trigger_type: string
  conditions: string
  actions: string
  risk_level: string
  enabled: boolean
}

const route = useRoute()
const router = useRouter()

const formRef = ref<FormInstance>()
const loading = ref(false)
const saving = ref(false)

const policyId = computed(() => (route.query.id as string) || '')
const isEdit = computed(() => !!policyId.value)

const formData = reactive<PolicyForm>({
  name: '',
  description: '',
  trigger_type: '',
  conditions: '',
  actions: '',
  risk_level: '',
  enabled: true,
})

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' },
    { min: 2, max: 100, message: '名称长度在 2 到 100 个字符', trigger: 'blur' },
  ],
  description: [{ max: 500, message: '描述不能超过 500 个字符', trigger: 'blur' }],
  trigger_type: [{ required: true, message: '请选择触发类型', trigger: 'change' }],
  conditions: [
    { required: true, message: '请输入触发条件', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value) {
          try {
            JSON.parse(value)
            callback()
          } catch {
            callback(new Error('请输入合法的 JSON 格式'))
          }
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  actions: [{ required: true, message: '请输入执行动作', trigger: 'blur' }],
  risk_level: [{ required: true, message: '请选择风险等级', trigger: 'change' }],
}

const previewJson = computed(() => {
  try {
    const conditions = formData.conditions ? JSON.parse(formData.conditions) : null
    const payload = {
      name: formData.name,
      description: formData.description,
      trigger_type: formData.trigger_type,
      conditions,
      actions: formData.actions ? formData.actions.split('\n').filter(Boolean) : [],
      risk_level: formData.risk_level,
      enabled: formData.enabled,
    }
    return JSON.stringify(payload, null, 2)
  } catch {
    return '条件 JSON 解析错误'
  }
})

function buildPayload() {
  return {
    name: formData.name,
    description: formData.description,
    trigger_type: formData.trigger_type,
    conditions: formData.conditions ? JSON.parse(formData.conditions) : {},
    actions: formData.actions ? formData.actions.split('\n').filter(Boolean) : [],
    risk_level: formData.risk_level,
    enabled: formData.enabled,
  }
}

async function loadPolicy() {
  if (!policyId.value) return
  loading.value = true
  try {
    const res = await policyService.get(policyId.value)
    const data = res.data?.data ?? res.data
    formData.name = data.name ?? ''
    formData.description = data.description ?? ''
    formData.trigger_type = data.trigger_type ?? ''
    formData.conditions = data.conditions ? JSON.stringify(data.conditions, null, 2) : ''
    formData.actions = Array.isArray(data.actions) ? data.actions.join('\n') : (data.actions ?? '')
    formData.risk_level = data.risk_level ?? ''
    formData.enabled = data.enabled ?? true
  } catch (e: any) {
    ElMessage.error('加载策略失败: ' + (e.message ?? '未知错误'))
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const payload = buildPayload()
    if (isEdit.value) {
      await policyService.update(policyId.value, payload)
      ElMessage.success('策略更新成功')
    } else {
      await policyService.create(payload)
      ElMessage.success('策略创建成功')
    }
    handleBack()
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.message ?? '未知错误'))
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  ElMessageBox.confirm('确定要离开吗？未保存的更改将丢失。', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    handleBack()
  }).catch(() => {
    // cancelled
  })
}

function handleBack() {
  router.back()
}

onMounted(() => {
  loadPolicy()
})
</script>

<style scoped>
.policy-edit-page {
  padding: 16px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}
.json-preview {
  background: #f5f7fa;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 12px;
  font-size: 13px;
  line-height: 1.6;
  max-height: 400px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  color: #303133;
}
</style>
