<template>
  <div class="page-container">
    <div class="page-header">
      <h2>API Key 管理</h2>
      <el-button type="primary" @click="showCreateDialog">创建 API Key</el-button>
    </div>

    <el-table :data="apiKeys" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="name" label="名称" width="180" />
      <el-table-column label="范围" min-width="180">
        <template #default="{ row }">
          <el-tag v-for="s in (row.scopes || [])" :key="s" size="small" style="margin-right:4px">
            {{ scopeLabels[s] || s }}
          </el-tag>
          <span v-if="!row.scopes?.length" class="text-muted">—</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column prop="expires_at" label="过期时间" width="180">
        <template #default="{ row }">
          <span v-if="row.expires_at">{{ row.expires_at }}</span>
          <el-tag v-else type="info" size="small">永不过期</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Create Dialog -->
    <el-dialog v-model="dialogVisible" title="创建 API Key" width="480px">
      <el-form :model="formData" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="formData.name" placeholder="请输入 API Key 名称" />
        </el-form-item>
        <el-form-item label="范围">
          <el-checkbox-group v-model="formData.scopes">
            <el-checkbox v-for="opt in scopeOptions" :key="opt.value" :label="opt.value">
              {{ opt.label }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="过期时间">
          <el-date-picker v-model="formData.expires_at" type="datetime" placeholder="留空表示永不过期"
            style="width: 100%" value-format="YYYY-MM-DDTHH:mm:ssZ" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- Show Secret Dialog -->
    <el-dialog v-model="secretDialogVisible" title="API Key 创建成功" width="520px" :close-on-click-modal="false">
      <el-alert type="warning" :closable="false" show-icon style="margin-bottom: 16px">
        <template #title>
          请立即复制并妥善保管此密钥，关闭后将无法再次查看！
        </template>
      </el-alert>
      <el-form label-width="80px">
        <el-form-item label="名称">
          <span>{{ createdKey.name }}</span>
        </el-form-item>
        <el-form-item label="Key ID">
          <div class="secret-row">
            <code>{{ createdKey.key_id }}</code>
            <el-button size="small" @click="copyText(createdKey.key_id)">复制</el-button>
          </div>
        </el-form-item>
        <el-form-item label="密钥">
          <div class="secret-row">
            <code class="secret-value">{{ createdKey.secret }}</code>
            <el-button size="small" type="primary" @click="copyText(createdKey.secret)">复制</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" @click="secretDialogVisible = false">我已保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

const scopeOptions = [
  { value: 'asset:read', label: '资产读取' },
  { value: 'asset:write', label: '资产写入' },
  { value: 'alert:read', label: '告警读取' },
  { value: 'alert:write', label: '告警处理' },
  { value: 'event:read', label: '事件读取' },
  { value: 'policy:read', label: '策略读取' },
  { value: 'policy:write', label: '策略写入' },
  { value: 'execution:read', label: '执行读取' },
  { value: 'execution:write', label: '执行操作' },
  { value: 'admin', label: '全部管理' },
]

const scopeLabels: Record<string, string> = {}
scopeOptions.forEach(o => { scopeLabels[o.value] = o.label })

const loading = ref(false)
const saving = ref(false)
const apiKeys = ref<any[]>([])
const dialogVisible = ref(false)
const secretDialogVisible = ref(false)
const formData = reactive({
  name: '',
  scopes: [] as string[],
  expires_at: '',
})
const createdKey = reactive({
  name: '',
  key_id: '',
  secret: '',
})

async function loadApiKeys() {
  loading.value = true
  try {
    const { data } = await api.get(R.GOVERNANCE.API_KEYS)
    if (data.code === 0) {
      apiKeys.value = data.data.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载 API Key 列表失败')
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  formData.name = ''
  formData.scopes = []
  formData.expires_at = ''
  dialogVisible.value = true
}

async function handleCreate() {
  if (!formData.name) { ElMessage.warning('请输入 API Key 名称'); return }
  saving.value = true
  try {
    const payload: any = { name: formData.name, scopes: formData.scopes }
    if (formData.expires_at) payload.expires_at = formData.expires_at
    const { data } = await api.post(R.GOVERNANCE.API_KEYS, payload)
    dialogVisible.value = false
    // 创建成功，显示密钥
    const result = data.data || data
    createdKey.name = formData.name
    createdKey.key_id = result.key_id || result.id || ''
    createdKey.secret = result.secret || result.key || ''
    secretDialogVisible.value = true
    loadApiKeys()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '创建失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm(
    `确定删除 API Key「${row.name}」？删除后使用该 Key 的所有请求将被拒绝。`,
    '确认删除',
    { type: 'warning' }
  )
  try {
    await api.delete(R.GOVERNANCE.API_KEY_DETAIL(row.id))
    ElMessage.success('删除成功')
    loadApiKeys()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '删除失败')
  }
}

function copyText(text: string) {
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败，请手动选择复制')
  })
}

onMounted(() => { loadApiKeys() })
</script>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; color: #303133; }
.text-muted { color: #909399; }
.secret-row { display: flex; align-items: center; gap: 8px; width: 100%; }
.secret-row code { flex: 1; padding: 6px 10px; background: #f5f7fa; border-radius: 4px; font-size: 13px; word-break: break-all; }
.secret-value { color: #e6a23c; font-weight: bold; }
</style>
