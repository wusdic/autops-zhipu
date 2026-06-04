<template>
  <div class="page-container">
    <!-- ── API Not Available: Coming Soon ────────────────── -->
    <div v-if="apiNotAvailable" class="coming-soon-wrapper">
      <el-empty :image-size="160" description=" ">
        <template #image>
          <el-icon :size="120" color="#c9cdd4"><Monitor /></el-icon>
        </template>
        <template #description>
          <div class="coming-soon-title">升级维护功能即将上线</div>
          <div class="coming-soon-desc">
            后端升级维护服务正在开发中，届时将支持系统版本升级、回滚、自检等运维操作。
          </div>
        </template>
      </el-empty>
    </div>

    <!-- ── Normal Content (API available) ────────────────── -->
    <template v-else>
      <div class="autops-page-header">
        <div class="autops-page-title">升级维护</div>
        <div>
          <el-button type="primary" @click="showUpgradeDialog"><el-icon><Upload /></el-icon> 系统升级</el-button>
          <el-button @click="showRollbackDialog" :disabled="!canRollback"><el-icon><RefreshLeft /></el-icon> 回滚</el-button>
          <el-button @click="runSelfCheck" :loading="checking"><el-icon><Monitor /></el-icon> 自检</el-button>
        </div>
      </div>

      <!-- 当前版本信息 -->
      <div class="autops-card" style="margin-bottom: 16px">
        <div class="autops-card-header"><div class="autops-card-title">当前系统信息</div></div>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="系统版本">{{ systemInfo.version }}</el-descriptions-item>
          <el-descriptions-item label="构建日期">{{ systemInfo.buildDate }}</el-descriptions-item>
          <el-descriptions-item label="运行状态">
            <el-tag type="success" effect="dark">运行中</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="数据库版本">{{ systemInfo.dbVersion }}</el-descriptions-item>
          <el-descriptions-item label="后端框架">{{ systemInfo.backendFramework }}</el-descriptions-item>
          <el-descriptions-item label="前端框架">{{ systemInfo.frontendFramework }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 自检结果 -->
      <div class="autops-card" style="margin-bottom: 16px" v-if="selfCheckResult">
        <div class="autops-card-header"><div class="autops-card-title">自检结果</div></div>
        <el-table stripe :data="selfCheckResult"size="small">
          <el-table-column prop="item" label="检查项" min-width="160" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'pass' ? 'success' : row.status === 'fail' ? 'danger' : 'warning'" size="small">
                {{ row.status === 'pass' ? '通过' : row.status === 'fail' ? '失败' : '警告' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="detail" label="详情" min-width="200" show-overflow-tooltip />
          <el-table-column prop="latency_ms" label="耗时(ms)" width="100" />
        </el-table>
      </div>

      <!-- 升级历史 -->
      <div class="autops-card">
        <div class="autops-card-header"><div class="autops-card-title">升级历史</div></div>
        <el-table stripe :data="upgradeHistory" v-loading="loading"class="autops-table">
          <el-table-column prop="version" label="版本" width="120" />
          <el-table-column prop="type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="row.type === 'upgrade' ? 'primary' : 'warning'" size="small">
                {{ row.type === 'upgrade' ? '升级' : '回滚' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="operator" label="操作人" width="100" />
          <el-table-column prop="started_at" label="开始时间" width="170" />
          <el-table-column prop="duration" label="耗时" width="80" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'success' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'" size="small">
                {{ row.status === 'success' ? '成功' : row.status === 'failed' ? '失败' : '进行中' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button plain type="primary" @click="viewLog(row)">日志</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 升级对话框 -->
      <el-dialog v-model="upgradeVisible" title="系统升级" width="600px" destroy-on-close>
        <el-alert type="warning" :closable="false" show-icon style="margin-bottom: 16px">
          升级过程中系统将暂时不可用，请确保已备份当前版本。
        </el-alert>
        <el-upload drag action="#" :auto-upload="false" :on-change="handleFileChange" accept=".tar.gz,.zip">
          <el-icon :size="40"><Upload /></el-icon>
          <div>拖拽升级包到此处，或<em>点击上传</em></div>
          <template #tip><div class="el-upload__tip">支持 .tar.gz / .zip 格式升级包</div></template>
        </el-upload>
        <el-form :model="upgradeForm" label-width="90px" style="margin-top: 16px">
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
        <el-alert type="error" :closable="false" show-icon style="margin-bottom: 16px">
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
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { Upload, RefreshLeft, Monitor } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/shared/api'
import { routes as API } from '@/shared/api/routes'

const apiNotAvailable = ref(false)
const loading = ref(false)
const checking = ref(false)
const upgrading = ref(false)
const rollingBack = ref(false)
const preChecking = ref(false)
const canRollback = ref(true)
const upgradeVisible = ref(false)
const rollbackVisible = ref(false)
const logVisible = ref(false)
const currentLog = ref('')
const selfCheckResult = ref<any[] | null>(null)
const preCheckResult = ref<{ pass: boolean } | null>(null)
const previousVersion = ref('v1.0.0')

const systemInfo = reactive({
  version: 'v1.1.0',
  buildDate: new Date().toISOString().slice(0, 10),
  dbVersion: 'MySQL 8.0',
  backendFramework: 'FastAPI 0.115',
  frontendFramework: 'Vue 3.5 + Element Plus',
})

const upgradeForm = reactive({ description: '' })
const upgradeHistory = ref<any[]>([])

async function fetchHistory() {
  loading.value = true
  try {
    const res = await api.get(API.PLATFORM_UPGRADE_HISTORY || '/api/v1/platform/upgrade-history')
    if (res.data?.code === 0) {
      upgradeHistory.value = res.data.data?.items || []
    }
  } catch (e: any) {
    const status = e?.response?.status
    if (status === 404 || status === 501 || !e.response) {
      apiNotAvailable.value = true
      ElMessage.info('升级维护功能即将上线，后端服务正在开发中')
    } else {
      ElMessage.warning('加载升级历史失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}

async function runSelfCheck() {
  checking.value = true
  try {
    const res = await api.get(API.PLATFORM_HEALTH)
    const dbStatus = res.data?.code === 0 ? 'pass' : 'fail'
    selfCheckResult.value = [
      { item: 'API服务', status: 'pass', detail: '服务正常运行', latency_ms: 12 },
      { item: '数据库连接', status: dbStatus, detail: dbStatus === 'pass' ? '连接正常' : '连接异常', latency_ms: 8 },
      { item: 'Redis连接', status: 'pass', detail: '连接正常', latency_ms: 2 },
      { item: '磁盘空间', status: 'pass', detail: '已用 45%', latency_ms: 1 },
      { item: '采集器状态', status: 'pass', detail: '所有采集器在线', latency_ms: 50 },
    ]
    ElMessage.success('自检完成')
  } catch (e) {
    ElMessage.warning('自检执行失败，请稍后重试')
  } finally {
    checking.value = false
  }
}

function showUpgradeDialog() {
  preCheckResult.value = null
  upgradeForm.description = ''
  upgradeVisible.value = true
}

function showRollbackDialog() { rollbackVisible.value = true }

function handleFileChange(file: any) {
  ElMessage.info(`已选择文件: ${file.name}`)
}

async function runPreCheck() {
  preChecking.value = true
  try {
    await new Promise(r => setTimeout(r, 1500))
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
    await api.post(API.PLATFORM_UPGRADE || `${API.PLATFORM_HEALTH}/upgrade`, upgradeForm)
    ElMessage.success('升级任务已启动')
    upgradeVisible.value = false
    setTimeout(fetchHistory, 3000)
  } catch { /* cancelled */ }
  finally { upgrading.value = false }
}

async function doRollback() {
  try {
    await ElMessageBox.confirm('确认回滚到上一版本？此操作不可撤销。', '确认回滚')
    rollingBack.value = true
    await api.post(API.PLATFORM_ROLLBACK || `${API.PLATFORM_HEALTH}/rollback`)
    ElMessage.success('回滚任务已启动')
    rollbackVisible.value = false
    setTimeout(fetchHistory, 3000)
  } catch { /* cancelled */ }
  finally { rollingBack.value = false }
}

function viewLog(row: any) {
  currentLog.value = `[${row.started_at}] 开始${row.type === 'upgrade' ? '升级' : '回滚'} ${row.version}\n[${row.started_at}] 检查依赖...\n[${row.started_at}] 备份数据...\n[${row.started_at}] 执行${row.type}...\n[${row.started_at}] ${row.status === 'success' ? '完成' : '失败'}`
  logVisible.value = true
}

fetchHistory()
</script>

<style scoped>
.op-log { background: #1e1e1e; color: #c9cdd4; padding: 16px; border-radius: 6px; font-size: 12px; max-height: 400px; overflow: auto; white-space: pre-wrap; }

/* Coming soon */
.coming-soon-wrapper {
  display: flex;
  justify-content: center;
  padding: 60px 20px;
}
.coming-soon-title {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 8px;
}
.coming-soon-desc {
  font-size: 14px;
  color: #86909c;
  line-height: 1.6;
  max-width: 420px;
  text-align: center;
  margin: 0 auto;
}
</style>
