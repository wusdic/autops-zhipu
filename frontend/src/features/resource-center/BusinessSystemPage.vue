<template>
  <div class="page-container">
    <!-- Page Header -->
    <div class="page-header">
      <div>
        <h2 class="page-title">业务系统</h2>
        <p class="page-subtitle">管理业务系统及其关联资产</p>
      </div>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon> 新建业务系统
      </el-button>
    </div>

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
      <el-table
        :data="systems"
        stripe
        v-loading="loading"
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
            <el-tag :type="healthTagType(row.health_status)" size="small" effect="light">
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
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="viewSystem(row)">查看</el-button>
            <el-button text type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
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
      width="560px"
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
            <el-tag :type="healthTagType(currentSystem.health_status)" size="small">
              {{ healthLabel(currentSystem.health_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="描述">{{ currentSystem.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTime(currentSystem.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatTime(currentSystem.updated_at) }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
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
function healthTagType(status: string) {
  const map: Record<string, string> = { healthy: 'success', warning: 'warning', error: 'danger', unknown: 'info' }
  return map[status] || 'info'
}

function healthLabel(status: string) {
  const map: Record<string, string> = { healthy: '健康', warning: '告警', error: '异常', unknown: '未知' }
  return map[status] || '未知'
}

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
  sortOrder.value = order === 'ascending' ? 'asc' : order === 'descending' ? 'desc' : ''
  fetchSystems()
}

// ---------- Dialog ----------
function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  dialogVisible.value = true
}

function openEditDialog(row: BusinessSystem) {
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
  Object.assign(formData, { name: '', owner: '', contact: '', description: '' })
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
function viewSystem(row: BusinessSystem) {
  currentSystem.value = row
  drawerVisible.value = true
}

async function handleDelete(row: BusinessSystem) {
  try {
    await ElMessageBox.confirm(`确认删除业务系统「${row.name}」？此操作不可撤销。`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
    await client.delete(API.BUSINESS_SYSTEM_DETAIL(row.id))
    ElMessage.success('删除成功')
    fetchSystems()
  } catch (e: any) {
    if (e !== 'cancel') {
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
.page-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
  margin: 0;
}

.page-subtitle {
  font-size: 13px;
  color: #86909c;
  margin-top: 4px;
}

.filter-card {
  margin-bottom: 16px;
}

.filter-card :deep(.el-card__body) {
  padding: 16px;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.system-name {
  color: #165dff;
  cursor: pointer;
  font-weight: 500;
}

.system-name:hover {
  text-decoration: underline;
}

.text-tertiary {
  color: #86909c;
  font-size: 13px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: 16px;
}
</style>
