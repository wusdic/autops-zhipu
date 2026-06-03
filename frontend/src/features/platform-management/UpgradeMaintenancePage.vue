<template>
  <div class="page-container">
    <div class="autops-page-header">
      <h2>升级与维护</h2>
    </div>

    <!-- 当前版本 -->
    <el-card style="margin-bottom: 16px">
      <template #header><span>当前版本信息</span></template>
      <el-descriptions :column="3" border v-loading="loading">
        <el-descriptions-item label="版本号">{{ versionInfo.version || '-' }}</el-descriptions-item>
        <el-descriptions-item label="构建时间">{{ versionInfo.build_time || '-' }}</el-descriptions-item>
        <el-descriptions-item label="运行环境">{{ versionInfo.environment || 'production' }}</el-descriptions-item>
        <el-descriptions-item label="数据库状态">
          <el-tag :type="versionInfo.db_ok ? 'success' : 'danger'">{{ versionInfo.db_ok ? '正常' : '异常' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Redis状态">
          <el-tag :type="versionInfo.redis_ok ? 'success' : 'danger'">{{ versionInfo.redis_ok ? '正常' : '异常' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="运行时长">{{ versionInfo.uptime || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 维护模式 -->
    <el-card style="margin-bottom: 16px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>维护模式</span>
          <el-switch v-model="maintenanceMode" active-text="维护中" inactive-text="正常运行"
            @change="toggleMaintenance" :loading="togglingMaintenance" />
        </div>
      </template>
      <el-alert v-if="maintenanceMode" title="平台处于维护模式，仅管理员可访问" type="warning" show-icon :closable="false" />
      <el-alert v-else title="平台正常运行中" type="success" show-icon :closable="false" />
    </el-card>

    <!-- 操作按钮 -->
    <el-card style="margin-bottom: 16px">
      <template #header><span>系统操作</span></template>
      <el-row :gutter="16">
        <el-col :span="6">
          <el-button type="primary" @click="handleUpgrade" :loading="upgrading" style="width:100%">
            <el-icon><Upload /></el-icon> 系统升级
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button type="warning" @click="handleRollback" style="width:100%">
            <el-icon><RefreshLeft /></el-icon> 回滚
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button @click="handleBackup" :loading="backingUp" style="width:100%">
            <el-icon><FolderAdd /></el-icon> 手动备份
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button @click="fetchData" style="width:100%">
            <el-icon><Refresh /></el-icon> 刷新状态
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 升级历史 -->
    <el-card>
      <template #header><span>升级历史</span></template>
      <el-table :data="history" v-loading="loading" stripe>
        <el-table-column prop="version" label="版本" width="120" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.type === 'upgrade' ? 'primary' : row.type === 'rollback' ? 'warning' : 'info'">
              {{ row.type === 'upgrade' ? '升级' : row.type === 'rollback' ? '回滚' : row.type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'">
              {{ row.status === 'completed' ? '完成' : row.status === 'failed' ? '失败' : row.status === 'in_progress' ? '进行中' : row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="operator" label="操作人" width="100" />
        <el-table-column prop="created_at" label="时间" width="170">
          <template #default="{ row }">{{ row.created_at ? new Date(row.created_at).toLocaleString('zh-CN') : '-' }}</template>
        </el-table-column>
      </el-table>
      <div style="display:flex;justify-content:flex-end;margin-top:16px">
        <el-pagination v-model:current-page="page" v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]" :total="total" layout="total, sizes, prev, pager, next"
          @size-change="fetchHistory" @current-change="fetchHistory" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, RefreshLeft, FolderAdd, Refresh } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const loading = ref(false)
const upgrading = ref(false)
const backingUp = ref(false)
const togglingMaintenance = ref(false)
const maintenanceMode = ref(false)
const versionInfo = ref<Record<string, any>>({})
const history = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

async function fetchData() {
  loading.value = true
  try {
    const res = await client.get(API.PLATFORM_STATUS)
    const d = res.data?.data ?? res.data
    versionInfo.value = {
      version: d.version ?? '1.0.0',
      build_time: d.build_time ?? '-',
      environment: d.environment ?? 'production',
      db_ok: d.db_status === 'ok' || d.db_ok === true,
      redis_ok: d.redis_status === 'ok' || d.redis_ok === true,
      uptime: d.uptime ?? '-',
    }
    maintenanceMode.value = d.maintenance_mode ?? false
  } catch {
    versionInfo.value = { version: '1.0.0', build_time: '-', environment: 'production', db_ok: true, redis_ok: true, uptime: '-' }
  } finally { loading.value = false }
}

async function fetchHistory() {
  try {
    const res = await client.get(API.AUDIT, { params: { page: page.value, page_size: pageSize.value, action_category: 'system_upgrade' } })
    const d = res.data?.data ?? res.data
    history.value = d?.items ?? d?.results ?? (Array.isArray(d) ? d : [])
    total.value = d?.total ?? history.value.length
  } catch { history.value = [] }
}

async function toggleMaintenance(val: boolean) {
  togglingMaintenance.value = true
  try {
    await client.put(API.PLATFORM_STATUS, { maintenance_mode: val })
    ElMessage.success(val ? '已开启维护模式' : '已关闭维护模式')
  } catch { maintenanceMode.value = !val; ElMessage.error('操作失败') }
  finally { togglingMaintenance.value = false }
}

async function handleUpgrade() {
  try {
    await ElMessageBox.confirm('确认执行系统升级？升级期间服务将暂时不可用。', '系统升级', { type: 'warning' })
    upgrading.value = true
    await client.post('/api/v1/platform/upgrade')
    ElMessage.success('升级任务已启动')
    fetchHistory()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error('升级失败') }
  finally { upgrading.value = false }
}

async function handleRollback() {
  try {
    await ElMessageBox.confirm('确认回滚到上一版本？', '系统回滚', { type: 'warning' })
    await client.post('/api/v1/platform/rollback')
    ElMessage.success('回滚任务已启动')
    fetchHistory()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error('回滚失败') }
}

async function handleBackup() {
  try {
    backingUp.value = true
    await client.post(API.BACKUPS)
    ElMessage.success('备份任务已启动')
  } catch { ElMessage.error('备份失败') }
  finally { backingUp.value = false }
}

onMounted(() => { fetchData(); fetchHistory() })
</script>
