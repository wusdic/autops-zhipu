<template>
  <div class="asset-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>资产列表</span>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon><Plus /></el-icon> 新建资产
          </el-button>
        </div>
      </template>

      <!-- Filters -->
      <el-form :inline="true" class="filter-form">
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
        <el-form-item>
          <el-button type="primary" @click="loadAssets">查询</el-button>
        </el-form-item>
      </el-form>

      <!-- Table -->
      <el-table :data="assets" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" min-width="140" />
        <el-table-column prop="asset_type" label="类型" width="130">
          <template #default="{ row }">
            <el-tag size="small">{{ formatType(row.asset_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP" width="140" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="health_status" label="健康" width="90">
          <template #default="{ row }">
            <el-tag :type="healthType(row.health_status)" size="small">{{ row.health_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="os_type" label="系统" width="90" />
        <el-table-column prop="environment" label="环境" width="90" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewAsset(row)">详情</el-button>
            <el-button size="small" type="warning" @click="openEditDialog(row)">编辑</el-button>
            <el-popconfirm title="确认删除?" @confirm="deleteAsset(row.id)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
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
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>

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
            <el-option label="测试" value="staging" />
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
            <el-tag :type="statusType(currentAsset.status)">{{ currentAsset.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="健康状态">
            <el-tag :type="healthType(currentAsset.health_status)">{{ currentAsset.health_status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="操作系统">{{ currentAsset.os_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="环境">{{ currentAsset.environment || '-' }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ currentAsset.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ currentAsset.created_at }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ currentAsset.updated_at || '-' }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

const loading = ref(false)
const saving = ref(false)
const assets = ref<any[]>([])
const showFormDialog = ref(false)
const showDetail = ref(false)
const currentAsset = ref<any>(null)
const isEditing = ref(false)
const editingId = ref('')

const filters = reactive({ search: '', asset_type: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const defaultForm = {
  name: '', asset_type: 'linux_server', ip: '', port: undefined as number | undefined,
  os_type: 'linux', description: '', environment: 'production', status: 'active',
}
const formData = reactive({ ...defaultForm })

function formatType(t: string) {
  const map: Record<string, string> = {
    linux_server: 'Linux', windows_server: 'Windows', database: '数据库',
    network_device: '网络', web_service: 'Web',
  }
  return map[t] || t
}

function statusType(s: string) {
  return s === 'active' ? 'success' : s === 'inactive' ? 'danger' : 'warning'
}

function healthType(h: string) {
  return h === 'healthy' ? 'success' : h === 'warning' ? 'warning' : h === 'critical' ? 'danger' : 'info'
}

async function loadAssets() {
  loading.value = true
  try {
    const params: any = { page: pagination.page, page_size: pagination.pageSize }
    if (filters.asset_type) params.asset_type = filters.asset_type
    if (filters.status) params.status = filters.status
    const { data } = await api.get(R.ASSETS, { params })
    if (data.code === 0) {
      assets.value = data.data.items || []
      pagination.total = data.data.total || 0
    }
  } catch (e: any) {
    ElMessage.error('加载资产失败: ' + (e.message || e))
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
      const { data } = await api.put(`/api/v1/assets/${editingId.value}`, formData)
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
    await api.delete(`/api/v1/assets/${id}`)
    ElMessage.success('删除成功')
    loadAssets()
  } catch (e: any) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => loadAssets())
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filter-form { margin-bottom: 16px; }
</style>
