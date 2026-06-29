<template>
  <div class="report-generate-page autops-page-container">
    <PageHeader title="生成报表" desc="选择模板与参数，快速生成运维报表" />

    <!-- Generate Form Card -->
    <div class="autops-card mb-lg">
      <div class="autops-card-header">
        <span class="autops-card-title">报表配置</span>
      </div>
      <div class="autops-card-body">
        <el-form
          ref="formRef"
          :model="form"
          :rules="formRules"
          label-width="110px"
          label-position="right"
          style="max-width: 680px"
        >
          <el-form-item label="报表模板" prop="template_id">
            <el-select
              v-model="form.template_id"
              placeholder="请选择报表模板"
              style="width: 100%"
              filterable
            >
              <el-option
                v-for="tpl in templateList"
                :key="tpl.id"
                :label="tpl.name"
                :value="tpl.id"
              >
                <span>{{ tpl.name }}</span>
                <el-tag size="small" style="margin-left: 8px">{{ typeLabel(tpl.type) }}</el-tag>
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="报表标题" prop="title">
            <el-input v-model="form.title" placeholder="输入报表标题" maxlength="200" show-word-limit />
          </el-form-item>
          <el-form-item label="时间范围" prop="date_range">
            <el-date-picker
              v-model="form.date_range"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="目标资产" prop="asset_scope">
            <el-select
              v-model="form.asset_scope"
              placeholder="选择资产范围"
              style="width: 100%"
            >
              <el-option label="全部资产" value="all" />
              <el-option label="指定资产组" value="group" />
              <el-option label="指定资产" value="specific" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="form.asset_scope === 'group'" label="资产组">
            <el-input v-model="form.asset_group" placeholder="输入资产组名称" />
          </el-form-item>
          <el-form-item v-if="form.asset_scope === 'specific'" label="资产ID">
            <el-input v-model="form.asset_ids" placeholder="输入资产ID，多个以逗号分隔" />
          </el-form-item>
          <el-form-item label="输出格式">
            <el-radio-group v-model="form.format">
              <el-radio value="pdf">PDF</el-radio>
              <el-radio value="html">HTML</el-radio>
              <el-radio value="xlsx">Excel</el-radio>
              <el-radio value="docx">Word</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="large" :loading="generating" @click="handleGenerate">
              <el-icon style="margin-right: 4px"><Document /></el-icon>
              生成报表
            </el-button>
            <el-button @click="resetForm">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- Recent Tasks Card -->
    <div class="autops-card">
      <div class="autops-card-header">
        <span class="autops-card-title">最近生成任务</span>
        <el-button plain type="primary" @click="goToTaskPage">查看全部</el-button>
      </div>
      <div class="autops-card-body p-0">
        <el-table stripe
 :data="recentTasks"
 v-loading="tasksLoading"border
 empty-text="暂无生成任务"
 class="task-table"
 >
          <el-table-column prop="title" label="报表名称" min-width="180" show-overflow-tooltip />
          <el-table-column prop="template_name" label="模板" min-width="120" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="110" align="center">
            <template #default="{ row }">
              <StatusBadge :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column prop="progress" label="进度" width="140">
            <template #default="{ row }">
              <el-progress
                :percentage="row.progress || 0"
                :status="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'exception' : undefined"
                :stroke-width="14"
                :text-inside="true"
              />
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="170">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right" align="center">
            <template #default="{ row }">
              <el-button
                type="primary" plain
                @click="previewReport(row)"
              >预览</el-button>
              <el-button
                v-if="row.status === 'completed'"
                size="small"
                plain
                @click="downloadReport(row)"
              >下载</el-button>
              <el-button
                type="warning" plain
                @click="retryTask(row)"
              >重试</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Document } from '@element-plus/icons-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import { reportService } from '@/shared/api'
import { taskStatusTag, taskStatusLabel } from '@/shared/utils/labels'

const route = useRoute()
const router = useRouter()

// ── State ──────────────────────────────────────────────────────────
const generating = ref(false)
const tasksLoading = ref(false)
const templateList = ref<any[]>([])
const recentTasks = ref<any[]>([])
const formRef = ref<FormInstance>()

