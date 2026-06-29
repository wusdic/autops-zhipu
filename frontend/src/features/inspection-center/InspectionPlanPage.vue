<template>
  <div class="autops-page-container">
    <!-- 页面头部 -->
    <div class="autops-page-header">
      <div class="autops-page-title">巡检计划</div>
      <div class="autops-page-desc">创建和管理巡检计划，设置调度周期</div>
    </div>
    <!-- 搜索栏 -->
    <div class="autops-toolbar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索计划名称..."
        clearable
        style="width: 260px"
        @keyup.enter="fetchPlans"
        @clear="fetchPlans"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="enabledFilter" placeholder="状态筛选" clearable style="width: 130px" @change="fetchPlans">
        <el-option label="已启用" :value="true" />
        <el-option label="已禁用" :value="false" />
      </el-select>
      <el-button type="default" @click="fetchPlans">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
      <el-button text type="primary" @click="goConfig('/config/inspection-rules')">
        <el-icon><Setting /></el-icon> 配置巡检规则
      </el-button>
      <el-button text type="primary" @click="goConfig('/inspection/templates')">
        <el-icon><Setting /></el-icon> 巡检模板
      </el-button>
    </div>

    <!-- 数据表格 -->
    <el-table stripe :data="plans" v-loading="loading"empty-text="暂无巡检计划">
      <el-table-column prop="name" label="计划名称" min-width="180" show-overflow-tooltip />
      <el-table-column prop="template_name" label="关联模板" width="160" show-overflow-tooltip>
        <template #default="{ row }">
          <span>{{ row.template_name || getTemplateName(row.template_id) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="cron" label="执行周期" width="140">
        <template #default="{ row }">
          <span class="cron-text">{{ row.cron }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="cron_description" label="周期说明" width="130">
        <template #default="{ row }">
          <span class="text-tertiary">{{ row.cron_description || parseCron(row.cron) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="next_run" label="下次执行" width="170">
        <template #default="{ row }">
          <span class="text-tertiary">{{ row.next_run || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="enabled" label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
            {{ row.enabled ? '已启用' : '已禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">
          <span class="text-tertiary">{{ row.created_at || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button plain type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button plain type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="page-pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="fetchPlans"
        @current-change="fetchPlans"
      />
    </div>

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑计划' : '新建计划'"
      width="600px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="计划名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入计划名称" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="关联模板" prop="template_id">
          <el-select
            v-model="form.template_id"
            placeholder="请选择巡检模板"
            style="width: 100%"
            filterable
            :loading="templateLoading"
          >
            <el-option
              v-for="tpl in templateOptions"
              :key="tpl.id"
              :label="tpl.name"
              :value="tpl.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="执行周期" prop="cron">
          <el-input v-model="form.cron" placeholder="Cron 表达式，如: 0 8 * * *">
            <template #append>
              <el-tooltip content="Cron 表达式格式: 分 时 日 月 周&#10;示例:&#10;0 8 * * * 每天 8:00&#10;0 */2 * * * 每 2 小时&#10;0 0 * * 1 每周一 0:00" placement="top">
                <el-icon><QuestionFilled /></el-icon>
              </el-tooltip>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="周期预览">
          <span class="cron-preview">{{ parseCron(form.cron) || '请输入 Cron 表达式' }}</span>
        </el-form-item>
        <el-form-item label="是否启用" prop="enabled">
          <el-switch v-model="form.enabled" active-text="启用" inactive-text="禁用" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入计划描述（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Plus, Search, Refresh, QuestionFilled, Setting } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { inspectionService } from '@/shared/api'

const router = useRouter()
function goConfig(path: string) { router.push(path) }

// ---------- 状态 ----------
const loading = ref(false)
const submitLoading = ref(false)
const templateLoading = ref(false)
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref<string>('')
const plans = ref<any[]>([])
const searchQuery = ref('')
const enabledFilter = ref<boolean | string>('')
const templateOptions = ref<any[]>([])
const formRef = ref<FormInstance>()

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

const form = reactive({
  name: '',
  template_id: '',
  cron: '0 8 * * *',
  enabled: true,
  description: '',
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入计划名称', trigger: 'blur' }],
  template_id: [{ required: true, message: '请选择关联模板', trigger: 'change' }],
  cron: [{ required: true, message: '请输入 Cron 表达式', trigger: 'blur' }],
}

// ---------- 工具函数 ----------
function getTemplateName(templateId: string) {
  if (!templateId) return '-'
  const tpl = templateOptions.value.find(t => t.id === templateId)
  return tpl ? tpl.name : templateId
}

function parseCron(cron: string) {
  if (!cron) return ''
  const parts = cron.trim().split(/\s+/)
  if (parts.length < 5) return '无效表达式'

  const [minute, hour, dayOfMonth, month, dayOfWeek] = parts

  // 每天
  if (dayOfMonth === '*' && month === '*' && dayOfWeek === '*') {
    if (hour.startsWith('*/')) {
      return '每 ' + hour.slice(2) + ' 小时执行'
    }
    return '每天 ' + hour + ':' + minute.padStart(2, '0') + ' 执行'
  }
  // 每周
  if (dayOfWeek !== '*' && dayOfMonth === '*' && month === '*') {
    const weekDayMap: Record<string, string> = {
      '0': '周日', '1': '周一', '2': '周二', '3': '周三',
      '4': '周四', '5': '周五', '6': '周六', '7': '周日',
    }
    return '每' + weekDayMap[dayOfWeek] || '周' + dayOfWeek + ' ' + hour + ':' + minute.padStart(2, '0') + ' 执行'
  }
  // 每月
  if (dayOfMonth !== '*' && month === '*' && dayOfWeek === '*') {
    return '每月 ' + dayOfMonth + ' 日 ' + hour + ':' + minute.padStart(2, '0') + ' 执行'
  }
  return 'Cron: ' + cron
}

// ---------- API ----------
async function fetchPlans() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.page_size,
    }
    if (searchQuery.value.trim()) {
      params.name = searchQuery.value.trim()
    }
    if (enabledFilter.value !== '' && enabledFilter.value !== null) {
      params.enabled = enabledFilter.value
    }
    const res = await inspectionService.listPlans(params)
    const data = res.data?.data ?? res.data
    plans.value = data?.items ?? data ?? []
    pagination.total = data?.total ?? plans.value.length
  } catch (err: any) {
    ElMessage.error(err.message || '获取计划列表失败')
  } finally {
    loading.value = false
  }
}

async function fetchTemplates() {
  templateLoading.value = true
  try {
    const res = await inspectionService.listTemplates({ page_size: 200 })
    const data = res.data?.data ?? res.data
    templateOptions.value = data?.items ?? data ?? []
  } catch {
    templateOptions.value = []
  } finally {
    templateLoading.value = false
  }
}

async function createPlan(data: Record<string, any>) {
  return inspectionService.createPlan(data)
}

async function updatePlan(id: string, data: Record<string, any>) {
  return inspectionService.updatePlan(id, data)
}

async function deletePlan(id: string) {
  return inspectionService.deletePlan(id)
}

// ---------- 操作 ----------
function handleCreate() {
  isEditing.value = false
  editingId.value = ''
  form.enabled = true
  form.cron = '0 8 * * *'
  dialogVisible.value = true
}

function handleEdit(row: any) {
  isEditing.value = true
  editingId.value = row.id
  form.name = row.name || ''
  form.template_id = row.template_id || ''
  form.cron = row.cron || '0 8 * * *'
  form.enabled = row.enabled !== false
  form.description = row.description || ''
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    const payload = {
      name: form.name,
      template_id: form.template_id,
      cron: form.cron,
      enabled: form.enabled,
      description: form.description,
    }
    if (isEditing.value) {
      await updatePlan(editingId.value, payload)
      ElMessage.success('计划更新成功')
    } else {
      await createPlan(payload)
      ElMessage.success('计划创建成功')
    }
    dialogVisible.value = false
    fetchPlans()
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(
      '确定要删除计划「' + row.name + '」吗？此操作不可恢复。',
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await deletePlan(row.id)
    ElMessage.success('计划已删除')
    fetchPlans()
  } catch (err: any) {
    if (err !== 'cancel' && err?.action !== 'cancel' && err?.message !== 'cancel') {
      ElMessage.error(err.message || '删除失败')
    }
  }
}

function resetForm() {
  form.name = ''
  form.template_id = ''
  form.cron = '0 8 * * *'
  form.enabled = true
  form.description = ''
  isEditing.value = false
  editingId.value = ''
  formRef.value?.resetFields()
}

// ---------- 初始化 ----------
onMounted(() => {
  fetchPlans()
  fetchTemplates()
})
</script>

<style scoped>

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--autops-space-lg);
}

.page-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: var(--autops-space-lg);
}
.page-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--autops-space-lg);
}
.text-tertiary {
  color: var(--autops-info);
  font-size: var(--autops-font-13);
}
.cron-text {
  font-family: 'Courier New', Courier, monospace;
  font-size: var(--autops-font-13);
  background: var(--autops-bg-3);
  padding: 2px 6px;
  border-radius: var(--autops-radius-sm);
}
.cron-preview {
  color: var(--autops-info);
  font-size: var(--autops-font-13);
}
</style>
