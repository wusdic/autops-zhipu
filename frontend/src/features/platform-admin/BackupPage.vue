<template>
  <div class="page-container">
    <div class="page-header">
      <h2>备份恢复</h2>
      <div class="header-actions">
        <el-button @click="loadBackups" :loading="loading">刷新</el-button>
        <el-button type="primary" @click="handleCreateBackup" :loading="creating">新建备份</el-button>
      </div>
    </div>

    <el-table :data="backups" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="created_at" label="备份时间" width="180" />
      <el-table-column prop="size" label="大小" width="120">
        <template #default="{ row }">
          {{ formatSize(row.size) }}
        </template>
      </el-table-column>
      <el-table-column prop="type" label="类型" width="120">
        <template #default="{ row }">
          <el-tag :type="row.type === 'full' ? '' : 'info'" size="small">
            {{ typeLabels[row.type] || row.type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small">
            {{ statusLabels[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="备注" min-width="200" />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button
            size="small"
            type="warning"
            :disabled="row.status !== 'completed'"
            @click="handleRestore(row)"
          >
            恢复
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Restore Confirmation Dialog -->
    <el-dialog v-model="restoreDialogVisible" title="确认恢复" width="460px">
      <el-alert type="error" :closable="false" show-icon style="margin-bottom: 16px">
        <template #title>
          <strong>危险操作</strong>
        </template>
        恢复操作将覆盖当前所有数据，此操作不可逆！
      </el-alert>
      <p style="margin: 12px 0; color: #606266;">
        确定要恢复到以下备份点吗？
      </p>
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item label="备份时间">{{ restoreTarget.created_at }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ typeLabels[restoreTarget.type] || restoreTarget.type }}</el-descriptions-item>
        <el-descriptions-item label="大小">{{ formatSize(restoreTarget.size) }}</el-descriptions-item>
      </el-descriptions>
      <div style="margin-top: 16px;">
        <el-input v-model="confirmText" placeholder='请输入 "CONFIRM" 确认操作' />
      </div>
      <template #footer>
        <el-button @click="restoreDialogVisible = false">取消</el-button>
        <el-button type="danger" :disabled="confirmText !== 'CONFIRM'" :loading="restoring" @click="doRestore">
          确认恢复
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

// NOTE: 后端暂无备份 API，页面先做 UI 框架，API 调用使用 try/catch 空处理

const typeLabels: Record<string, string> = { full: '全量备份', incremental: '增量备份' }
const statusLabels: Record<string, string> = { completed: '已完成', running: '进行中', failed: '失败' }

const loading = ref(false)
const creating = ref(false)
const restoring = ref(false)
const backups = ref<any[]>([])
const restoreDialogVisible = ref(false)
const confirmText = ref('')
const restoreTarget = reactive({
  id: '',
  created_at: '',
  type: '',
  size: 0,
})

function statusTagType(status: string): 'success' | 'warning' | 'danger' | 'info' {
  switch (status) {
    case 'completed': return 'success'
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

async function loadBackups() {
  loading.value = true
  try {
    // TODO: 替换为实际备份 API 路由常量
    const { data } = await api.get(R.BACKUPS)
    if (data.code === 0) {
      backups.value = data.data.items || data.data || []
    }
  } catch {
    // 后端暂无备份 API，忽略错误
  } finally {
    loading.value = false
  }
}

async function handleCreateBackup() {
  await ElMessageBox.confirm('确定创建一份新的全量备份？', '新建备份', { type: 'info' })
  creating.value = true
  try {
    // TODO: 替换为实际备份 API 路由常量
    await api.post(R.BACKUPS, { type: 'full' })
    ElMessage.success('备份任务已创建')
    loadBackups()
  } catch {
    // 后端暂无备份 API，忽略错误
    ElMessage.warning('备份功能暂未接入后端')
  } finally {
    creating.value = false
  }
}

function handleRestore(row: any) {
  restoreTarget.id = row.id
  restoreTarget.created_at = row.created_at
  restoreTarget.type = row.type
  restoreTarget.size = row.size
  confirmText.value = ''
  restoreDialogVisible.value = true
}

async function doRestore() {
  restoring.value = true
  try {
    // TODO: 替换为实际备份 API 路由常量
    await api.post(R.BACKUP_RESTORE(restoreTarget.id))
    ElMessage.success('恢复任务已启动')
    restoreDialogVisible.value = false
    loadBackups()
  } catch {
    // 后端暂无备份 API，忽略错误
    ElMessage.warning('恢复功能暂未接入后端')
  } finally {
    restoring.value = false
  }
}

onMounted(() => { loadBackups() })
</script>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; color: #303133; }
.header-actions { display: flex; gap: 8px; }
</style>
