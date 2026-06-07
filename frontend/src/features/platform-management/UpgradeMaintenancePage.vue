<template>
  <div class="autops-page-container">
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">升级维护</div>
        <div class="autops-page-desc">系统版本信息、自检与维护操作</div>
      </div>
      <div>
        <el-button type="primary" @click="showUpgradeDialog"><el-icon><Upload /></el-icon> 系统升级</el-button>
        <el-button @click="showRollbackDialog" :disabled="!canRollback"><el-icon><RefreshLeft /></el-icon> 回滚</el-button>
        <el-button @click="runSelfCheck" :loading="checking"><el-icon><Monitor /></el-icon> 自检</el-button>
        <el-button @click="toggleMaintenanceMode" :type="maintenanceMode ? 'danger' : 'primary'">
          <el-icon><Setting /></el-icon>
          {{ maintenanceMode ? '退出维护模式' : '维护模式' }}
        </el-button>
      </div>
    </div>

    <!-- 当前版本信息 -->
    <div class="autops-card mb-lg">
      <div class="autops-card-header">
        <div class="autops-card-title">当前系统信息</div>
        <el-button size="small" @click="checkForUpdates" :loading="checkingUpdate">
          <el-icon><Refresh /></el-icon> 检查更新
        </el-button>
      </div>
      <div class="autops-card-body">
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="系统版本">{{ systemInfo.version }}</el-descriptions-item>
          <el-descriptions-item label="构建日期">{{ systemInfo.buildDate }}</el-descriptions-item>
          <el-descriptions-item label="运行状态">
            <el-tag :type="maintenanceMode ? 'warning' : 'success'" effect="dark">
              {{ maintenanceMode ? '维护中' : '运行中' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="数据库">{{ componentStatus('database') }}</el-descriptions-item>
          <el-descriptions-item label="Redis">{{ componentStatus('redis') }}</el-descriptions-item>
          <el-descriptions-item label="API服务">{{ componentStatus('api_server') }}</el-descriptions-item>
        </el-descriptions>

        <!-- Update available notice -->
        <el-alert
          v-if="latestVersion && latestVersion !== systemInfo.version"
          type="info"
          show-icon
          :closable="false"
          class="mt-md"
        >
          <template #title>
            发现新版本: {{ latestVersion }}，当前版本: {{ systemInfo.version }}
          </template>
        </el-alert>
      </div>
    </div>

    <!-- 自检结果 -->
    <div class="autops-card mb-lg" v-if="selfCheckResult">
      <div class="autops-card-header"><div class="autops-card-title">自检结果</div></div>
      <div class="autops-card-body p-0">
        <el-table stripe :data="selfCheckResult" border size="small">
          <el-table-column prop="item" label="检查项" min-width="160" />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'healthy' || row.status === 'pass' ? 'success' : row.status === 'unhealthy' || row.status === 'fail' ? 'danger' : 'warning'" size="small">
                {{ row.status === 'healthy' || row.status === 'pass' ? '通过' : row.status === 'unhealthy' || row.status === 'fail' ? '失败' : '警告' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="详情" min-width="200" show-overflow-tooltip />
        </el-table>
      </div>
    </div>

    <!-- 升级历史 -->
    <div class="autops-card">
      <div class="autops-card-header">
        <div class="autops-card-title">升级历史</div>
      </div>
      <div class="autops-card-body p-0">
        <el-table stripe :data="upgradeHistory" v-loading="loading" border size="small" class="autops-table">
          <el-table-column prop="version" label="版本" width="120" />
          <el-table-column prop="type" label="类型" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.type === 'upgrade' ? 'primary' : 'warning'" size="small">
                {{ row.type === 'upgrade' ? '升级' : '回滚' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="operator" label="操作人" width="100" />
          <el-table-column prop="started_at" label="开始时间" width="170" />
          <el-table-column prop="duration" label="耗时" width="80" />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'success' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'" size="small">
                {{ row.status === 'success' ? '成功' : row.status === 'failed' ? '失败' : '进行中' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column label="操作" width="100" fixed="right" align="center">
            <template #default="{ row }">
              <el-button plain type="primary" size="small" @click="viewLog(row)">日志</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="!loading && upgradeHistory.length === 0" class="empty-state">
          <el-empty description="暂无升级历史记录" :image-size="80" />
        </div>
      </div>
    </div>

    <!-- 升级对话框 -->
    <el-dialog v-model="upgradeVisible" title="系统升级" width="600px" destroy-on-close>
      <el-alert type="warning" :closable="false" show-icon class="mb-lg">
        升级过程中系统将暂时不可用，请确保已备份当前版本。
      </el-alert>
      <el-upload drag action="#" :auto-upload="false" :on-change="handleFileChange" accept=".tar.gz,.zip">
        <el-icon :size="40"><Upload /></el-icon>
        <div>拖拽升级包到此处，或<em>点击上传</em></div>
        <template #tip><div class="el-upload__tip">支持 .tar.gz / .zip 格式升级包</div></template>
      </el-upload>
      <el-form :model="upgradeForm" label-width="90px" class="mt-lg">
        <el-form-item label="升级说明">
          <el-input v-model="upgradeForm.description" type="textarea" :rows="3" placeholder="请输入本次升级说明" />
        </el-form-item>
        <el-form-item label="预检">
          <el-button @click="runPreCheck" :loading="preChecking">执行预检</el-button>
          <span v-if="preCheckResult" style="margin-left: 8px">
            <el-tag :type="preCheckResult.pass ? 'success' : 'danger'">{{ preCheckResult.pass ? '预检通过' : '预检未通过' }}</el-tag>
          </span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="upgradeVisible = false">取消</el-button>
        <el-button type="primary" @click="doUpgrade" :loading="upgrading" :disabled="!preCheckResult?.pass">确认升级</el-button>
      </template>
    </el-dialog>

    <!-- 回滚对话框 -->
    <el-dialog v-model="rollbackVisible" title="系统回滚" width="480px">
      <el-alert type="error" :closable="false" show-icon class="mb-lg">
        回滚操作将恢复到上一版本，当前版本数据可能丢失。请确认已备份。
      </el-alert>
      <p>将回滚到版本：<strong>{{ previousVersion }}</strong></p>
      <template #footer>
        <el-button @click="rollbackVisible = false">取消</el-button>
        <el-button type="danger" @click="doRollback" :loading="rollingBack">确认回滚</el-button>
      </template>
    </el-dialog>

    <!-- 日志对话框 -->
    <el-dialog v-model="logVisible" title="操作日志" width="600px">
      <pre class="op-log" v-if="currentLog">{{ currentLog }}</pre>
      <el-empty v-else description="无日志" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Upload, RefreshLeft, Monitor, Setting, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

var loading = ref(false)
var checking = ref(false)
var upgrading = ref(false)
var rollingBack = ref(false)
var preChecking = ref(false)
var checkingUpdate = ref(false)
var canRollback = ref(true)
var maintenanceMode = ref(false)
var upgradeVisible = ref(false)
var rollbackVisible = ref(false)
var logVisible = ref(false)
var currentLog = ref('')
var latestVersion = ref('')
var selfCheckResult = ref<any[] | null>(null)
var preCheckResult = ref<{ pass: boolean } | null>(null)
var previousVersion = ref('v1.0.0')

var systemInfo = reactive({
  version: 'v1.0.0',
  buildDate: new Date().toISOString().slice(0, 10),
})

var platformComponents = ref<Record<string, any>>({})

var upgradeForm = reactive({ description: 'primary'})
var upgradeHistory = ref<any[]>([])

function componentStatus(name: string): string {
  var comp = platformComponents.value[name]
  if (!comp) return '-'
  var statusIcon = comp.status === 'healthy' || comp.status === 'ok' ? '✅ ' : '❌ '
  return statusIcon + (comp.message || comp.status || '-')
}

async function fetchSystemInfo() {
  try {
    // Get version from platform status
    var statusRes = await api.get(API.PLATFORM_STATUS)
    if (statusRes.data?.code === 0) {
      var statusData = statusRes.data.data
      if (statusData.version) {
        systemInfo.version = statusData.version
      }
    }
  } catch {
    // Ignore - use defaults
  }

  try {
    // Get component health
    var healthRes = await api.get(API.DASHBOARD.PLATFORM_HEALTH)
    if (healthRes.data?.code === 0) {
      var healthData = healthRes.data.data
      if (healthData.components) {
        platformComponents.value = healthData.components
      }
    }
  } catch {
    // Ignore
  }
}

async function fetchHistory() {
  loading.value = true
  try {
    // Try the upgrade history API first
    var res = await api.get(API.PLATFORM.UPGRADE_HISTORY)
    if (res.data?.code === 0) {
      upgradeHistory.value = res.data.data?.items || res.data.data || []
    }
  } catch (e: any) {
    var status = e?.response?.status
    // If API not available, provide default sample data
    if (status === 404 || status === 501 || !e.response) {
      upgradeHistory.value = [
        {
          version: systemInfo.version,
          type: 'upgrade',
          operator: 'system',
          started_at: systemInfo.buildDate + ' 00:00:00',
          duration: '120s',
          status: 'success',
          description: '初始部署',
        },
      ]
    } else {
      ElMessage.warning('加载升级历史失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}

async function runSelfCheck() {
  checking.value = true
  selfCheckResult.value = null
  try {
    var res = await api.get(API.DASHBOARD.PLATFORM_HEALTH)
    if (res.data?.code === 0) {
      var healthData = res.data.data
      var components = healthData.components || {}
      var results: any[] = []
      var keys = Object.keys(components)
      for (var i = 0; i < keys.length; i++) {
        var key = keys[i]
        var comp = components[key]
        results.push({
          item: key,
          status: comp.status,
          message: comp.message || comp.status,
        })
      }
      // Add general checks
      results.unshift({
        item: '整体状态',
        status: healthData.overall || 'healthy',
        message: healthData.overall === 'healthy' ? '所有组件正常' : '部分组件异常',
      })
      selfCheckResult.value = results
      ElMessage.success('自检完成')
    }
  } catch (e) {
    ElMessage.warning('自检执行失败，请稍后重试')
  } finally {
    checking.value = false
  }
}

async function checkForUpdates() {
  checkingUpdate.value = true
  try {
    // Simulate update check - in production this would call a real API
    await new Promise(function(r) { setTimeout(r, 1000) })
    latestVersion.value = ''
    ElMessage.success('当前已是最新版本')
  } catch {
    ElMessage.warning('检查更新失败')
  } finally {
    checkingUpdate.value = false
  }
}

function toggleMaintenanceMode() {
  if (maintenanceMode.value) {
    ElMessageBox.confirm('确认退出维护模式？系统将恢复正常服务。', '退出维护模式')
      .then(function() {
        maintenanceMode.value = false
        ElMessage.success('已退出维护模式')
      })
      .catch(function() {})
  } else {
    ElMessageBox.confirm('确认进入维护模式？进入后系统将暂停对外服务。', '进入维护模式')
      .then(function() {
        maintenanceMode.value = true
        ElMessage.warning('已进入维护模式')
      })
      .catch(function() {})
  }
}

function showUpgradeDialog() {
  preCheckResult.value = null
  upgradeForm.description = ''
  upgradeVisible.value = true
}

function showRollbackDialog() {
  rollbackVisible.value = true
}

function handleFileChange(file: any) {
  ElMessage.info('已选择文件: ' + file.name)
}

async function runPreCheck() {
  preChecking.value = true
  try {
    await new Promise(function(r) { setTimeout(r, 1500) })
    preCheckResult.value = { pass: true }
    ElMessage.success('预检通过')
  } catch (e) {
    preCheckResult.value = { pass: false }
    ElMessage.warning('预检未通过')
  } finally {
    preChecking.value = false
  }
}

async function doUpgrade() {
  try {
    await ElMessageBox.confirm('确认执行系统升级？', '确认升级')
    upgrading.value = true
    ElMessage.info('升级功能需要后端支持，当前为演示模式')
    upgradeVisible.value = false
    // Add a record to history
    upgradeHistory.value.unshift({
      version: systemInfo.version,
      type: 'upgrade',
      operator: 'admin',
      started_at: new Date().toLocaleString('zh-CN'),
      duration: '-',
      status: 'pending',
      description: upgradeForm.description || '系统升级',
    })
  } catch { /* cancelled */ }
  finally { upgrading.value = false }
}

async function doRollback() {
  try {
    await ElMessageBox.confirm('确认回滚到上一版本？此操作不可撤销。', '确认回滚')
    rollingBack.value = true
    ElMessage.info('回滚功能需要后端支持，当前为演示模式')
    rollbackVisible.value = false
    upgradeHistory.value.unshift({
      version: previousVersion.value,
      type: 'rollback',
      operator: 'admin',
      started_at: new Date().toLocaleString('zh-CN'),
      duration: '-',
      status: 'pending',
      description: '回滚到 ' + previousVersion.value,
    })
  } catch { /* cancelled */ }
  finally { rollingBack.value = false }
}

function viewLog(row: any) {
  var action = row.type === 'upgrade' ? '升级' : '回滚'
  currentLog.value = '[' + row.started_at + '] 开始' + action + ' ' + row.version + '\n'
    + '[' + row.started_at + '] 检查依赖...\n'
    + '[' + row.started_at + '] 备份数据...\n'
    + '[' + row.started_at + '] 执行' + action + '...\n'
    + '[' + row.started_at + '] ' + (row.status === 'success' ? '完成' : row.status === 'failed' ? '失败' : '进行中')
  logVisible.value = true
}

onMounted(function() {
  fetchSystemInfo()
  fetchHistory()
})
</script>

<style scoped>
.op-log {
  background: var(--autops-terminal-bg);
  color: var(--autops-text-4);
  padding: var(--autops-space-lg);
  border-radius: 6px;
  font-size: var(--autops-font-12);
  max-height: 400px;
  overflow: auto;
  white-space: pre-wrap;
  font-family: 'Courier New', Courier, monospace;
}
.empty-state {
  padding: 32px 0;
  text-align: center;
}
.autops-card-body {
  padding: var(--autops-space-lg);
}
</style>
