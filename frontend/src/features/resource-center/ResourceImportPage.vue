<template>
  <div class="autops-page-container">
    <PageHeader title="资产导入" desc="批量导入资产数据" />

    <!-- 上传区域 -->
    <el-card shadow="never" class="upload-card">
      <template #header>
        <div class="autops-card-header">
          <span class="title">
            <el-icon><UploadFilled /></el-icon>
            资产导入
          </span>
          <el-button plain type="primary" @click="handleDownloadTemplate">
            <el-icon><Download /></el-icon>
            下载模板
          </el-button>
        </div>
      </template>

      <el-upload
        ref="uploadRef"
        class="import-uploader"
        drag
        :auto-upload="false"
        :limit="1"
        :on-change="handleFileChange"
        :on-exceed="handleExceed"
        :on-remove="handleFileRemove"
        :before-upload="beforeUpload"
        accept=".csv,.xlsx,.xls"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 CSV / Excel 文件，单次上传不超过 10MB，文件需符合导入模板格式
          </div>
        </template>
      </el-upload>

      <div class="upload-actions">
        <el-button
          type="primary"
          :icon="Upload"
          :loading="uploading"
          :disabled="!selectedFile"
          @click="handleUpload"
        >
          开始导入
        </el-button>
        <el-button @click="handleClearFile">清除文件</el-button>
      </div>

      <!-- 上传进度 -->
      <el-progress
        v-if="uploadProgress > 0 && uploadProgress < 100"
        :percentage="uploadProgress"
        :status="uploadStatus"
        class="mt-lg"
      />
    </el-card>

    <!-- 导入结果弹窗 -->
    <el-dialog v-model="resultDialogVisible" title="导入结果" width="600px" destroy-on-close>
      <template v-if="importResult">
        <el-result
          :icon="importResult.fail_count > 0 ? 'warning' : 'success'"
          :title="importResult.fail_count > 0 ? '部分导入成功' : '导入完成'"
          :sub-title="'共 ' + importResult.total + ' 条，成功 ' + importResult.success_count + ' 条，失败 ' + importResult.fail_count + ' 条'"
        />
        <el-divider v-if="importResult.errors?.length" content-position="left">错误详情</el-divider>
        <el-table stripe
          v-if="importResult.errors?.length"
          :data="importResult.errors"
          max-height="300"
          border
          size="small"
        >
          <el-table-column prop="row" label="行号" width="70" align="center" />
          <el-table-column prop="field" label="字段" width="120" />
          <el-table-column prop="message" label="错误信息" show-overflow-tooltip />
        </el-table>
      </template>
      <template #footer>
        <el-button type="primary" @click="resultDialogVisible = false">确定</el-button>
      </template>
    </el-dialog>

    <!-- 导入历史 -->
    <el-card shadow="never" class="history-card">
      <template #header>
        <div class="card-header">
          <span class="title">导入历史</span>
          <div class="actions">
            <el-input
              v-model="historyFilter.keyword"
              placeholder="搜索文件名"
              clearable
              style="width: 200px; margin-right: 8px"
              :prefix-icon="Search"
              @clear="fetchHistory"
              @keyup.enter="fetchHistory"
            />
            <el-button :icon="Refresh" @click="fetchHistory">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table stripe v-loading="historyLoading" :data="historyData" border>
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column prop="filename" label="文件名" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="filename-cell">
              <el-icon :size="16"><Document /></el-icon>
              <span>{{ row.filename }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="文件大小" width="110" align="center">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="total_count" label="记录数" width="90" align="center" />
        <el-table-column prop="success_count" label="成功" width="90" align="center">
          <template #default="{ row }">
            <el-tag type="success" size="small">{{ row.success_count ?? 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="fail_count" label="失败" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="(row.fail_count ?? 0) > 0 ? 'danger' : 'info'" size="small">
              {{ row.fail_count ?? 0 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              :type="(historyStatusMap[row.status] || 'info') as TagType"
              size="small"
              effect="dark"
            >
              {{ historyStatusLabelMap[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="导入时间" width="170" sortable>
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="operator" label="操作人" width="110" />
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" plain size="small" @click="handleViewDetail(row)">
              查看详情
            </el-button>
            <el-button
              type="success" plain
              size="small"
              @click="handleDownloadReport(row)"
            >
              下载报告
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="historyPagination.page"
          v-model:page-size="historyPagination.page_size"
          :page-sizes="[10, 20, 50]"
          :total="historyPagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="handleHistorySizeChange"
          @current-change="handleHistoryPageChange"
        />
      </div>
    </el-card>

    <!-- 历史详情弹窗 -->
    <el-dialog v-model="detailDialogVisible" title="导入详情" width="600px" destroy-on-close>
      <template v-if="detailData">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="文件名" :span="2">{{ detailData.filename }}</el-descriptions-item>
          <el-descriptions-item label="文件大小">{{ formatFileSize(detailData.file_size) }}</el-descriptions-item>
          <el-descriptions-item label="记录数">{{ detailData.total_count }}</el-descriptions-item>
          <el-descriptions-item label="成功">
            <el-tag type="success">{{ detailData.success_count ?? 0 }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="失败">
            <el-tag :type="(detailData.fail_count ?? 0) > 0 ? 'danger' : 'info'">
              {{ detailData.fail_count ?? 0 }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="导入时间" :span="2">{{ formatTime(detailData.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="操作人">{{ detailData.operator || '-' }}</el-descriptions-item>
        </el-descriptions>

        <el-divider v-if="detailData.errors?.length" content-position="left">
          错误明细 ({{ detailData.errors.length }})
        </el-divider>
        <el-table stripe
          v-if="detailData.errors?.length"
          :data="detailData.errors.slice(0, 50)"
          max-height="280"
          border
          size="small"
        >
          <el-table-column prop="row" label="行号" width="70" align="center" />
          <el-table-column prop="field" label="字段" width="120" />
          <el-table-column prop="value" label="值" width="140" show-overflow-tooltip />
          <el-table-column prop="message" label="错误信息" show-overflow-tooltip />
        </el-table>
        <div v-if="(detailData.errors?.length ?? 0) > 50" class="more-errors">
          仅展示前 50 条，共 {{ detailData.errors?.length ?? 0 }} 条错误
        </div>
      </template>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadInstance, UploadRawFile, UploadFile } from 'element-plus'
import {
  UploadFilled,
  Upload,
  Download,
  Search,
  Refresh,
  Document,
} from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import PageHeader from '@/shared/components/PageHeader.vue'
import { API } from '@/shared/api/routes'

// ─── 类型定义 ────────────────────────────────────────
interface ImportResult {
  total: number
  success_count: number
  fail_count: number
  errors?: { row: number; field: string; value?: string; message: string }[]
}

interface ImportHistory {
  id: number | string
  filename: string
  file_size: number
  total_count: number
  success_count: number
  fail_count: number
  status: string
  created_at: string
  operator: string
  errors?: { row: number; field: string; value?: string; message: string }[]
  [key: string]: unknown
}

// ─── 响应式状态 ──────────────────────────────────────
const uploadRef = ref<UploadInstance>()
const selectedFile = ref<UploadRawFile | null>(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref<'' | 'success' | 'exception' | 'warning'>('')

const resultDialogVisible = ref(false)
const importResult = ref<ImportResult | null>(null)

const historyLoading = ref(false)
const historyData = ref<ImportHistory[]>([])
const detailDialogVisible = ref(false)
const detailData = ref<ImportHistory | null>(null)

const historyFilter = reactive({ keyword: ''})
const historyPagination = reactive({ page: 1, page_size: 10, total: 0 })

// ─── 映射表 ──────────────────────────────────────────
const historyStatusMap: Record<string, TagType> = {
  pending: 'warning',
  processing: '',
  completed: 'success',
  partial: 'warning',
  failed: 'danger',
}

const historyStatusLabelMap: Record<string, string> = {
  pending: '等待中',
  processing: '处理中',
  completed: '完成',
  partial: '部分成功',
  failed: '失败',
}

// ─── 文件上传处理 ────────────────────────────────────
function handleFileChange(file: UploadFile) {
  if (file.raw) {
    selectedFile.value = file.raw
  }
}

function handleFileRemove() {
  selectedFile.value = null
  uploadProgress.value = 0
}

function handleExceed() {
  ElMessage.warning('只能上传一个文件，请先移除已选文件')
}

function handleClearFile() {
  uploadRef.value?.clearFiles()
  selectedFile.value = null
  uploadProgress.value = 0
  uploadStatus.value = ''
}

function beforeUpload(rawFile: UploadRawFile): boolean {
  const validTypes = [
    'text/csv',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
  ]
  if (!validTypes.includes(rawFile.type) && !rawFile.name.match(/\.(csv|xlsx|xls)$/i)) {
    ElMessage.error('仅支持 CSV / Excel 文件格式')
    return false
  }
  const maxSize = 10 * 1024 * 1024
  if (rawFile.size > maxSize) {
    ElMessage.error('文件大小不能超过 10MB')
    return false
  }
  return true
}

async function handleUpload() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  uploading.value = true
  uploadProgress.value = 0
  uploadStatus.value = ''

  try {
    const res = await client.post(API.ASSET_IMPORT, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e: any) => {
        if (e.total) {
          uploadProgress.value = Math.round((e.loaded * 100) / e.total)
        }
      },
    })

    const data = res.data?.data ?? res.data
    importResult.value = {
      total: data?.total ?? 0,
      success_count: data?.success_count ?? 0,
      fail_count: data?.fail_count ?? 0,
      errors: data?.errors ?? [],
    }
    uploadStatus.value = importResult.value.fail_count > 0 ? 'warning' : 'success'
    uploadProgress.value = 100
    resultDialogVisible.value = true

    ElMessage.success('文件上传成功，导入处理完成')
    handleClearFile()
    fetchHistory()
  } catch {
    uploadStatus.value = 'exception'
    uploadProgress.value = 100
    ElMessage.warning('导入功能暂不可用，请确认后端资源导入服务已启动')
  } finally {
    uploading.value = false
  }
}

// ─── 下载模板 ────────────────────────────────────────
function handleDownloadTemplate() {
  const link = document.createElement('a')
  link.href = '/templates/asset_import_template.xlsx'
  link.download = 'asset_import_template.xlsx'
  link.click()
}

// ─── 导入历史 ────────────────────────────────────────
async function fetchHistory() {
  historyLoading.value = true
  try {
    const params: Record<string, unknown> = {
      page: historyPagination.page,
      page_size: historyPagination.page_size,
    }
    if (historyFilter.keyword) params.keyword = historyFilter.keyword

    const res = await client.get(API.ASSET_IMPORT, { params })
    const data = res.data?.data ?? res.data
    if (Array.isArray(data)) {
      historyData.value = data
      historyPagination.total = data.length
    } else {
      historyData.value = data?.items ?? data?.results ?? data?.list ?? []
      historyPagination.total = data?.total ?? historyData.value.length
    }
  } catch {
    historyData.value = []
    historyPagination.total = 0
    ElMessage.warning('暂无可导入的资源数据，请先通过资源发现任务添加资源')
  } finally {
    historyLoading.value = false
  }
}

function handleHistorySizeChange(size: number) {
  historyPagination.page_size = size
  historyPagination.page = 1
  fetchHistory()
}

function handleHistoryPageChange(page: number) {
  historyPagination.page = page
  fetchHistory()
}

// ─── 查看详情 ────────────────────────────────────────
function handleViewDetail(row: any) {
  detailData.value = row
  detailDialogVisible.value = true
}

// ─── 下载报告 ────────────────────────────────────────
async function handleDownloadReport(row: any) {
  try {
    const res = await client.get(API.ASSET_IMPORT + '/' + row.id + '/report', {
      responseType: 'blob',
    })
    const blob = new Blob([res.data])
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = 'import_report_' + row.id + '.xlsx'
    link.click()
    URL.revokeObjectURL(link.href)
  } catch {
    ElMessage.error('下载报告失败')
  }
}

// ─── 工具函数 ────────────────────────────────────────
function formatTime(time: string): string {
  if (!time) return '-'
  try {
    return new Date(time).toLocaleString('zh-CN', { hour12: false })
  } catch {
    return time
  }
}

function formatFileSize(bytes: number): string {
  if (!bytes || bytes === 0) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return size.toFixed(1) + ' ' + units[i]
}

// ─── 初始化 ──────────────────────────────────────────
onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.resource-import-page {
  padding: var(--autops-space-xl);
}

.upload-card {
  margin-bottom: var(--autops-space-lg);
}

.upload-card 
.import-uploader {
  width: 100%;
}

.import-uploader :deep(.el-upload-dragger) {
  width: 100%;
}

.upload-actions {
  margin-top: var(--autops-space-lg);
  display: flex;
  gap: 8px;
}

.history-card 
.history-card .autops-card-header .actions {
  display: flex;
  align-items: center;
}

.filename-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--autops-space-lg);
  padding: var(--autops-space-xs) 0;
}

.more-errors {
  text-align: center;
  color: var(--autops-info);
  font-size: var(--autops-font-12);
  margin-top: 8px;
}
</style>
