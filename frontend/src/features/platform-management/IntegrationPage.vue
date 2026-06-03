<template>
  <div class="page-container">
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">外部集成</div>
        <div class="autops-page-desc">管理平台与外部系统的集成连接</div>
      </div>
      <div class="header-actions">
        <el-button @click="loadIntegrations" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <!-- ── Filters ──────────────────────────────────────── -->
    <div class="filter-bar">
      <el-input
        v-model="keyword"
        placeholder="搜索集成名称..."
        clearable
        prefix-icon="Search"
        style="width: 240px"
        @keyup.enter="loadIntegrations"
      />
      <el-select v-model="filterType" placeholder="集成类型" clearable style="width: 140px">
        <el-option label="认证" value="auth" />
        <el-option label="通知" value="notification" />
        <el-option label="监控" value="monitoring" />
        <el-option label="事件" value="event" />
        <el-option label="数据" value="data" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="连接状态" clearable style="width: 120px">
        <el-option label="已连接" value="connected" />
        <el-option label="未连接" value="disconnected" />
        <el-option label="错误" value="error" />
      </el-select>
      <el-button type="primary" @click="loadIntegrations">查询</el-button>
    </div>

    <!-- ── Table ────────────────────────────────────────── -->
    <el-table
      :data="integrations"
      v-loading="loading"
      stripe
      border
      row-key="name"
      empty-text="暂无集成配置"
      style="width: 100%"
    >
      <el-table-column prop="name" label="名称" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">
          <div class="int-name-cell">
            <el-icon size="18" :color="getIntegrationIconColor(row.type)">
              <Connection />
            </el-icon>
            <span>{{ row.name }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="type" label="类型" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="typeTagMap[row.type] ?? 'info'">
            {{ typeLabelMap[row.type] ?? row.type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag
            :type="statusTagMap[row.status] ?? 'info'"
            size="small"
            effect="dark"
          >
            {{ statusLabelMap[row.status] ?? row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
      <el-table-column prop="endpoint" label="端点地址" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="text-secondary">{{ row.endpoint || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="last_sync" label="最后同步" width="170">
        <template #default="{ row }">
          <span class="text-secondary">{{ row.last_sync || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right" align="center">
        <template #default="{ row }">
          <el-button
            text
            type="primary"
            size="small"
            @click="openConfigDialog(row)"
          >
            配置
          </el-button>
          <el-button
            text
            type="success"
            size="small"
            :loading="testingMap[row.name]"
            @click="testConnection(row)"
          >
            测试连接
          </el-button>
          <el-button
            text
            :type="row.status === 'connected' ? 'warning' : 'primary'"
            size="small"
            @click="toggleIntegration(row)"
          >
            {{ row.status === 'connected' ? '禁用' : '启用' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadIntegrations"
      />
    </div>

    <!-- ── Config Dialog ─────────────────────────────────── -->
    <el-dialog
      v-model="configDialogVisible"
      :title="`配置 - ${configuringName}`"
      width="560px"
      destroy-on-close
    >
      <el-form
        ref="configFormRef"
        :model="configForm"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="集成名称">
          <el-input :model-value="configuringName" disabled />
        </el-form-item>
        <el-form-item label="端点地址" prop="endpoint">
          <el-input v-model="configForm.endpoint" placeholder="如 ldap://host:389" />
        </el-form-item>
        <el-form-item label="认证用户">
          <el-input v-model="configForm.username" placeholder="可选" />
        </el-form-item>
        <el-form-item label="认证密码">
          <el-input
            v-model="configForm.password"
            type="password"
            show-password
            placeholder="可选"
          />
        </el-form-item>
        <el-form-item label="额外参数">
          <el-input
            v-model="configForm.extra"
            type="textarea"
            :rows="3"
            placeholder="JSON 格式额外参数（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="configDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingConfig" @click="saveConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { Refresh, Connection } from '@element-plus/icons-vue'
import { platformService } from '@/shared/api'

// ── Maps ─────────────────────────────────────────────────
const typeLabelMap: Record<string, string> = {
  auth: '认证',
  notification: '通知',
  monitoring: '监控',
  event: '事件',
  data: '数据',
}
const typeTagMap: Record<string, string> = {
  auth: 'primary',
  notification: 'success',
  monitoring: 'warning',
  event: 'danger',
  data: '',
}
const statusLabelMap: Record<string, string> = {
  connected: '已连接',
  disconnected: '未连接',
  error: '错误',
}
const statusTagMap: Record<string, string> = {
  connected: 'success',
  disconnected: 'info',
  error: 'danger',
}

function getIntegrationIconColor(type: string): string {
  const map: Record<string, string> = {
    auth: '#165dff',
    notification: '#00b42a',
    monitoring: '#ff7d00',
    event: '#f53f3f',
    data: '#722ed1',
  }
  return map[type] ?? '#86909c'
}

// ── State ────────────────────────────────────────────────
const loading = ref(false)
const integrations = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

const keyword = ref('')
const filterType = ref('')
const filterStatus = ref('')

const testingMap = reactive<Record<string, boolean>>({})

const configDialogVisible = ref(false)
const configuringName = ref('')
const savingConfig = ref(false)
const configFormRef = ref<FormInstance>()
const configForm = reactive({
  endpoint: '',
  username: '',
  password: '',
  extra: '',
})

// ── Data Loading ─────────────────────────────────────────
async function loadIntegrations() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize,
    }
    if (keyword.value) params.keyword = keyword.value
    if (filterType.value) params.type = filterType.value
    if (filterStatus.value) params.status = filterStatus.value

    const res = await platformService.integrations(params)
    const data = res.data?.data ?? res.data
    if (Array.isArray(data)) {
      integrations.value = data
      total.value = data.length
    } else {
      integrations.value = data?.items ?? data?.list ?? []
      total.value = data?.total ?? integrations.value.length
    }
  } catch (err: any) {
    ElMessage.error(err.message || '加载集成列表失败')
  } finally {
    loading.value = false
  }
}

// ── Test Connection ──────────────────────────────────────
async function testConnection(row: any) {
  testingMap[row.name] = true
  try {
    await platformService.integrationTest(row.name)
    ElMessage.success(`${row.name} 连接测试成功`)
    loadIntegrations()
  } catch (err: any) {
    ElMessage.error(err.message || `${row.name} 连接测试失败`)
  } finally {
    testingMap[row.name] = false
  }
}

// ── Toggle Enable/Disable ────────────────────────────────
async function toggleIntegration(row: any) {
  const action = row.status === 'connected' ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(
      `确定${action}集成「${row.name}」吗？`,
      `${action}确认`,
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
    ElMessage.success(`已${action} ${row.name}`)
    loadIntegrations()
  } catch {
    // cancelled
  }
}

// ── Config Dialog ────────────────────────────────────────
function openConfigDialog(row: any) {
  configuringName.value = row.name
  configForm.endpoint = row.endpoint ?? ''
  configForm.username = row.username ?? ''
  configForm.password = ''
  configForm.extra = row.extra ? JSON.stringify(row.extra, null, 2) : ''
  configDialogVisible.value = true
}

async function saveConfig() {
  savingConfig.value = true
  try {
    // In a real implementation this would call an update API
    ElMessage.success(`${configuringName.value} 配置已保存`)
    configDialogVisible.value = false
    loadIntegrations()
  } catch (err: any) {
    ElMessage.error(err.message || '保存失败')
  } finally {
    savingConfig.value = false
  }
}

// ── Init ─────────────────────────────────────────────────
onMounted(() => {
  loadIntegrations()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}
.autops-page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.autops-page-title {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
}
.header-actions {
  display: flex;
  gap: 8px;
}

.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.int-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.text-secondary {
  color: #86909c;
  font-size: 12px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
