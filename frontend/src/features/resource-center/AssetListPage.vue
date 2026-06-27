<template>
  <div class="asset-list">
    <div class="autops-page-header">
      <span class="autops-page-title">资源列表</span>
      <div class="autops-toolbar-right">
        <el-button type="success" @click="showImportDialog = true">
          <el-icon><Upload /></el-icon> 批量导入
        </el-button>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon> 新建资产
        </el-button>
      </div>
    </div>

    <div class="autops-card">
      <div class="autops-card-body">

      <!-- Filters -->
      <el-form :inline="true" class="autops-toolbar">
        <el-form-item label="搜索">
          <el-input v-model="filters.search" placeholder="名称/IP搜索" clearable @clear="loadAssets" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.asset_type" placeholder="全部" clearable @change="loadAssets">
            <el-option label="Linux 服务器" value="linux_server" />
            <el-option label="Windows 服务器" value="windows_server" />
            <el-option label="数据库" value="database" />
            <el-option label="网络设备" value="network_device" />
            <el-option label="Web 服务" value="web_service" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable @change="loadAssets">
            <el-option label="活跃" value="active" />
            <el-option label="停用" value="inactive" />
            <el-option label="维护中" value="maintenance" />
          </el-select>
        </el-form-item>
        <el-form-item label="环境">
          <el-select v-model="filters.environment" placeholder="全部" clearable @change="loadAssets">
            <el-option label="生产" value="production" />
            <el-option label="预发布" value="staging" />
            <el-option label="开发" value="development" />
            <el-option label="测试" value="test" />
          </el-select>
        </el-form-item>
        <el-form-item label="健康">
          <el-select v-model="filters.health_status" placeholder="全部" clearable @change="loadAssets">
            <el-option label="健康" value="healthy" />
            <el-option label="警告" value="warning" />
            <el-option label="严重" value="critical" />
            <el-option label="未知" value="unknown" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="filters.tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入标签"
            clearable
            @change="loadAssets"
          >
            <el-option v-for="tag in availableTags" :key="tag" :label="tag" :value="tag" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadAssets">查询</el-button>
        </el-form-item>
      </el-form>

      <!-- Table -->
      <el-table stripe
 ref="tableRef"
 :data="assets"
 v-loading="loading"@selection-change="handleSelectionChange"
 >
        <el-table-column type="selection" width="45" />
        <el-table-column prop="name" label="名称" min-width="140" />
        <el-table-column prop="asset_type" label="类型" width="130">
          <template #default="{ row }">
            <el-tag size="small">{{ formatType(row.asset_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP" width="140" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="(statusType(row.status)) as TagType" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="health_status" label="健康" width="90">
          <template #default="{ row }">
            <el-tag :type="(healthType(row.health_status)) as TagType" size="small">{{ healthLabel(row.health_status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reachability" label="可达性" width="90">
          <template #default="{ row }">
            <el-tag :type="row.reachability === 'reachable' ? 'success' : row.reachability === 'unreachable' ? 'danger' : 'info'" size="small">
              {{ ({ reachable: '可达', unreachable: '不可达', unknown: '未知' } as Record<string, string>)[row.reachability] || row.reachability || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="os_type" label="系统" width="90">
          <template #default="{ row }">
            <span>{{ formatOs(row.os_type) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="environment" label="环境" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="(envType(row.environment)) as TagType" effect="plain">{{ formatEnv(row.environment) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewAsset(row)">详情</el-button>
            <el-button size="small" type="warning" @click="openEditDialog(row)">编辑</el-button>
            <el-popconfirm title="确认删除?" @confirm="deleteAsset(row.id)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
            <el-dropdown trigger="click" @command="(cmd: string) => handleQuickAction(cmd, row)">
              <el-button size="small" type="info" class="quick-action-btn">
                更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="collect">
                    <el-icon><VideoPlay /></el-icon> 快速采集
                  </el-dropdown-item>
                  <el-dropdown-item command="check">
                    <el-icon><Monitor /></el-icon> 状态检查
                  </el-dropdown-item>
                  <el-dropdown-item command="bind-credential">
                    <el-icon><Key /></el-icon> 绑定凭证
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @change="loadAssets"
      />
      </div>
    </div>

    <!-- Batch Operation Bar -->
    <transition name="batch-bar">
      <div v-if="selectedAssets.length > 0" class="batch-operation-bar">
        <span class="batch-info">已选择 <strong>{{ selectedAssets.length }}</strong> 项</span>
        <el-button type="danger" @click="batchDelete" :loading="batchLoading">
          <el-icon><Delete /></el-icon> 批量删除
        </el-button>
        <el-button type="warning" @click="openBatchCredentialDialog">
          <el-icon><Key /></el-icon> 批量绑定凭证
        </el-button>
        <el-button type="success" @click="openBatchGroupDialog">
          <el-icon><FolderAdd /></el-icon> 批量加入分组
        </el-button>
        <el-button @click="clearSelection">取消选择</el-button>
      </div>
    </transition>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="showFormDialog" :title="isEditing ? '编辑资产' : '新建资产'" width="600px">
      <el-form :model="formData" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="formData.asset_type" style="width: 100%">
            <el-option label="Linux 服务器" value="linux_server" />
            <el-option label="Windows 服务器" value="windows_server" />
            <el-option label="数据库" value="database" />
            <el-option label="网络设备" value="network_device" />
            <el-option label="Web 服务" value="web_service" />
          </el-select>
        </el-form-item>
        <el-form-item label="IP" required>
          <el-input v-model="formData.ip" />
        </el-form-item>
        <el-form-item label="端口">
          <el-input-number v-model="formData.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="操作系统">
          <el-select v-model="formData.os_type">
            <el-option label="Linux" value="linux" />
            <el-option label="Windows" value="windows" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="formData.status">
            <el-option label="活跃" value="active" />
            <el-option label="停用" value="inactive" />
            <el-option label="维护中" value="maintenance" />
          </el-select>
        </el-form-item>
        <el-form-item label="环境">
          <el-select v-model="formData.environment">
            <el-option label="生产" value="production" />
            <el-option label="预发布" value="staging" />
            <el-option label="开发" value="development" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button type="primary" @click="saveAsset" :loading="saving">{{ isEditing ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>

    <!-- Detail Drawer -->
    <el-drawer v-model="showDetail" title="资产详情" size="500px">
      <template v-if="currentAsset">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="ID">{{ currentAsset.id }}</el-descriptions-item>
          <el-descriptions-item label="名称">{{ currentAsset.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ formatType(currentAsset.asset_type) }}</el-descriptions-item>
          <el-descriptions-item label="IP">{{ currentAsset.ip }}</el-descriptions-item>
          <el-descriptions-item label="端口">{{ currentAsset.port || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="(statusType(currentAsset.status)) as TagType">{{ currentAsset.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="健康状态">
            <el-tag :type="(healthType(currentAsset.health_status)) as TagType">{{ currentAsset.health_status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="可达性">
            <el-tag :type="currentAsset.reachability === 'reachable' ? 'success' : 'danger'">
              {{ currentAsset.reachability || '-' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="操作系统">{{ currentAsset.os_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="环境">{{ currentAsset.environment || '-' }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ currentAsset.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ currentAsset.created_at }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ currentAsset.updated_at || '-' }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-drawer>

    <!-- Import Dialog -->
    <el-dialog v-model="showImportDialog" title="批量导入资产" width="780px" destroy-on-close>
      <el-upload
        ref="importUploadRef"
        :auto-upload="false"
        :limit="1"
        accept=".csv,.xlsx,.xls"
        :on-change="handleImportFileChange"
        :on-remove="handleImportFileRemove"
        drag
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽文件到此处，或 <em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 CSV / Excel 文件，包含列: name, asset_type, ip, port, os_type, environment, status</div>
        </template>
      </el-upload>

      <div v-if="importPreviewData.length > 0" class="import-preview">
        <el-divider>数据预览 (共 {{ importPreviewData.length }} 条)</el-divider>
        <el-table stripe :data="importPreviewData"max-height="300" size="small">
          <el-table-column prop="name" label="名称" min-width="120" />
          <el-table-column prop="asset_type" label="类型" width="120" />
          <el-table-column prop="ip" label="IP" width="130" />
          <el-table-column prop="port" label="端口" width="70" />
          <el-table-column prop="environment" label="环境" width="80" />
          <el-table-column prop="status" label="状态" width="80" />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="closeImportDialog">取消</el-button>
        <el-button
          type="primary"
          :disabled="importPreviewData.length === 0"
          :loading="importLoading"
          @click="executeImport"
        >
          确认导入
        </el-button>
      </template>
    </el-dialog>

    <!-- Batch Bind Credential Dialog -->
    <el-dialog v-model="showBatchCredDialog" title="批量绑定凭证" width="480px">
      <el-form label-width="80px">
        <el-form-item label="选中资产">
          <span>{{ selectedAssets.length }} 项</span>
        </el-form-item>
        <el-form-item label="选择凭证" required>
          <el-select v-model="batchCredId" placeholder="请选择凭证" filterable style="width: 100%">
            <el-option
              v-for="cred in credentialOptions"
              :key="cred.id"
              :label="cred.name"
              :value="cred.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchCredDialog = false">取消</el-button>
        <el-button type="primary" :loading="batchLoading" @click="batchBindCredential">确认绑定</el-button>
      </template>
    </el-dialog>

    <!-- Batch Add to Group Dialog -->
    <el-dialog v-model="showBatchGroupDialog" title="批量加入分组" width="480px">
      <el-form label-width="80px">
        <el-form-item label="选中资产">
          <span>{{ selectedAssets.length }} 项</span>
        </el-form-item>
        <el-form-item label="选择分组" required>
          <el-select v-model="batchGroupId" placeholder="请选择分组" filterable style="width: 100%">
            <el-option
              v-for="group in groupOptions"
              :key="group.id"
              :label="group.name"
              :value="group.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchGroupDialog = false">取消</el-button>
        <el-button type="primary" :loading="batchLoading" @click="batchAddToGroup">确认加入</el-button>
      </template>
    </el-dialog>

    <!-- Quick Bind Credential Dialog (single row) -->
    <el-dialog v-model="showQuickBindDialog" title="绑定凭证" width="480px">
      <el-form label-width="80px">
        <el-form-item label="资产">
          <span>{{ quickBindAsset?.name }}</span>
        </el-form-item>
        <el-form-item label="选择凭证" required>
          <el-select v-model="quickBindCredId" placeholder="请选择凭证" filterable style="width: 100%">
            <el-option
              v-for="cred in credentialOptions"
              :key="cred.id"
              :label="cred.name"
              :value="cred.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showQuickBindDialog = false">取消</el-button>
        <el-button type="primary" :loading="quickActionLoading" @click="executeQuickBind">确认绑定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import type { TagType } from '@/shared/types'
import {
  Plus, Upload, UploadFilled, Delete, Key, FolderAdd,
  ArrowDown, VideoPlay, Monitor,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadFile } from 'element-plus'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import {
  assetTypeLabel, assetStatusTag, assetStatusLabel,
  healthTag, healthLabel as healthLabel0,
} from '@/shared/utils/labels'

// ---------- State ----------
const loading = ref(false)
const saving = ref(false)
const assets = ref<any[]>([])
const showFormDialog = ref(false)
const showDetail = ref(false)
const currentAsset = ref<any>(null)
const isEditing = ref(false)
const editingId = ref('')
const tableRef = ref()

// Filters
const filters = reactive({
  search: '',
  asset_type: '',
  status: '',
  environment: '',
  health_status: '',
  tags: [] as string[],
})
const availableTags = ref<string[]>([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

// Selection & Batch
const selectedAssets = ref<any[]>([])
const batchLoading = ref(false)

// Batch credential dialog
const showBatchCredDialog = ref(false)
const batchCredId = ref('')
const credentialOptions = ref<any[]>([])

// Batch group dialog
const showBatchGroupDialog = ref(false)
const batchGroupId = ref('')
const groupOptions = ref<any[]>([])

// Import
const showImportDialog = ref(false)
const importLoading = ref(false)
const importPreviewData = ref<any[]>([])
const importFileRaw = ref<File | null>(null)
const importUploadRef = ref()

// Quick actions
const quickActionLoading = ref(false)
const showQuickBindDialog = ref(false)
const quickBindAsset = ref<any>(null)
const quickBindCredId = ref('')

// ---------- Form ----------
const defaultForm = {
  name: '', asset_type: 'linux_server', ip: '', port: undefined as number | undefined,
  os_type: 'linux', description: '', environment: 'production', status: 'active',
}
const formData = reactive({ ...defaultForm })

// ---------- Helpers ----------
// 类型/状态/健康统一取自 shared/utils/labels.ts（单一事实源）
const formatType = (t: string): string => assetTypeLabel(t)
const statusType = (s: string): TagType => assetStatusTag(s) as TagType
const statusLabel = (s: string): string => assetStatusLabel(s)
const healthType = (h: string): TagType => healthTag(h) as TagType
const healthLabel = (h: string): string => healthLabel0(h)

function lifecycleType(ls: string): TagType {
  const map: Record<string, string> = {
    managed: 'primary', online: 'success', maintenance: 'warning', retired: 'danger',
  }
  return (map[ls] || 'info') as TagType
}

function formatLifecycle(ls: string) {
  const map: Record<string, string> = {
    managed: '纳管', online: '在线', maintenance: '维护中', retired: '退役',
  }
  return map[ls] || ls || '-'
}

function formatOs(o: string) {
  if (!o) return '-'
  const map: Record<string, string> = { linux: 'Linux', windows: 'Windows', centos: 'CentOS', ubuntu: 'Ubuntu', redhat: 'RHEL' }
  return map[o.toLowerCase()] || o
}

function formatEnv(e: string) {
  if (!e) return '-'
  const map: Record<string, string> = { production: '生产', prod: '生产', staging: '预发布', testing: '测试', test: '测试', development: '开发', dev: '开发' }
  return map[e.toLowerCase()] || e
}

function envType(e: string): TagType {
  if (!e) return ('info') as TagType
  const map: Record<string, string> = { production: 'danger', prod: 'danger', staging: 'warning', testing: 'primary', test: 'primary', development: 'success', dev: 'success' }
  return (map[e.toLowerCase()] || 'info') as TagType
}

// ---------- Load ----------
async function loadAssets() {
  loading.value = true
  try {
    const params: any = { page: pagination.page, page_size: pagination.pageSize }
    if (filters.search) params.search = filters.search
    if (filters.asset_type) params.asset_type = filters.asset_type
    if (filters.status) params.status = filters.status
    if (filters.environment) params.environment = filters.environment
    if (filters.health_status) params.health_status = filters.health_status
    if (filters.tags.length > 0) params.tags = filters.tags.join(',')
    const { data } = await api.get(R.ASSETS, { params })
    if (data.code === 0) {
      assets.value = data.data.items || []
      pagination.total = data.data.total || 0
      // Collect tags from items for filter suggestions
      const tagSet = new Set<string>()
      assets.value.forEach((a: any) => (a.tags || []).forEach((t: string) => tagSet.add(t)))
      tagSet.forEach(t => { if (!availableTags.value.includes(t)) availableTags.value.push(t) })
    }
  } catch (e: any) {
    ElMessage.error('加载资产失败: ' + (e.message || e))
  } finally {
    loading.value = false
  }
}

async function loadCredentialOptions() {
  try {
    const { data } = await api.get(R.CREDENTIALS, { params: { page_size: 100 } })
    if (data.code === 0) credentialOptions.value = data.data.items || []
  } catch { /* ignore */ }
}

async function loadGroupOptions() {
  try {
    const { data } = await api.get(R.ASSET_GROUPS, { params: { page_size: 100 } })
    if (data.code === 0) groupOptions.value = data.data.items || []
  } catch { /* ignore */ }
}

// ---------- Selection ----------
function handleSelectionChange(rows: any[]) {
  selectedAssets.value = rows
}

function clearSelection() {
  tableRef.value?.clearSelection()
}

// ---------- CRUD ----------
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
    asset_type: row.asset_type,
    ip: row.ip,
    port: row.port,
    os_type: row.os_type || 'linux',
    description: row.description || '',
    environment: row.environment || 'production',
    status: row.status || 'active',
  })
  showFormDialog.value = true
}

async function saveAsset() {
  if (!formData.name || !formData.ip) {
    ElMessage.warning('名称和IP为必填项')
    return
  }
  saving.value = true
  try {
    if (isEditing.value) {
      const { data } = await api.put(R.ASSET_DETAIL(editingId.value), formData)
      if (data.code === 0) {
        ElMessage.success('保存成功')
        showFormDialog.value = false
        loadAssets()
      } else {
        ElMessage.error(data.message || '保存失败')
      }
    } else {
      const { data } = await api.post(R.ASSETS, formData)
      if (data.code === 0) {
        ElMessage.success('创建成功')
        showFormDialog.value = false
        Object.assign(formData, { ...defaultForm })
        loadAssets()
      } else {
        ElMessage.error(data.message || '创建失败')
      }
    }
  } catch (e: any) {
    ElMessage.error((isEditing.value ? '保存' : '创建') + '失败: ' + (e.message || e))
  } finally {
    saving.value = false
  }
}

function viewAsset(row: any) {
  currentAsset.value = row
  showDetail.value = true
}

async function deleteAsset(id: string) {
  try {
    await api.delete(R.ASSET_DETAIL(id))
    ElMessage.success('删除成功')
    loadAssets()
  } catch (e: any) {
    ElMessage.error('删除失败')
  }
}

// ---------- Batch Operations ----------
async function batchDelete() {
  try {
    await ElMessageBox.confirm(
      '确认删除选中的 ' + selectedAssets.value.length + ' 项资产？此操作不可撤销。',
      '批量删除确认',
      { type: 'warning' },
    )
  } catch { return }

  batchLoading.value = true
  try {
    const ids = selectedAssets.value.map(a => a.id)
    await Promise.all(ids.map(id => api.delete(R.ASSET_DETAIL(id))))
    ElMessage.success('成功删除 ' + ids.length + ' 项资产')
    clearSelection()
    loadAssets()
  } catch (e: any) {
    ElMessage.error('批量删除失败: ' + (e.message || e))
  } finally {
    batchLoading.value = false
  }
}

function openBatchCredentialDialog() {
  batchCredId.value = ''
  loadCredentialOptions()
  showBatchCredDialog.value = true
}

async function batchBindCredential() {
  if (!batchCredId.value) {
    ElMessage.warning('请选择凭证')
    return
  }
  batchLoading.value = true
  try {
    const assetIds = selectedAssets.value.map(a => a.id)
    await api.post(R.CREDENTIAL_BIND(batchCredId.value), { asset_ids: assetIds })
    ElMessage.success('已绑定凭证到 ' + assetIds.length + ' 项资产')
    showBatchCredDialog.value = false
    clearSelection()
    loadAssets()
  } catch (e: any) {
    ElMessage.error('批量绑定凭证失败: ' + (e.message || e))
  } finally {
    batchLoading.value = false
  }
}

function openBatchGroupDialog() {
  batchGroupId.value = ''
  loadGroupOptions()
  showBatchGroupDialog.value = true
}

async function batchAddToGroup() {
  if (!batchGroupId.value) {
    ElMessage.warning('请选择分组')
    return
  }
  batchLoading.value = true
  try {
    const assetIds = selectedAssets.value.map(a => a.id)
    await api.post(R.ASSET_GROUP_MEMBERS(batchGroupId.value), { asset_ids: assetIds })
    ElMessage.success('已将 ' + assetIds.length + ' 项资产加入分组')
    showBatchGroupDialog.value = false
    clearSelection()
  } catch (e: any) {
    ElMessage.error('批量加入分组失败: ' + (e.message || e))
  } finally {
    batchLoading.value = false
  }
}

// ---------- Import ----------
function handleImportFileChange(file: UploadFile) {
  if (!file.raw) return
  importFileRaw.value = file.raw
  parseImportFile(file.raw)
}

function handleImportFileRemove() {
  importFileRaw.value = null
  importPreviewData.value = []
}

function parseImportFile(file: File) {
  const isCsv = file.name.endsWith('.csv')
  if (isCsv) {
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result as string
      const lines = text.trim().split('\n')
      if (lines.length < 2) {
        ElMessage.warning('文件为空或缺少数据行')
        return
      }
      const headers = lines[0].split(',').map(h => h.trim().toLowerCase())
      const rows = lines.slice(1).map(line => {
        const values = line.split(',').map(v => v.trim())
        const obj: Record<string, string> = {}
        headers.forEach((h, i) => { obj[h] = values[i] || '' })
        return obj
      })
      importPreviewData.value = rows
    }
    reader.readAsText(file)
  } else {
    // For xlsx/xls, inform user that parsing is handled server-side
    ElMessage.info('Excel 文件将在上传后由服务端解析预览')
    importPreviewData.value = []
  }
}

function closeImportDialog() {
  showImportDialog.value = false
  importPreviewData.value = []
  importFileRaw.value = null
}

async function executeImport() {
  if (!importFileRaw.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  importLoading.value = true
  try {
    const formDataObj = new FormData()
    formDataObj.append('file', importFileRaw.value)
    const { data } = await api.post(R.ASSET_IMPORT, formDataObj, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    if (data.code === 0) {
      const imported = data.data?.imported ?? data.data?.created?.length ?? 0
      ElMessage.success('成功导入 ' + imported + ' 项资产')
      closeImportDialog()
      loadAssets()
    } else {
      ElMessage.error(data.message || '导入失败')
    }
  } catch (e: any) {
    ElMessage.error('导入失败: ' + (e.message || e))
  } finally {
    importLoading.value = false
  }
}

// ---------- Quick Actions ----------
async function handleQuickAction(command: string, row: any) {
  switch (command) {
    case 'collect':
      await quickCollect(row)
      break
    case 'check':
      await quickStatusCheck(row)
      break
    case 'bind-credential':
      quickBindAsset.value = row
      quickBindCredId.value = ''
      loadCredentialOptions()
      showQuickBindDialog.value = true
      break
  }
}

async function quickCollect(row: any) {
  quickActionLoading.value = true
  try {
    const { data } = await api.post(R.ASSET_COLLECTION_TRIGGER(row.id))
    if (data.code === 0) {
      ElMessage.success('已触发 [' + row.name + '] 采集任务')
    } else {
      ElMessage.error(data.message || '触发采集失败')
    }
  } catch (e: any) {
    ElMessage.error('触发采集失败: ' + (e.message || e))
  } finally {
    quickActionLoading.value = false
  }
}

async function quickStatusCheck(row: any) {
  quickActionLoading.value = true
  try {
    const { data } = await api.get(R.STATES.LATEST(row.id))
    if (data.code === 0) {
      ElMessage.success('[' + row.name + '] 状态: ' + (data.data?.health_status || '正常'))
    } else {
      ElMessage.warning(data.message || '无法获取状态')
    }
  } catch (e: any) {
    ElMessage.error('状态检查失败: ' + (e.message || e))
  } finally {
    quickActionLoading.value = false
  }
}

async function executeQuickBind() {
  if (!quickBindCredId.value) {
    ElMessage.warning('请选择凭证')
    return
  }
  quickActionLoading.value = true
  try {
    await api.post(R.CREDENTIAL_BIND(quickBindCredId.value), {
      asset_ids: [quickBindAsset.value.id],
    })
    ElMessage.success('凭证已绑定到 [' + quickBindAsset.value.name + ']')
    showQuickBindDialog.value = false
  } catch (e: any) {
    ElMessage.error('绑定凭证失败: ' + (e.message || e))
  } finally {
    quickActionLoading.value = false
  }
}

// ---------- Init ----------
onMounted(() => loadAssets())
</script>

<style scoped>
.filter-form {
  margin-bottom: var(--autops-space-lg);
}
.quick-action-btn {
  margin-left: 4px;
}

/* Batch operation floating bar */
.batch-operation-bar {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 999;
  background: var(--autops-bg-1);
  border: 1px solid var(--autops-bg-4);
  border-radius: var(--autops-radius-md);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  padding: var(--autops-space-md) 24px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.batch-info {
  color: var(--autops-text-2);
  margin-right: 8px;
  white-space: nowrap;
}

/* Transition for batch bar */
.batch-bar-enter-active,
.batch-bar-leave-active {
  transition: all 0.3s ease;
}
.batch-bar-enter-from,
.batch-bar-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

/* Import preview */
.import-preview {
  margin-top: var(--autops-space-lg);
}
</style>
