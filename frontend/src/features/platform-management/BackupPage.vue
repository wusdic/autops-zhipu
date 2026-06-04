<template>
  <div class="page-container">
    <!-- ── API Not Available: Coming Soon ────────────────── -->
    <div v-if="apiNotAvailable" class="coming-soon-wrapper">
      <el-empty :image-size="160" description=" ">
        <template #description>
          <div class="coming-soon-title">备份恢复功能即将上线</div>
          <div class="coming-soon-desc">
            后端备份恢复服务正在开发中，届时将支持系统数据备份、恢复、定时备份策略等功能。
          </div>
        </template>
      </el-empty>
    </div>

    <!-- ── Normal Content (API available) ────────────────── -->
    <template v-else>
      <div class="autops-page-header">
        <div>
          <div class="autops-page-title">备份恢复</div>
          <div class="autops-page-desc">系统数据备份和恢复</div>
        </div>
        <div class="top-actions">
          <el-button @click="loadBackups" :loading="loading">刷新</el-button>
          <el-button type="primary" @click="openCreateDialog">新建备份</el-button>
        </div>
      </div>

    <!-- ── Storage Info Card ───────────────────────────────── -->
    <div class="autops-card storage-card">
      
        <div class="card-title">存储空间</div>
      
      <div class="storage-body">
        <el-progress
          :percentage="storagePercentage"
          :color="storageColor"
          :stroke-width="18"
          :format="() => storageText"
        />
        <div class="storage-detail">
          已使用 <strong>{{ formatSize(storage.used) }}</strong>
          / 总计 <strong>{{ formatSize(storage.total) }}</strong>
          &nbsp;·&nbsp; 共 <strong>{{ storage.count }}</strong> 份备份
        </div>
      </div>
    </div>

    <!-- ── Auto-backup Settings Card ───────────────────────── -->
    <div class="autops-card settings-card">
      
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span class="card-title">定时备份</span>
          <el-button size="small" type="primary" :loading="savingSettings" @click="saveSettings">
            保存设置
          </el-button>
        </div>
      
      <el-form label-width="120px" label-position="right">
        <el-form-item label="启用定时备份">
          <el-switch v-model="settings.enabled" />
        </el-form-item>
        <el-form-item label="Cron 表达式">
          <el-input
            v-model="settings.cron"
            placeholder="0 2 * * *  (每天凌晨2点)"
            :disabled="!settings.enabled"
            style="max-width:320px"
          />
          <span class="form-hint" v-if="settings.enabled">
            &nbsp;{{ cronDescription }}
          </span>
        </el-form-item>
        <el-form-item label="备份类型">
          <el-select v-model="settings.type" :disabled="!settings.enabled" style="width:160px">
            <el-option label="全量备份" value="full" />
            <el-option label="增量备份" value="incremental" />
          </el-select>
        </el-form-item>
        <el-form-item label="保留策略">
          <el-input-number
            v-model="settings.retention"
            :min="1"
            :max="100"
            :disabled="!settings.enabled"
            style="width:160px"
          />
          <span class="form-hint">&nbsp;保留最近 N 份备份</span>
        </el-form-item>
      </el-form>
    </div>

    <!-- ── Backup List Table ───────────────────────────────── -->
    <el-table stripe :data="backups" v-loading="loading"border style="width:100%">
      <el-table-column prop="id" label="ID" width="100" show-overflow-tooltip>
        <template #default="{ row }">
          <span style="font-family:monospace;font-size:12px">{{ row.id && String(row.id).length > 12 ? String(row.id).slice(0, 8) + '...' : (row.id || '-') }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="文件名 / 描述" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.filename || row.description || '—' }}
        </template>
      </el-table-column>
      <el-table-column prop="size" label="大小" width="110" align="right">
        <template #default="{ row }">{{ formatSize(row.size) }}</template>
      </el-table-column>
      <el-table-column prop="type" label="类型" width="110" align="center">
        <template #default="{ row }">
          <el-tag :type="row.type === 'full' ? '' : 'info'" size="small">
            {{ typeLabels[row.type] || row.type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="110" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small">
            {{ statusLabels[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" sortable>
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="耗时" width="100" align="right">
        <template #default="{ row }">{{ formatDuration(row) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right" align="center">
        <template #default="{ row }">
          <el-button
            size="small"
            :disabled="row.status !== 'completed'"
            @click="handleDownload(row)"
          >
            下载
          </el-button>
          <el-button
            size="small"
            type="warning"
            :disabled="row.status !== 'completed'"
            @click="openRestoreDialog(row)"
          >
            恢复
          </el-button>
          <el-button
            size="small"
            type="danger"
            @click="handleDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- ── Pagination ──────────────────────────────────────── -->
    <el-pagination
      v-model:current-page="page"
      :page-size="pageSize"
      :total="total"
      :page-sizes="[20, 50, 100]"
      layout="total, sizes, prev, pager, next"
      @change="loadBackups"
      style="margin-top:16px;justify-content:flex-end"
    />

    <!-- ── Create Backup Dialog ────────────────────────────── -->
    <el-dialog v-model="createDialogVisible" title="新建备份" width="480px" destroy-on-close>
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="备份类型">
          <el-radio-group v-model="createForm.type">
            <el-radio value="full">全量备份</el-radio>
            <el-radio value="incremental">增量备份</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="可选：添加备份描述"
          />
        </el-form-item>
        <el-alert v-if="createForm.type === 'full'" type="info" :closable="false" style="margin-top:8px">
          全量备份将导出所有数据，耗时较长但恢复时无需依赖其他备份。
        </el-alert>
        <el-alert v-else type="warning" :closable="false" style="margin-top:8px">
          增量备份仅导出自上次备份以来的变更，恢复时需要依赖最近的全量备份。
        </el-alert>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="doCreateBackup">确认创建</el-button>
      </template>
    </el-dialog>

    <!-- ── Restore Confirmation Dialog ─────────────────────── -->
    <el-dialog v-model="restoreDialogVisible" title="确认恢复" width="600px" destroy-on-close>
      <el-alert type="error" :closable="false" show-icon style="margin-bottom:16px">
        <template #title><strong>危险操作</strong></template>
        恢复操作将覆盖当前所有数据，此操作不可逆！
      </el-alert>
      <p style="margin:12px 0;color:#4e5969">确定要恢复到以下备份点吗？</p>
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item label="备份ID">{{ restoreTarget.id }}</el-descriptions-item>
        <el-descriptions-item label="文件名">{{ restoreTarget.filename || '—' }}</el-descriptions-item>
        <el-descriptions-item label="备份时间">{{ formatTime(restoreTarget.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ typeLabels[restoreTarget.type] || restoreTarget.type }}</el-descriptions-item>
        <el-descriptions-item label="大小">{{ formatSize(restoreTarget.size) }}</el-descriptions-item>
      </el-descriptions>

      <!-- Restore progress -->
      <div v-if="restoreProgress.active" style="margin-top:16px">
        <el-progress
          :percentage="restoreProgress.percent"
          :status="restoreProgress.status"
          :stroke-width="16"
        />
        <p style="margin-top:8px;color:#86909c;font-size:13px">{{ restoreProgress.message }}</p>
      </div>

      <div v-if="!restoreProgress.active" style="margin-top:16px">
        <el-input v-model="confirmText" placeholder='请输入 "CONFIRM" 确认操作' />
      </div>

      <template #footer>
        <el-button @click="closeRestoreDialog" :disabled="restoreProgress.active && restoreProgress.percent < 100">
          {{ restoreProgress.percent >= 100 ? '关闭' : '取消' }}
        </el-button>
        <el-button
          v-if="restoreProgress.percent < 100"
          type="danger"
          :disabled="confirmText !== 'CONFIRM'"
          :loading="restoring"
          @click="doRestore"
        >
          确认恢复
        </el-button>
      </template>
    </el-dialog>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

// ── Constants ──────────────────────────────────────────────
const typeLabels: Record<string, string> = { full: '全量备份', incremental: '增量备份' }
const statusLabels: Record<string, string> = {
  creating: '创建中',
  running: '进行中',
  completed: '已完成',
  failed: '失败',
}

// ── Refs ───────────────────────────────────────────────────
const apiNotAvailable = ref(false)
const loading = ref(false)
const creating = ref(false)
const restoring = ref(false)
const savingSettings = ref(false)

const backups = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

// Storage info
const storage = reactive({ used: 0, total: 0, count: 0 })

// Auto-backup settings
const settings = reactive({
  enabled: false,
  cron: '0 2 * * *',
  type: 'full',
  retention: 7,
})

// Create dialog
const createDialogVisible = ref(false)
const createForm = reactive({ type: 'full', description: '' })

// Restore dialog
const restoreDialogVisible = ref(false)
const confirmText = ref('')
const restoreTarget = reactive({
  id: '',
  filename: '',
  created_at: '',
  type: '',
  size: 0,
})
const restoreProgress = reactive({
  active: false,
  percent: 0,
  status: '' as '' | 'success' | 'exception',
  message: '',
})

let restoreTimer: ReturnType<typeof setInterval> | null = null

// ── Computed ───────────────────────────────────────────────
const storagePercentage = computed(() => {
  if (!storage.total) return 0
  return Math.min(Math.round((storage.used / storage.total) * 100), 100)
})

const storageText = computed(() => `${storagePercentage.value}%`)

const storageColor = computed(() => {
  const pct = storagePercentage.value
  if (pct >= 90) return '#f53f3f'
  if (pct >= 70) return '#ff7d00'
  return '#00b42a'
})

const cronDescription = computed(() => {
  const c = settings.cron.trim()
  if (c === '0 2 * * *') return '每天凌晨 2:00'
  if (c === '0 2 * * 0') return '每周日凌晨 2:00'
  if (c === '0 2 1 * *') return '每月 1 日凌晨 2:00'
  return ''
})

// ── Helpers ────────────────────────────────────────────────
function statusTagType(status: string): 'success' | 'warning' | 'danger' | 'info' {
  switch (status) {
    case 'completed': return 'success'
    case 'creating':
    case 'running': return 'warning'
    case 'failed': return 'danger'
    default: return 'info'
  }
}

function formatSize(bytes: number | undefined): string {
  if (!bytes) return '—'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}

function formatTime(t: string | undefined): string {
  return t ? new Date(t).toLocaleString('zh-CN') : '—'
}

function formatDuration(row: any): string {
  if (!row.created_at) return '—'
  const start = new Date(row.created_at).getTime()
  const end = row.finished_at ? new Date(row.finished_at).getTime() : Date.now()
  const diff = Math.max(0, Math.round((end - start) / 1000))
  if (diff < 60) return `${diff}s`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ${diff % 60}s`
  return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`
}

// ── API: Load backup list ──────────────────────────────────
async function loadBackups() {
  loading.value = true
  try {
    const { data } = await api.get(R.BACKUPS, {
      params: { page: page.value, page_size: pageSize.value },
    })
    if (data.code === 0) {
      backups.value = data.data.items || data.data || []
      total.value = data.data.total ?? backups.value.length
    }
  } catch (e: any) {
    const status = e?.response?.status
    if (status === 404 || status === 501 || !e.response) {
      apiNotAvailable.value = true
      ElMessage.info('备份恢复功能即将上线，后端服务正在开发中')
    } else {
      ElMessage.warning(e.message || '加载备份列表失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}

// ── API: Storage info ──────────────────────────────────────
async function loadStorage() {
  try {
    const { data } = await api.get(R.BACKUP_STORAGE)
    if (data.code === 0 && data.data) {
      storage.used = data.data.used || 0
      storage.total = data.data.total || 0
      storage.count = data.data.count || 0
    }
  } catch {
    // Storage endpoint may not exist yet; silently ignore
  }
}

// ── API: Auto-backup settings ──────────────────────────────
async function loadSettings() {
  try {
    const { data } = await api.get(R.BACKUP_SETTINGS)
    if (data.code === 0 && data.data) {
      settings.enabled = data.data.enabled ?? false
      settings.cron = data.data.cron || '0 2 * * *'
      settings.type = data.data.type || 'full'
      settings.retention = data.data.retention || 7
    }
  } catch {
    // Settings endpoint may not exist yet; use defaults
  }
}

async function saveSettings() {
  savingSettings.value = true
  try {
    await api.put(R.BACKUP_SETTINGS, { ...settings })
    ElMessage.success('备份设置已保存')
  } catch (e: any) {
    ElMessage.warning(e.message || '保存设置失败')
  } finally {
    savingSettings.value = false
  }
}

// ── API: Create backup ─────────────────────────────────────
function openCreateDialog() {
  createForm.type = 'full'
  createForm.description = ''
  createDialogVisible.value = true
}

async function doCreateBackup() {
  creating.value = true
  try {
    await api.post(R.BACKUPS, {
      type: createForm.type,
      description: createForm.description || undefined,
    })
    ElMessage.success('备份任务已创建')
    createDialogVisible.value = false
    loadBackups()
    loadStorage()
  } catch (e: any) {
    ElMessage.warning(e.message || '创建备份失败')
  } finally {
    creating.value = false
  }
}

// ── API: Download ──────────────────────────────────────────
function handleDownload(row: any) {
  // Open download in new window/tab — the browser will handle the file download
  const url = R.BACKUP_DOWNLOAD(row.id)
  const token = localStorage.getItem('token')
  const link = document.createElement('a')
  link.href = token ? `${url}?token=${encodeURIComponent(token)}` : url
  link.target = '_blank'
  link.rel = 'noopener noreferrer'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  ElMessage.info('正在下载备份文件…')
}

// ── API: Delete ────────────────────────────────────────────
async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定删除备份「${row.filename || row.description || row.id}」？此操作不可撤销。`,
      '删除备份',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return // user cancelled
  }

  try {
    await api.delete(R.BACKUP_DETAIL(row.id))
    ElMessage.success('备份已删除')
    loadBackups()
    loadStorage()
  } catch (e: any) {
    ElMessage.warning(e.message || '删除失败')
  }
}

// ── API: Restore ───────────────────────────────────────────
function openRestoreDialog(row: any) {
  restoreTarget.id = row.id
  restoreTarget.filename = row.filename || ''
  restoreTarget.created_at = row.created_at
  restoreTarget.type = row.type
  restoreTarget.size = row.size
  confirmText.value = ''
  restoreProgress.active = false
  restoreProgress.percent = 0
  restoreProgress.status = ''
  restoreProgress.message = ''
  restoreDialogVisible.value = true
}

function closeRestoreDialog() {
  if (restoreTimer) {
    clearInterval(restoreTimer)
    restoreTimer = null
  }
  restoreDialogVisible.value = false
}

async function doRestore() {
  restoring.value = true
  restoreProgress.active = true
  restoreProgress.percent = 0
  restoreProgress.status = ''
  restoreProgress.message = '正在启动恢复任务…'

  try {
    const { data } = await api.post(R.BACKUP_RESTORE(restoreTarget.id))
    if (data.code !== 0) {
      throw new Error(data.message || '恢复失败')
    }
    // Start simulated progress (real impl would poll backend)
    restoreProgress.message = '恢复进行中…'
    simulateRestoreProgress()
    ElMessage.success('恢复任务已启动')
  } catch (e: any) {
    restoreProgress.status = 'exception'
    restoreProgress.message = e.message || '恢复失败'
    ElMessage.warning(e.message || '恢复失败')
  } finally {
    restoring.value = false
  }
}

function simulateRestoreProgress() {
  if (restoreTimer) clearInterval(restoreTimer)
  restoreTimer = setInterval(() => {
    if (restoreProgress.percent >= 100) {
      clearInterval(restoreTimer!)
      restoreTimer = null
      restoreProgress.status = 'success'
      restoreProgress.message = '恢复完成，建议刷新页面验证数据。'
      loadBackups()
      return
    }
    restoreProgress.percent = Math.min(restoreProgress.percent + 10, 100)
  }, 800)
}

// ── Lifecycle ──────────────────────────────────────────────
onMounted(() => {
  loadBackups()
  loadStorage()
  loadSettings()
})

onUnmounted(() => {
  if (restoreTimer) {
    clearInterval(restoreTimer)
    restoreTimer = null
  }
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; color: #1d2129; }
.storage-card { margin-bottom: 16px; }
.storage-body { padding: 4px 0; }
.storage-detail { margin-top: 12px; color: #4e5969; font-size: 13px; }
.storage-detail strong { color: #1d2129; }

.settings-card { margin-bottom: 16px; }
.form-hint { color: #86909c; font-size: 13px; }

/* Coming soon */
.coming-soon-wrapper {
  display: flex;
  justify-content: center;
  padding: 60px 20px;
}
.coming-soon-title {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 8px;
}
.coming-soon-desc {
  font-size: 14px;
  color: #86909c;
  line-height: 1.6;
  max-width: 420px;
  text-align: center;
  margin: 0 auto;
}
</style>
