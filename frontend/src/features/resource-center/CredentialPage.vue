<template>
  <div class="credential-page">
    <!-- 页面头部 -->
    <div class="autops-page-header">
      <span class="autops-page-title">凭证库</span>
      <div class="autops-toolbar-right">
        <el-button type="primary" @click="openCreateDialog" :icon="Plus">新建凭证</el-button>
      </div>
    </div>

    <div class="autops-card">
      <div class="autops-card-body">

      <!-- 筛选 -->
      <el-form :inline="true" class="autops-toolbar">
        <el-form-item label="类型">
          <el-select v-model="filters.credential_type" placeholder="全部" clearable @change="loadCredentials">
            <el-option label="SSH 密码" value="ssh_password" />
            <el-option label="SSH 密钥" value="ssh_key" />
            <el-option label="SNMP" value="snmp" />
            <el-option label="Windows" value="windows" />
            <el-option label="数据库" value="database" />
            <el-option label="API Token" value="api_token" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input v-model="filters.search" placeholder="凭证名称" clearable @clear="loadCredentials" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadCredentials">查询</el-button>
        </el-form-item>
      </el-form>

      <!-- 凭证列表 -->
      <el-table stripe :data="credentials" v-loading="loading">
        <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="credential_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ formatCredentialType(row.credential_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" width="130" show-overflow-tooltip />
        <el-table-column prop="password" label="密码/密钥" width="130">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:4px">
              <span v-if="!row._showSecret">{{ maskSecret(row) }}</span>
              <span v-else style="font-family:monospace;font-size:12px">{{ row.password || row.secret || row.token || '-' }}</span>
              <el-button plain size="small" @click="toggleSecret(row)">
                <el-icon><View v-if="!row._showSecret" /><Hide v-else /></el-icon>
              </el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="bind_count" label="绑定资产" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.bind_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="140" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openBindDialog(row)">绑定</el-button>
            <el-button size="small" type="warning" @click="openEditDialog(row)">编辑</el-button>
            <el-popconfirm title="确认删除此凭证?" @confirm="deleteCredential(row.id)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && !credentials.length" description="暂无凭证" />

      <el-pagination
        v-if="pagination.total > 0"
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @change="loadCredentials"
      />
      </div>
    </div>

    <!-- 创建/编辑凭证弹窗 -->
    <el-dialog v-model="showFormDialog" :title="isEditing ? '编辑凭证' : '新建凭证'" width="600px">
      <el-form :model="formData" label-width="90px" ref="formRef" :rules="formRules">
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="凭证名称" />
        </el-form-item>
        <el-form-item label="类型" prop="credential_type">
          <el-select v-model="formData.credential_type" style="width: 100%" @change="onTypeChange">
            <el-option label="SSH 密码" value="ssh_password" />
            <el-option label="SSH 密钥" value="ssh_key" />
            <el-option label="SNMP" value="snmp" />
            <el-option label="Windows" value="windows" />
            <el-option label="数据库" value="database" />
            <el-option label="API Token" value="api_token" />
          </el-select>
        </el-form-item>
        <el-form-item label="用户名" prop="username" v-if="showUsername">
          <el-input v-model="formData.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="showPassword">
          <el-input v-model="formData.password" type="password" show-password placeholder="密码" />
        </el-form-item>
        <el-form-item label="私钥" prop="secret" v-if="formData.credential_type === 'ssh_key'">
          <el-input v-model="formData.secret" type="textarea" :rows="4" placeholder="粘贴SSH私钥内容" />
        </el-form-item>
        <el-form-item label="Token" prop="token" v-if="formData.credential_type === 'api_token'">
          <el-input v-model="formData.token" type="textarea" :rows="2" placeholder="API Token" />
        </el-form-item>
        <el-form-item label="端口">
          <el-input-number v-model="formData.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="2" placeholder="描述(可选)" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button type="primary" @click="saveCredential" :loading="saving">{{ isEditing ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>

    <!-- 绑定资产弹窗 -->
    <el-dialog v-model="showBindDialog" title="绑定凭证到资产" width="600px">
      <p style="margin-bottom:12px;color:#4e5969">
        将凭证 <strong>{{ bindingCredential?.name }}</strong> 绑定到以下资产:
      </p>

      <!-- 已绑定的资产 -->
      <div v-if="boundAssets.length" class="mb-lg">
        <h4 style="font-size:13px;color:#86909c;margin-bottom:8px">已绑定资产</h4>
        <el-table stripe :data="boundAssets" size="small"max-height="200">
          <el-table-column prop="name" label="名称" min-width="130" />
          <el-table-column prop="ip" label="IP" width="140" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button size="small" plain type="danger" @click="unbindAsset(row.id)">解绑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 选择资产绑定 -->
      <h4 style="font-size:13px;color:#86909c;margin-bottom:8px">添加绑定</h4>
      <el-input
        v-model="bindAssetSearch"
        placeholder="搜索资产名称或IP"
        clearable
        style="margin-bottom: 8px"
        :prefix-icon="Search"
        @input="searchBindAssets"
      />
      <el-table stripe
        :data="bindAvailableAssets"
        v-loading="bindAssetLoading"
        size="small"
        max-height="250"
        @selection-change="handleBindSelection"
      >
        <el-table-column type="selection" width="45" />
        <el-table-column prop="name" label="名称" min-width="130" />
        <el-table-column prop="ip" label="IP" width="140" />
        <el-table-column prop="asset_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.asset_type }}</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="showBindDialog = false">关闭</el-button>
        <el-button type="primary" @click="bindAssets" :disabled="!selectedBindAssets.length" :loading="binding">
          绑定 ({{ selectedBindAssets.length }})
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Plus, View, Hide, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

