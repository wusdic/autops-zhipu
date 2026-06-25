<template>
  <div class="report-template-page">
    <!-- Page Header -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">报表模板</div>
        <div class="autops-page-desc">管理报表模板，支持创建、编辑和生成报表</div>
      </div>
    </div>

    <!-- Main Card -->
    <div class="autops-card main-card">
      <div class="autops-card-header">
        <span class="autops-card-title">模板列表</span>
        <div class="card-header__actions">
          <el-button type="primary" :icon="Plus" @click="openCreateDialog">新建模板</el-button>
          <el-button :icon="Refresh" circle size="small" @click="loadTemplates" />
        </div>
      </div>
      <div class="autops-card-body">
        <!-- Filters -->
        <el-form :inline="true" class="autops-toolbar filter-form" @submit.prevent="handleSearch">
          <el-form-item label="关键词">
            <el-input
              v-model="filters.keyword"
              placeholder="搜索模板名称"
              clearable
              :prefix-icon="Search"
              style="width: 200px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="类型">
            <el-select v-model="filters.type" placeholder="全部类型" clearable style="width: 160px">
              <el-option label="巡检报告" value="inspection" />
              <el-option label="异常报告" value="anomaly" />
              <el-option label="自动化报告" value="automation" />
              <el-option label="资产报告" value="asset" />
              <el-option label="合规报告" value="compliance" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
            <el-button :icon="RefreshLeft" @click="resetFilters">重置</el-button>
          </el-form-item>
        </el-form>

        <!-- Table -->
        <el-table stripe
 :data="templates"
 v-loading="loading"border
 row-key="id"
 class="template-table"
 >
          <el-table-column prop="name" label="模板名称" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="template-name-link" @click="openEditDialog(row)">{{ row.name || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="type" label="类型" width="130" align="center">
            <template #default="{ row }">
              <el-tag :type="(typeTagType(row.type)) as TagType" size="small">{{ typeLabel(row.type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip />
          <el-table-column prop="updated_at" label="更新时间" width="170">
            <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="320" fixed="right" align="center">
            <template #default="{ row }">
              <el-button type="primary" plain size="small" @click="openPreview(row)">预览</el-button>
              <el-button type="primary" plain size="small" @click="openEditDialog(row)">编辑</el-button>
              <el-button type="success" plain size="small" @click="handleCopy(row)">复制</el-button>
              <el-button type="warning" plain size="small" @click="handleExport(row)">导出</el-button>
              <el-button type="danger" plain size="small" @click="handleDelete(row)">删除</el-button>
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
            background
            @change="loadTemplates"
          />
        </div>
      </div>
    </div>

    <!-- Create / Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑模板' : '新建模板'"
      width="600px"
      destroy-on-close
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入模板名称" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择类型" style="width: 100%">
            <el-option label="巡检报告" value="inspection" />
            <el-option label="异常报告" value="anomaly" />
            <el-option label="自动化报告" value="automation" />
            <el-option label="资产报告" value="asset" />
            <el-option label="合规报告" value="compliance" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入模板描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="报表章节">
          <el-checkbox-group v-model="form.sections">
            <el-checkbox label="概述" value="summary" />
            <el-checkbox label="资产统计" value="assets" />
            <el-checkbox label="巡检结果" value="inspection" />
            <el-checkbox label="告警汇总" value="alerts" />
            <el-checkbox label="SLA统计" value="sla" />
            <el-checkbox label="审计日志" value="audit" />
          </el-checkbox-group>
        </el-form-item>
        <el-divider content-position="left">参数配置</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="时间范围">
              <el-select v-model="form.params.timeRange" placeholder="默认时间范围" style="width: 100%">
                <el-option label="最近24小时" value="24h" />
                <el-option label="最近7天" value="7d" />
                <el-option label="最近30天" value="30d" />
                <el-option label="自定义" value="custom" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="输出格式">
              <el-select v-model="form.params.outputFormat" placeholder="输出格式" style="width: 100%">
                <el-option label="PDF" value="pdf" />
                <el-option label="Word" value="docx" />
                <el-option label="HTML" value="html" />
                <el-option label="Excel" value="xlsx" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="自动发送">
              <el-switch v-model="form.params.autoSend" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="接收人" v-if="form.params.autoSend">
              <el-input v-model="form.params.receivers" placeholder="多人用逗号分隔" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- Preview Drawer -->
    <el-drawer v-model="previewVisible" title="模板预览" size="500px" destroy-on-close>
      <template v-if="previewData">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="模板名称">{{ previewData.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag :type="(typeTagType(previewData.type)) as TagType" size="small">{{ typeLabel(previewData.type) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="描述">{{ previewData.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatTime(previewData.updated_at) }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="previewData.sections && previewData.sections.length" class="mt-lg">
          <h4 style="margin-bottom: 8px">报表章节</h4>
          <el-tag v-for="sec in previewData.sections" :key="sec" size="small" style="margin: 2px 4px">
            {{ sectionLabel(sec) }}
          </el-tag>
        </div>

        <div v-if="previewData.params" class="mt-lg">
          <h4 style="margin-bottom: 8px">参数配置</h4>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="时间范围">{{ previewData.params.timeRange || '-' }}</el-descriptions-item>
            <el-descriptions-item label="输出格式">{{ previewData.params.outputFormat || '-' }}</el-descriptions-item>
            <el-descriptions-item label="自动发送">{{ previewData.params.autoSend ? '是' : '否' }}</el-descriptions-item>
            <el-descriptions-item label="接收人" v-if="previewData.params.autoSend">{{ previewData.params.receivers || '-' }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </template>
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleGenerate(previewData)">生成报告</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Search, Refresh, RefreshLeft, Plus } from '@element-plus/icons-vue'
import { reportService } from '@/shared/api'

const router = useRouter()

// ── State ──────────────────────────────────────────────────────────
const loading = ref(false)
const templates = ref<any[]>([])
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref('')
const submitting = ref(false)
const formRef = ref<FormInstance>()
const previewVisible = ref(false)
const previewData = ref<any>(null)

const filters = reactive({
  keyword: '',
  type: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const form = reactive({
  name: '',
  type: '',
  description: '',
  sections: [] as string[],
  params: {
    timeRange: '7d',
    outputFormat: 'pdf',
    autoSend: false,
    receivers: '',
  } as Record<string, any>,
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
}

// ── Helpers ────────────────────────────────────────────────────────
function formatTime(val: string | null | undefined): string {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds())
}

function typeLabel(t: string): string {
  const map: Record<string, string> = {
    inspection: '巡检报告',
    anomaly: '异常报告',
    automation: '自动化报告',
    asset: '资产报告',
    compliance: '合规报告',
  }
  return map[t] || t || '-'
}

function typeTagType(t: string): TagType {
  const map: Record<string, string> = {
    inspection: '',
    anomaly: 'danger',
    automation: 'warning',
    asset: 'success',
    compliance: 'info',
  }
  return (map[t] || 'info') as TagType
}

function sectionLabel(s: string): string {
  const map: Record<string, string> = {
    summary: '概述',
    assets: '资产统计',
    inspection: '巡检结果',
    alerts: '告警汇总',
    sla: 'SLA统计',
    audit: '审计日志',
  }
  return map[s] || s
}

// ── Data Loading ───────────────────────────────────────────────────
async function loadTemplates() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.type) params.type = filters.type

    const { data } = await reportService.listTemplates(params)
    if (data.code === 0) {
      templates.value = data.data?.items || data.data?.list || []
      pagination.total = data.data?.total || 0
    }
  } catch (err: any) {
    ElMessage.error(err.message || '加载模板列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  loadTemplates()
}

function resetFilters() {
  filters.keyword = ''
  filters.type = ''
  pagination.page = 1
  loadTemplates()
}

// ── Dialog ─────────────────────────────────────────────────────────
function resetForm() {
  form.name = ''
  form.type = ''
  form.description = ''
  form.sections = []
  form.params = { timeRange: '7d', outputFormat: 'pdf', autoSend: false, receivers: ''}
  formRef.value?.resetFields()
}

function openCreateDialog() {
  isEditing.value = false
  editingId.value = ''
  resetForm()
  dialogVisible.value = true
}

function openEditDialog(row: any) {
  isEditing.value = true
  editingId.value = row.id
  form.name = row.name || ''
  form.type = row.type || ''
  form.description = row.description || ''
  form.sections = row.sections || []
  form.params = row.params || { timeRange: '7d', outputFormat: 'pdf', autoSend: false, receivers: ''}
  dialogVisible.value = true
}

async function submitForm() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      const payload: Record<string, any> = {
        name: form.name,
        type: form.type,
        description: form.description,
        sections: form.sections,
        params: form.params,
      }
      if (isEditing.value) {
        const { data } = await reportService.updateTemplate(editingId.value, payload)
        if (data.code === 0) {
          ElMessage.success('模板更新成功')
          dialogVisible.value = false
          loadTemplates()
        } else {
          ElMessage.error(data.message || '更新失败')
        }
      } else {
        const { data } = await reportService.createTemplate(payload)
        if (data.code === 0) {
          ElMessage.success('模板创建成功')
          dialogVisible.value = false
          loadTemplates()
        } else {
          ElMessage.error(data.message || '创建失败')
        }
      }
    } catch (err: any) {
      ElMessage.error(err.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// ── Actions ────────────────────────────────────────────────────────
async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm('确认删除模板「' + row.name + '」？此操作不可恢复。', '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    const { data } = await reportService.deleteTemplate(row.id)
    if (data.code === 0) {
      ElMessage.success('模板已删除')
      loadTemplates()
    } else {
      ElMessage.error(data.message || '删除失败')
    }
  } catch {
    // cancelled
  }
}

function handleGenerate(row: any) {
  router.push({ name: 'report-generate', query: { template_id: row.id } })
}

function openPreview(row: any) {
  previewData.value = row
  previewVisible.value = true
}

async function handleCopy(row: any) {
  try {
    const payload = {
      name: row.name + ' (副本)',
      type: row.type,
      description: row.description,
      sections: row.sections || [],
      params: row.params || {},
    }
    const { data } = await reportService.createTemplate(payload)
    if (data.code === 0) {
      ElMessage.success('模板复制成功')
      loadTemplates()
    } else {
      ElMessage.error(data.message || '复制失败')
    }
  } catch (err: any) {
    ElMessage.error(err.message || '复制失败')
  }
}

function handleExport(row: any) {
  const exportData = {
    name: row.name,
    type: row.type,
    description: row.description,
    sections: row.sections,
    params: row.params || {},
  }
  const jsonStr = JSON.stringify(exportData, null, 2)
  const blob = new Blob([jsonStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'template_' + (row.name || 'export') + '.json'
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('模板已导出')
}

// ── Lifecycle ──────────────────────────────────────────────────────
onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.report-template-page {
  padding: var(--autops-space-xl);
}

.main-card {
  border-radius: var(--autops-radius-md);
}
.filter-form {
  margin-bottom: var(--autops-space-lg);
  padding-bottom: 16px;
  border-bottom: 1px solid var(--autops-bg-4);
}

.filter-form :deep(.el-form-item) {
  margin-bottom: var(--autops-space-md);
}

.template-table {
  width: 100%;
}

.template-name-link {
  cursor: pointer;
  color: var(--autops-primary);
}

.template-name-link:hover {
  text-decoration: underline;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--autops-space-lg);
}
</style>
