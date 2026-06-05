<template>
  <div class="export-center-page">
    <div class="autops-page-header">
      <div class="autops-page-title-row">
        <el-button plain @click="router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <span class="autops-page-title">导出中心</span>
      </div>
      <div class="autops-page-desc">管理数据导出任务，支持多种格式和类型导出</div>
    </div>

    <!-- 导出任务列表 -->
    <el-card class="mt-4" shadow="never">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>导出任务</span>
          <el-button type="primary" size="small" @click="createExport">新建导出</el-button>
        </div>
      </template>

      <el-table stripe :data="exports" v-loading="loading"border>
        <el-table-column prop="name" label="导出名称" min-width="180" />
        <el-table-column prop="type" label="导出类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ typeLabels[row.type] || row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="format" label="格式" width="80">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.format || 'xlsx' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabels[row.status] || row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="150">
          <template #default="{ row }">
            <el-progress
              v-if="row.status === 'processing'"
              :percentage="row.progress || 0"
              :stroke-width="6"
            />
            <span v-else>{{ row.status === 'completed' ? '100%' : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="大小" width="100">
          <template #default="{ row }">{{ row.file_size ? formatSize(row.file_size) : '-' }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'completed'" plain type="primary" @click="downloadExport(row)">下载</el-button>
            <el-button v-if="row.status === 'processing'" plain type="danger" @click="cancelExport(row)">取消</el-button>
            <el-button plain type="danger" @click="deleteExport(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination class="mt-4" v-model:current-page="pagination.page" v-model:page-size="pagination.size"
        :total="pagination.total" :page-sizes="[20, 50, 100]" layout="total, sizes, prev, pager, next"
        @size-change="loadExports" @current-change="loadExports" />
    </el-card>

    <!-- 新建导出弹窗 -->
    <el-dialog v-model="dialogVisible" title="新建导出任务" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="导出名称">
          <el-input v-model="form.name" placeholder="输入导出任务名称" />
        </el-form-item>
        <el-form-item label="导出类型">
          <el-select v-model="form.type" style="width: 100%">
            <el-option label="资产列表" value="assets" />
            <el-option label="告警记录" value="alerts" />
            <el-option label="巡检结果" value="inspections" />
            <el-option label="执行记录" value="executions" />
            <el-option label="审计日志" value="audit_logs" />
            <el-option label="工单记录" value="tickets" />
          </el-select>
        </el-form-item>
        <el-form-item label="导出格式">
          <el-radio-group v-model="form.format">
            <el-radio label="xlsx">Excel</el-radio>
            <el-radio label="csv">CSV</el-radio>
            <el-radio label="json">JSON</el-radio>
            <el-radio label="pdf">PDF</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker v-model="form.dateRange" type="daterange" range-separator="至"
            start-placeholder="开始日期" end-placeholder="结束日期" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">开始导出</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const exports = ref<any[]>([])

const pagination = reactive({ page: 1, size: 20, total: 0 })
const form = reactive({ name: '', type: 'assets', format: 'xlsx', dateRange: null as any })

const typeLabels: Record<string, string> = {
  assets: '资产列表', alerts: '告警记录', inspections: '巡检结果',
  executions: '执行记录', audit_logs: '审计日志', tickets: '工单记录',
}
const statusLabels: Record<string, string> = {
  pending: '等待中', processing: '处理中', completed: '已完成', failed: '失败', cancelled: '已取消',
}
function statusType(s: string) {
  return { pending: 'warning', processing: '', completed: 'success', failed: 'danger', cancelled: 'info' }[s] || 'info'
}

function formatSize(bytes: number) {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / 1048576).toFixed(1) + 'MB'
}

async function loadExports() {
  loading.value = true
  try {
    const res = await api.get(API.EXPORTS, { params: { page: pagination.page, page_size: pagination.size } })
    const data = res.data?.data
    exports.value = data?.items || []
    pagination.total = data?.total || 0
  } catch { exports.value = [] }
  finally { loading.value = false }
}

function createExport() {
  Object.assign(form, { name: '', type: 'assets', format: 'xlsx', dateRange: null })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.name) { ElMessage.warning('请输入导出名称'); return }
  submitting.value = true
  try {
    await api.post(API.EXPORTS, form)
    ElMessage.success('导出任务已创建')
    dialogVisible.value = false
    loadExports()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '创建失败') }
  finally { submitting.value = false }
}

function downloadExport(row: any) {
  if (row.download_url) window.open(row.download_url, '_blank')
  else ElMessage.info('下载链接生成中')
}

async function cancelExport(row: any) {
  try {
    await api.post(API.EXPORT_CANCEL(row.id))
    ElMessage.success('导出已取消')
    loadExports()
  } catch { ElMessage.error('取消失败') }
}

async function deleteExport(row: any) {
  try {
    await ElMessageBox.confirm('确认删除此导出记录？', '删除确认', { type: 'warning' })
    await api.delete(API.EXPORT_DETAIL(row.id))
    ElMessage.success('已删除')
    loadExports()
  } catch { /* cancelled */ }
}

onMounted(loadExports)
</script>

<style scoped>
.export-center-page { padding: var(--autops-space-xl); }
.mt-4 { margin-top: var(--autops-space-lg); }
</style>