// 列表
const loading = ref(false)
const credentials = ref<any[]>([])
const filters = reactive({ credential_type: '', search: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

// 表单
const showFormDialog = ref(false)
const isEditing = ref(false)
const editingId = ref('')
const saving = ref(false)
const formRef = ref<FormInstance>()

const defaultForm = {
  name: '',
  credential_type: 'ssh_password',
  username: '',
  password: '',
  secret: '',
  token: '',
  port: 22 as number | undefined,
  description: '',
}
const formData = reactive({ ...defaultForm })

const formRules: FormRules = {
  name: [{ required: true, message: '请输入凭证名称', trigger: 'blur' }],
  credential_type: [{ required: true, message: '请选择类型', trigger: 'change' }],
}

const showUsername = computed(() => {
  return ['ssh_password', 'ssh_key', 'windows', 'database'].includes(formData.credential_type)
})

const showPassword = computed(() => {
  return ['ssh_password', 'windows', 'database', 'snmp'].includes(formData.credential_type)
})

// 绑定
const showBindDialog = ref(false)
const bindingCredential = ref<any>(null)
const boundAssets = ref<any[]>([])
const bindAssetSearch = ref('')
const bindAvailableAssets = ref<any[]>([])
const selectedBindAssets = ref<any[]>([])
const bindAssetLoading = ref(false)
const binding = ref(false)

function formatCredentialType(t: string) {
  const map: Record<string, string> = {
    ssh_password: 'SSH密码', ssh_key: 'SSH密钥', snmp: 'SNMP',
    windows: 'Windows', database: '数据库', api_token: 'API Token',
  }
  return map[t] || t
}

function formatTime(t: string) {
  return t ? new Date(t).toLocaleString('zh-CN') : '-'
}

function maskSecret(row: any) {
  const val = row.password || row.secret || row.token
  if (!val) return '-'
  return '********'
}

function toggleSecret(row: any) {
  row._showSecret = !row._showSecret
}

function onTypeChange(type: string) {
  if (type === 'ssh_password' || type === 'ssh_key') formData.port = 22
  else if (type === 'database') formData.port = 3306
  else if (type === 'snmp') formData.port = 161
  else formData.port = undefined
}

async function loadCredentials() {
  loading.value = true
  try {
    const params: any = { page: pagination.page, page_size: pagination.pageSize }
    if (filters.credential_type) params.credential_type = filters.credential_type
    if (filters.search) params.search = filters.search
    const { data } = await api.get(R.CREDENTIALS, { params })
    if (data.code === 0) {
      credentials.value = (data.data?.items || data.data || []).map((c: any) => ({ ...c, _showSecret: false }))
      pagination.total = data.data?.total || 0
    }
  } catch (e: any) {
    ElMessage.error('加载凭证失败: ' + (e.message || e))
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  isEditing.value = false
  editingId.value = ''
  Object.assign(formData, { ...defaultForm })
  showFormDialog.value = true
}

function openEditDialog(row: any) {
  isEditing.value = true
  editingId.value = row.id
  Object.assign(formData, {
    name: row.name,
    credential_type: row.credential_type,
    username: row.username || '',
    password: '', // 编辑时不回填密码
    secret: '',
    token: '',
    port: row.port,
    description: row.description || '',
  })
  showFormDialog.value = true
}

async function saveCredential() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const payload: any = { ...formData }
    // 清理不需要的字段
    if (payload.credential_type !== 'ssh_key') delete payload.secret
    if (payload.credential_type !== 'api_token') delete payload.token
    if (!showUsername.value) delete payload.username
    if (!showPassword.value) delete payload.password

    if (isEditing.value) {
      // 编辑时如果没有输入密码则不传密码字段
      if (!payload.password) delete payload.password
      if (!payload.secret) delete payload.secret
      if (!payload.token) delete payload.token
      const { data } = await api.put(R.CREDENTIAL_DETAIL(editingId.value), payload)
      if (data.code === 0) {
        ElMessage.success('凭证已更新')
        showFormDialog.value = false
        loadCredentials()
      } else {
        ElMessage.error(data.message || '更新失败')
      }
    } else {
      const { data } = await api.post(R.CREDENTIALS, payload)
      if (data.code === 0) {
        ElMessage.success('凭证已创建')
        showFormDialog.value = false
        loadCredentials()
      } else {
        ElMessage.error(data.message || '创建失败')
      }
    }
  } catch (e: any) {
    ElMessage.error((isEditing.value ? '更新' : '创建') + '失败: ' + (e.message || e))
  } finally {
    saving.value = false
  }
}

async function deleteCredential(id: string) {
  try {
    const { data } = await api.delete(R.CREDENTIAL_DETAIL(id))
    if (data.code === 0) {
      ElMessage.success('凭证已删除')
      loadCredentials()
    }
  } catch (e: any) {
    ElMessage.error('删除失败: ' + (e.message || e))
  }
}

// 绑定相关
async function openBindDialog(row: any) {
  bindingCredential.value = row
  showBindDialog.value = true
  bindAssetSearch.value = ''
  selectedBindAssets.value = []
  bindAvailableAssets.value = []
  await loadBoundAssets(row.id)
}

async function loadBoundAssets(credentialId: string) {
  try {
    const { data } = await api.get(R.CREDENTIAL_DETAIL(credentialId))
    if (data.code === 0) {
      boundAssets.value = data.data?.assets || data.data?.bound_assets || []
    }
  } catch {
    boundAssets.value = []
  }
}

async function searchBindAssets() {
  bindAssetLoading.value = true
  try {
    const params: any = { page: 1, page_size: 50 }
    if (bindAssetSearch.value) params.search = bindAssetSearch.value
    const { data } = await api.get(R.ASSETS, { params })
    if (data.code === 0) {
      const boundIds = new Set(boundAssets.value.map((a) => a.id))
      bindAvailableAssets.value = (data.data?.items || []).filter((a: any) => !boundIds.has(a.id))
    }
  } catch {
    // 静默
  } finally {
    bindAssetLoading.value = false
  }
}

function handleBindSelection(rows: any[]) {
  selectedBindAssets.value = rows
}

async function bindAssets() {
  if (!bindingCredential.value || !selectedBindAssets.value.length) return
  binding.value = true
  try {
    const asset_ids = selectedBindAssets.value.map((a) => a.id)
    const { data } = await api.post(R.CREDENTIAL_BIND(bindingCredential.value.id), { asset_ids })
    if (data.code === 0) {
      ElMessage.success('已绑定 ' + selectedBindAssets.value.length + ' 个资产')
      selectedBindAssets.value = []
      bindAssetSearch.value = ''
      loadBoundAssets(bindingCredential.value.id)
      loadCredentials() // 刷新绑定计数
    } else {
      ElMessage.error(data.message || '绑定失败')
    }
  } catch (e: any) {
    ElMessage.error('绑定失败: ' + (e.message || e))
  } finally {
    binding.value = false
  }
}

async function unbindAsset(assetId: string) {
  if (!bindingCredential.value) return
  try {
    const { data } = await api.post(R.CREDENTIAL_BIND(bindingCredential.value.id), {
      action: 'unbind',
      asset_ids: [assetId],
    })
    if (data.code === 0) {
      ElMessage.success('已解绑')
      loadBoundAssets(bindingCredential.value.id)
      loadCredentials()
    }
  } catch (e: any) {
    ElMessage.error('解绑失败: ' + (e.message || e))
  }
}

onMounted(() => loadCredentials())
</script>

<style scoped>
.filter-form {
  margin-bottom: var(--autops-space-lg);
}
</style>
