<template>
  <div class="autops-page-container">
    <PageHeader title="Prompt 模板管理" desc="管理 AI 提示词模板">
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="openCreate">新建模板</el-button>
      </template>
    </PageHeader>

    <!-- Search & Filters -->
    <div class="autops-card filter-card">
      <el-row :gutter="16" align="middle">
        <el-col :span="8">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索模板名称..."
            :prefix-icon="Search"
            clearable
            @clear="loadList"
            @keyup.enter="loadList"
          />
        </el-col>
        <el-col :span="5">
          <el-select v-model="filters.usage" placeholder="用途筛选" clearable @change="loadList" style="width: 100%">
            <el-option label="根因诊断" value="diagnosis" />
            <el-option label="处置建议" value="remediation" />
            <el-option label="摘要生成" value="summary" />
            <el-option label="日志分析" value="log_analysis" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="loadList">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-col>
      </el-row>
    </div>

    <!-- Template Table -->
    <div class="autops-card mt-lg">
      <el-table stripe
 v-loading="loading"
 :data="tableData"style="width: 100%"
 >
        <el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="template-name" @click="openEdit(row)">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column label="用途" width="130">
          <template #default="{ row }">
            <el-tag :type="(usageTagType(row.usage)) as TagType" size="small">
              {{ usageLabel(row.usage) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model" label="模型" width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ row.model || '通用' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="170">
          <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="版本" width="70" align="center">
          <template #default="{ row }">v{{ row.version || 1 }}</template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button plain type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button plain size="small" @click="testTemplate(row)">测试</el-button>
            <el-button plain type="primary" size="small" @click="duplicateTemplate(row)">复制</el-button>
            <el-button plain type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadList"
          @current-change="loadList"
        />
      </div>
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑模板' : '新建模板'"
      width="780px"
      destroy-on-close
      @close="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="模板名称" prop="name">
              <el-input v-model="form.name" placeholder="输入模板名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="用途" prop="usage">
              <el-select v-model="form.usage" placeholder="选择用途" style="width: 100%">
                <el-option label="根因诊断" value="diagnosis" />
                <el-option label="处置建议" value="remediation" />
                <el-option label="摘要生成" value="summary" />
                <el-option label="日志分析" value="log_analysis" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="适用模型">
              <el-input v-model="form.model" placeholder="留空表示通用" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="温度参数">
              <el-slider v-model="form.temperature" :min="0" :max="200" :step="10" show-input />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="System Prompt" prop="system_prompt">
          <el-input
            type="textarea"
            v-model="form.system_prompt"
            :rows="4"
            placeholder="输入 System Prompt 内容"
          />
        </el-form-item>
        <el-form-item label="User Prompt" prop="user_prompt">
          <el-input
            type="textarea"
            v-model="form.user_prompt"
            :rows="8"
            placeholder="输入 User Prompt 内容，可使用 {{variable}} 作为变量占位符"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="模板说明（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- Test Dialog -->
    <el-dialog v-model="testDialogVisible" title="测试 Prompt 模板" width="780px" destroy-on-close>
      <el-form label-width="100px">
        <el-form-item label="模板名称">
          <el-input :model-value="testTemplateData.name" disabled />
        </el-form-item>
        <el-form-item label="测试输入">
          <el-input
            type="textarea"
            v-model="testInput"
            :rows="4"
            placeholder="输入测试参数（JSON 格式）"
          />
        </el-form-item>
        <el-form-item v-if="testResult" label="测试结果">
          <div class="test-result">{{ testResult }}</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="testDialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="testing" @click="runTest">执行测试</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { Plus, Search, Notebook } from '@element-plus/icons-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

// ─── State ───────────────────────────────────────────────────────────
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const dialogVisible = ref(false)
const testDialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref('')

const tableData = ref<any[]>([])
const testInput = ref('{\n  "alert_name": "CPU使用率过高",\n  "host": "server-01"\n}')
const testResult = ref('')
const testTemplateData = reactive<any>({})

const filters = reactive({
  keyword: '',
  usage: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  usage: '',
  model: '',
  temperature: 70,
  system_prompt: '',
  user_prompt: '',
  description: '',
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  usage: [{ required: true, message: '请选择用途', trigger: 'change' }],
  system_prompt: [{ required: true, message: '请输入 System Prompt', trigger: 'blur' }],
  user_prompt: [{ required: true, message: '请输入 User Prompt', trigger: 'blur' }],
}

// ─── Helpers ─────────────────────────────────────────────────────────
function usageLabel(usage: string): string {
  const map: Record<string, string> = {
    diagnosis: '根因诊断',
    remediation: '处置建议',
    summary: '摘要生成',
    log_analysis: '日志分析',
  }
  return map[usage] || usage || '-'
}

function usageTagType(usage: string): TagType {
  const map: Record<string, string> = {
    diagnosis: 'danger',
    remediation: 'warning',
    summary: 'success',
    log_analysis: '',
  }
  return (map[usage] ?? undefined) as TagType
}

function formatTime(t: string): string {
  return t ? new Date(t).toLocaleString('zh-CN') : '-'
}

// ─── Data Loading ────────────────────────────────────────────────────
async function loadList() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.usage) params.usage = filters.usage

    const { data } = await client.get(API.AIOPS.PROMPT_TEMPLATES, { params })
    if (data.code === 0) {
      const result = data.data
      tableData.value = result.items || result || []
      pagination.total = result.total || tableData.value.length
    }
  } catch (e: any) {
    ElMessage.error('加载模板列表失败: ' + (e.message || e))
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.keyword = ''
  filters.usage = ''
  pagination.page = 1
  loadList()
}

// ─── CRUD ────────────────────────────────────────────────────────────
function openCreate() {
  isEditing.value = false
  editingId.value = ''
  Object.assign(form, {
    name: '',
    usage: '',
    model: '',
    temperature: 70,
    system_prompt: '',
    user_prompt: '',
    description: '',
  })
  dialogVisible.value = true
}

function openEdit(row: any) {
  isEditing.value = true
  editingId.value = row.id
  Object.assign(form, {
    name: row.name || '',
    usage: row.usage || '',
    model: row.model || '',
    temperature: row.temperature ?? 70,
    system_prompt: row.system_prompt || '',
    user_prompt: row.user_prompt || '',
    description: row.description || '',
  })
  dialogVisible.value = true
}

async function handleSave() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const payload = { ...form }
    let res: any
    if (isEditing.value) {
      res = await client.put(API.AIOPS.PROMPT_TEMPLATE_DETAIL(editingId.value), payload)
    } else {
      res = await client.post(API.AIOPS.PROMPT_TEMPLATES, payload)
    }
    if (res.data.code === 0) {
      ElMessage.success(isEditing.value ? '模板已更新' : '模板已创建')
      dialogVisible.value = false
      loadList()
    } else {
      ElMessage.error(res.data.message || '保存失败')
    }
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.message || e))
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(
      '确定删除模板「' + row.name + '」？此操作不可撤销。',
      '确认删除',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }
    )
    const { data } = await client.delete(API.AIOPS.PROMPT_TEMPLATE_DETAIL(row.id))
    if (data.code === 0) {
      ElMessage.success('已删除')
      loadList()
    } else {
      ElMessage.error(data.message || '删除失败')
    }
  } catch {
    // cancelled
  }
}