const form = reactive({
  template_id: '',
  title: '',
  date_range: null as [string, string] | null,
  asset_scope: 'all',
  asset_group: '',
  asset_ids: '',
  format: 'pdf',
})

const formRules: FormRules = {
  template_id: [{ required: true, message: '请选择报表模板', trigger: 'change' }],
  title: [{ required: true, message: '请输入报表标题', trigger: 'blur' }],
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
    inspection: '巡检', anomaly: '异常', automation: '自动化', asset: '资产', compliance: '合规',
  }
  return map[t] || t || '-'
}

const statusType = (s: string): TagType => taskStatusTag(s) as TagType
const statusLabel = (s: string): string => taskStatusLabel(s)

// ── Data Loading ───────────────────────────────────────────────────
async function loadTemplates() {
  try {
    const { data } = await reportService.listTemplates({ page_size: 100 })
    if (data.code === 0) {
      templateList.value = data.data?.items || data.data?.list || []
    }
  } catch {
    // silently ignore
  }
}

async function loadRecentTasks() {
  tasksLoading.value = true
  try {
    const { data } = await reportService.listTasks({ page: 1, page_size: 5 })
    if (data.code === 0) {
      recentTasks.value = data.data?.items || data.data?.list || []
    }
  } catch {
    // silently ignore
  } finally {
    tasksLoading.value = false
  }
}

// ── Actions ────────────────────────────────────────────────────────
async function handleGenerate() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    generating.value = true
    try {
      const payload: Record<string, any> = {
        template_id: form.template_id,
        title: form.title,
        format: form.format,
      }
      if (form.date_range && form.date_range.length === 2) {
        payload.start_date = form.date_range[0]
        payload.end_date = form.date_range[1]
      }
      if (form.asset_scope === 'all') {
        payload.asset_scope = 'all'
      } else if (form.asset_scope === 'group') {
        payload.asset_scope = 'group'
        payload.asset_group = form.asset_group
      } else if (form.asset_scope === 'specific') {
        payload.asset_scope = 'specific'
        payload.asset_ids = form.asset_ids
      }

      const { data } = await reportService.generate(payload)
      if (data.code === 0) {
        ElMessage.success('报表生成任务已提交')
        loadRecentTasks()
      } else {
        ElMessage.error(data.message || '生成失败')
      }
    } catch (err: any) {
      ElMessage.error(err.message || '提交生成任务失败')
    } finally {
      generating.value = false
    }
  })
}

function resetForm() {
  form.template_id = ''
  form.title = ''
  form.date_range = null
  form.asset_scope = 'all'
  form.asset_group = ''
  form.asset_ids = ''
  form.format = 'pdf'
  formRef.value?.resetFields()
}

function previewReport(row: any) {
  router.push({ name: 'report-preview', query: { taskId: row.id } })
}

async function downloadReport(row: any) {
  try {
    const { data } = await reportService.download(row.id)
    if (data instanceof Blob) {
      const url = URL.createObjectURL(data)
      const link = document.createElement('a')
      link.href = url
      link.download = row.title || 'report' + '.' + form.format
      link.click()
      URL.revokeObjectURL(url)
    }
  } catch (err: any) {
    ElMessage.error(err.message || '下载失败')
  }
}

async function retryTask(row: any) {
  try {
    const payload: Record<string, any> = {
      template_id: row.template_id,
      title: row.title,
    }
    const { data } = await reportService.generate(payload)
    if (data.code === 0) {
      ElMessage.success('重试任务已提交')
      loadRecentTasks()
    }
  } catch (err: any) {
    ElMessage.error(err.message || '重试失败')
  }
}

function goToTaskPage() {
  router.push({ name: 'report-task' })
}

// ── Lifecycle ──────────────────────────────────────────────────────
onMounted(() => {
  // Pre-fill template_id from route query if present
  if (route.query.template_id) {
    form.template_id = route.query.template_id as string
  }
  loadTemplates()
  loadRecentTasks()
})
</script>

<style scoped>
.report-generate-page {
  padding: var(--autops-space-xl);
}



.task-table {
  width: 100%;
}
</style>
