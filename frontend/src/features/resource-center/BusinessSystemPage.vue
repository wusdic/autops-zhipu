<template>
  <div class="autops-page-container">
    <PageHeader title="业务系统" desc="管理业务系统及其关联资产">
      <template #actions>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon> 新建业务系统
        </el-button>
      </template>
    </PageHeader>

    <!-- Search & Filter Bar -->
    <el-card shadow="never" class="filter-card">
      <el-row :gutter="16" align="middle">
        <el-col :span="8">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索系统名称、负责人..."
            clearable
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterHealth" placeholder="健康状态" clearable @change="handleSearch">
            <el-option label="健康" value="healthy" />
            <el-option label="告警" value="warning" />
            <el-option label="异常" value="error" />
            <el-option label="未知" value="unknown" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button @click="handleSearch">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- Data Table -->
    <el-card shadow="never" class="table-card">
      <el-table stripe
 :data="systems"v-loading="loading"
 empty-text="暂无业务系统"
 @sort-change="handleSortChange"
 >
        <el-table-column prop="name" label="系统名称" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="system-name" @click="viewSystem(row)">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="负责人" width="120" />
        <el-table-column prop="asset_count" label="资产数量" width="100" sortable="custom" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.asset_count ?? 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="health_status" label="健康状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="(healthTagType(row.health_status)) as TagType" size="small" effect="light">
              {{ healthLabel(row.health_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="contact" label="联系方式" width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="text-tertiary">{{ row.contact || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="170" sortable="custom">
          <template #default="{ row }">
            <span class="text-tertiary">{{ formatTime(row.updated_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button plain type="primary" size="small" @click="viewSystem(row)">查看</el-button>
            <el-button plain type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button plain type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="fetchSystems"
          @current-change="fetchSystems"
        />
      </div>
    </el-card>

    <!-- Create / Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑业务系统' : '新建业务系统'"
      width="600px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="90px"
        label-position="right"
      >
        <el-form-item label="系统名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入系统名称" maxlength="64" />
        </el-form-item>
        <el-form-item label="负责人" prop="owner">
          <el-input v-model="formData.owner" placeholder="请输入负责人" maxlength="32" />
        </el-form-item>
        <el-form-item label="联系方式" prop="contact">
          <el-input v-model="formData.contact" placeholder="请输入联系方式" maxlength="64" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            placeholder="请输入系统描述"
            :rows="4"
            maxlength="256"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- Detail Drawer -->
    <el-drawer v-model="drawerVisible" title="业务系统详情" size="480px">
      <template v-if="currentSystem">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="系统名称">{{ currentSystem.name }}</el-descriptions-item>
          <el-descriptions-item label="负责人">{{ currentSystem.owner || '-' }}</el-descriptions-item>
          <el-descriptions-item label="联系方式">{{ currentSystem.contact || '-' }}</el-descriptions-item>
          <el-descriptions-item label="资产数量">
            <el-tag size="small">{{ currentSystem.asset_count ?? 0 }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="健康状态">
            <el-tag :type="(healthTagType(currentSystem.health_status)) as TagType" size="small">
              {{ healthLabel(currentSystem.health_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="描述">{{ currentSystem.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTime(currentSystem.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatTime(currentSystem.updated_at) }}</el-descriptions-item>
        </el-descriptions>

        <!-- 成员资产管理 -->
        <div style="margin-top: 16px; display: flex; align-items: center; justify-content: space-between">
          <span style="font-weight: 600">成员资产（{{ members.length }}）</span>
          <el-button type="primary" size="small" @click="openAddMembers"><el-icon><Plus /></el-icon> 添加资产</el-button>
        </div>
        <el-table :data="members" v-loading="membersLoading" size="small" style="margin-top: 8px" empty-text="暂无成员资产">
          <el-table-column prop="name" label="名称" min-width="120" show-overflow-tooltip />
          <el-table-column prop="ip" label="IP" width="120" />
          <el-table-column label="操作" width="70" align="center">
            <template #default="{ row }">
              <el-button link type="danger" size="small" @click="removeMember(row)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-drawer>

    <!-- 添加成员资产对话框 -->
    <el-dialog v-model="addMembersVisible" title="添加成员资产" width="520px">
      <el-select
        v-model="selectedAssetIds"
        multiple filterable remote :remote-method="searchAssets" :loading="assetSearchLoading"
        placeholder="搜索并选择资产（仅未归属或属于本业务的资产）" style="width: 100%"
      >
        <el-option v-for="a in assetCandidates" :key="a.id" :label="a.name + (a.ip ? ' (' + a.ip + ')' : '')" :value="a.id" />
      </el-select>
      <template #footer>
        <el-button @click="addMembersVisible = false">取消</el-button>
        <el-button type="primary" :loading="addingMembers" @click="confirmAddMembers">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import client from '@/shared/api/client'
import { healthLabel as healthLabelFn } from '@/shared/utils/labels'
import { API } from '@/shared/api/routes'

// ---------- Types ----------
interface BusinessSystem {
  id: string
  name: string
  owner: string
  contact: string
  description: string
  asset_count: number
  health_status: 'healthy' | 'warning' | 'error' | 'unknown'
  created_at: string
  updated_at: string
}

// ---------- State ----------
const loading = ref(false)
const submitting = ref(false)
const systems = ref<BusinessSystem[]>([])
const dialogVisible = ref(false)
const drawerVisible = ref(false)
const isEditing = ref(false)
const editingId = ref<string | null>(null)
const currentSystem = ref<BusinessSystem | null>(null)
const formRef = ref<FormInstance>()

const searchKeyword = ref('')
const filterHealth = ref('')
const sortField = ref('')
const sortOrder = ref('')

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

const formData = reactive({
  name: '',
  owner: '',
  contact: '',
  description: '',
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入系统名称', trigger: 'blur' }],
  owner: [{ required: true, message: '请输入负责人', trigger: 'blur' }],
}

// ---------- Helpers ----------
function healthTagType(status: string): TagType {
  const map: Record<string, string> = { healthy: 'success', warning: 'warning', error: 'danger', unknown: 'info' }
  return (map[status] || 'info') as TagType
}

const healthLabel = (status: string): string => healthLabelFn(status)

function formatTime(val?: string) {
  if (!val) return '-'
  return val.replace('T', ' ').substring(0, 19)
}

// ---------- Data Fetching ----------
async function fetchSystems() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.page_size,
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (filterHealth.value) params.health_status = filterHealth.value
    if (sortField.value) {
      params.sort_by = sortField.value
      params.sort_order = sortOrder.value
    }

    const res = await client.get(API.BUSINESS_SYSTEMS, { params })
    const data = res.data?.data ?? res.data
    if (Array.isArray(data?.items)) {
      systems.value = data.items
      pagination.total = data.total ?? data.items.length
    } else if (Array.isArray(data)) {
      systems.value = data
      pagination.total = data.length
    }
  } catch (e: any) {
    ElMessage.error(e.message || '获取业务系统列表失败')
  } finally {
    loading.value = false
  }
}

// ---------- Search & Filter ----------
function handleSearch() {
  pagination.page = 1
  fetchSystems()
}

function resetFilters() {
  searchKeyword.value = ''
  filterHealth.value = ''
  sortField.value = ''
  sortOrder.value = ''
  handleSearch()
}

function handleSortChange({ prop, order }: any) {
  sortField.value = prop || ''
  sortOrder.value = order === 'ascending' ? 'asc' : order === 'descending' ? 'desc' : 'primary'
  fetchSystems()
}

// ---------- Dialog ----------
function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  dialogVisible.value = true
}

function openEditDialog(row: any) {
  isEditing.value = true
  editingId.value = row.id
  Object.assign(formData, {
    name: row.name,
    owner: row.owner,
    contact: row.contact,
    description: row.description,
  })
  dialogVisible.value = true
}

function resetForm() {
  Object.assign(formData, { name: '', owner: '', contact: '', description: ''})
  formRef.value?.resetFields()
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload = { ...formData }
    if (isEditing.value && editingId.value) {
      await client.put(API.BUSINESS_SYSTEM_DETAIL(editingId.value), payload)
      ElMessage.success('更新成功')
    } else {
      await client.post(API.BUSINESS_SYSTEMS, payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchSystems()
  } catch (e: any) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

// ---------- Actions ----------
function viewSystem(row: any) {
  currentSystem.value = row
  drawerVisible.value = true
  loadMembers()
}

// ---------- 成员资产管理 ----------
const members = ref<any[]>([])
const membersLoading = ref(false)
const addMembersVisible = ref(false)
const selectedAssetIds = ref<string[]>([])
const assetCandidates = ref<any[]>([])
const assetSearchLoading = ref(false)
const addingMembers = ref(false)

async function loadMembers() {
  if (!currentSystem.value) return
  membersLoading.value = true
  try {
    const { data } = await client.get(`${API.BUSINESS_SYSTEM_DETAIL(currentSystem.value.id)}/members`, { params: { page: 1, page_size: 500 } })
    members.value = data?.data?.items || data?.data || []
  } catch { members.value = [] }
  finally { membersLoading.value = false }
}

function openAddMembers() {
  selectedAssetIds.value = []
  assetCandidates.value = []
  addMembersVisible.value = true
  searchAssets('')
}

async function searchAssets(query: string) {
  assetSearchLoading.value = true
  try {
    const params: any = { page: 1, page_size: 50, asset_type: '' }
    if (query) params.keyword = query
    const { data } = await client.get(API.ASSETS, { params })
    const items = data?.data?.items || data?.data || []
    // 排除业务系统本身；仅展示未归属或已属于本业务的资产
    assetCandidates.value = items.filter((a: any) =>
      a.asset_type !== 'business_system' &&
      (!a.business_system_id || a.business_system_id === currentSystem.value?.id))
  } catch { assetCandidates.value = [] }
  finally { assetSearchLoading.value = false }
}

async function confirmAddMembers() {
  if (!currentSystem.value || selectedAssetIds.value.length === 0) { addMembersVisible.value = false; return }
  addingMembers.value = true
  try {
    await client.post(`${API.BUSINESS_SYSTEM_DETAIL(currentSystem.value.id)}/members`, { asset_ids: selectedAssetIds.value })
    ElMessage.success('已添加成员资产')
    addMembersVisible.value = false
    await loadMembers()
    fetchSystems()
  } catch (e: any) {
    ElMessage.error('添加失败: ' + (e.message || e))
  } finally { addingMembers.value = false }
}

async function removeMember(row: any) {
  if (!currentSystem.value) return
  try {
    await ElMessageBox.confirm(`确认将「${row.name}」移出该业务系统？`, '移除确认', { type: 'warning' })
    await client.delete(`${API.BUSINESS_SYSTEM_DETAIL(currentSystem.value.id)}/members/${row.id}`)
    ElMessage.success('已移除')
    await loadMembers()
    fetchSystems()
  } catch { /* cancelled */ }
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm('确认删除业务系统「' + row.name + '」？此操作不可撤销。', '删除确认', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
    await client.delete(API.BUSINESS_SYSTEM_DETAIL(row.id))
    ElMessage.success('删除成功')
    fetchSystems()
  } catch (e: any) {
    if (e !== 'cancel' && e?.action !== 'cancel' && e?.message !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

// ---------- Init ----------
onMounted(() => {
  fetchSystems()
})
</script>

<style scoped>
.filter-card {
  margin-bottom: var(--autops-space-lg);
}

.filter-card :deep(.el-card__body) {
  padding: var(--autops-space-lg);
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.system-name {
  color: var(--autops-primary);
  cursor: pointer;
  font-weight: 500;
}

.system-name:hover {
  text-decoration: underline;
}

.text-tertiary {
  color: var(--autops-info);
  font-size: var(--autops-font-13);
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: var(--autops-space-lg);
}
</style>