function duplicateTemplate(row: any) {
  isEditing.value = false
  editingId.value = ''
  Object.assign(form, {
    name: row.name + ' (副本)',
    usage: row.usage || '',
    model: row.model || '',
    temperature: row.temperature ?? 70,
    system_prompt: row.system_prompt || '',
    user_prompt: row.user_prompt || '',
    description: row.description || '',
  })
  dialogVisible.value = true
}

// ─── Test ────────────────────────────────────────────────────────────
function testTemplate(row: any) {
  Object.assign(testTemplateData, row)
  testInput.value = '{\n  "alert_name": "CPU使用率过高",\n  "host": "server-01"\n}'
  testResult.value = ''
  testDialogVisible.value = true
}

async function runTest() {
  testing.value = true
  testResult.value = ''
  try {
    let variables: Record<string, any> = {}
    try {
      variables = JSON.parse(testInput.value)
    } catch {
      ElMessage.warning('测试输入必须是有效的 JSON 格式')
      testing.value = false
      return
    }

    const { data } = await client.post(API.AIOPS.PROMPT_TEMPLATE_TEST(testTemplateData.id), { variables })
    if (data.code === 0) {
      testResult.value = data.data?.output || data.data?.result || JSON.stringify(data.data, null, 2)
    } else {
      testResult.value = '错误: ' + data.message || '测试失败'
    }
  } catch (e: any) {
    testResult.value = '错误: ' + e.message || e
  } finally {
    testing.value = false
  }
}

function resetForm() {
  formRef.value?.resetFields()
}

// ─── Init ────────────────────────────────────────────────────────────
onMounted(() => {
  loadList()
})
</script>

<style scoped>
.prompt-template-page {
  padding: 0;
}
.autops-page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--autops-space-lg);
}
.top-actions {
  display: flex;
  gap: 8px;
}
.filter-card {
  margin-bottom: 0;
}
.template-name {
  color: var(--autops-primary);
  cursor: pointer;
  font-weight: 500;
}
.template-name:hover {
  text-decoration: underline;
}
.pagination-wrapper {
  margin-top: var(--autops-space-lg);
  display: flex;
  justify-content: flex-end;
}
.test-result {
  background: var(--autops-bg-2);
  padding: var(--autops-space-md);
  border-radius: 6px;
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: var(--autops-font-13);
  font-family: monospace;
  max-height: 300px;
  overflow: auto;
}
</style>
