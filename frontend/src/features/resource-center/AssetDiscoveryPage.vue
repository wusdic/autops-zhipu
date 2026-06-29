<template>
  <div class="autops-page-container">
    <PageHeader title="资源发现" desc="扫描网段自动发现资产并纳管" />

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row mb-lg">
      <el-col :xs="12" :sm="6">
        <div class="autops-metric-card">
          <div class="metric-icon bg-brand"><el-icon size="20"><Search /></el-icon></div>
          <div class="metric-label">已发现资产</div>
          <div class="metric-value">{{ stats.total_discovered }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="autops-metric-card">
          <div class="metric-icon bg-success"><el-icon size="20"><CircleCheckFilled /></el-icon></div>
          <div class="metric-label">已纳管</div>
          <div class="metric-value">{{ stats.onboarded }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="autops-metric-card">
          <div class="metric-icon bg-warning"><el-icon size="20"><Clock /></el-icon></div>
          <div class="metric-label">待审核</div>
          <div class="metric-value">{{ stats.pending_review }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="autops-metric-card">
          <div class="metric-icon bg-info"><el-icon size="20"><Plus /></el-icon></div>
          <div class="metric-label">今日发现</div>
          <div class="metric-value">{{ stats.today }}</div>
        </div>
      </el-col>
    </el-row>

    <el-tabs v-model="activeTab" class="main-tabs">
      <!-- 发现任务 -->
      <el-tab-pane label="发现任务" name="tasks">
        <div class="autops-toolbar">
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon> 新建发现任务
          </el-button>
          <el-button @click="loadTasks"><el-icon><Refresh /></el-icon> 刷新</el-button>
          <span v-if="hasRunningTasks" class="polling-hint">
            <el-icon class="is-loading"><Refresh /></el-icon> 任务执行中，自动刷新…
          </span>
        </div>

        <el-alert
          v-if="hasRunningTasks"
          type="info" :closable="false" show-icon class="mb-2"
          title="有任务正在执行（每 5 秒自动刷新）。若长时间停留在「运行中」不完成，请确认采集 Worker(autops-worker) 是否在运行。"
        />

        <el-table stripe :data="tasks" v-loading="loading">
          <el-table-column type="index" label="序号" width="60" />
          <el-table-column prop="name" label="任务名称" min-width="180" show-overflow-tooltip />
          <el-table-column label="IP范围" min-width="180">
            <template #default="{ row }">
              <span v-if="row.ip_range">{{ row.ip_range }}</span>
              <span v-else-if="row.ip_start">{{ row.ip_start }} - {{ row.ip_end }}</span>
              <span v-else-if="row.cidr">{{ row.cidr }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="protocol" label="协议" width="100">
            <template #default="{ row }">
              <el-tag size="small">{{ row.protocol || 'ICMP' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="(taskStatusType(row.status)) as TagType" size="small">{{ taskStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="discovered_count" label="发现数" width="90" />
          <el-table-column prop="started_at" label="开始时间" width="170">
            <template #default="{ row }">{{ formatTime(row.started_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.status === 'pending'" size="small" type="primary" @click="startTask(row)">启动</el-button>
              <el-button v-if="row.status === 'running'" size="small" type="warning" @click="stopTask(row)">停止</el-button>
              <el-button v-if="row.status === 'completed'" size="small" type="success" @click="viewResults(row)">查看结果</el-button>
              <el-button size="small" @click="deleteTask(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination v-if="taskTotal > taskPagination.pageSize" class="pagination"
          :current-page="taskPagination.page" :page-size="taskPagination.pageSize"
          :total="taskTotal" @current-change="(p: number) => { taskPagination.page = p; loadTasks() }"
          layout="total, prev, pager, next" />
      </el-tab-pane>

      <!-- 发现结果 -->
      <el-tab-pane label="发现结果" name="results">
        <div class="autops-toolbar">
          <el-select v-model="resultFilter.status" placeholder="状态" clearable style="width:130px;margin-right:8px">
            <el-option label="新发现" value="new" /><el-option label="已纳管" value="managed" />
            <el-option label="已变更" value="changed" /><el-option label="忽略" value="ignored" />
          </el-select>
          <el-select v-model="resultFilter.asset_type" placeholder="类型" clearable style="width:130px;margin-right:8px">
            <el-option label="Linux" value="linux_server" /><el-option label="Windows" value="windows_server" />
            <el-option label="网络设备" value="network_device" /><el-option label="数据库" value="database" />
            <el-option label="Web服务" value="web_service" />
          </el-select>
          <el-input v-model="resultFilter.keyword" placeholder="IP/主机名" clearable style="width:200px;margin-right:8px" @clear="loadResults" @keyup.enter="loadResults" />
          <el-button type="primary" @click="loadResults"><el-icon><Search /></el-icon> 搜索</el-button>
          <el-button @click="batchOnboard" :disabled="!selectedResults.length" type="success">
            批量纳管 ({{ selectedResults.length }})
          </el-button>
        </div>

        <el-table stripe :data="results" v-loading="resultLoading"@selection-change="(s: any[]) => selectedResults = s">
          <el-table-column type="selection" width="50" />
          <el-table-column prop="ip" label="IP地址" width="150" />
          <el-table-column prop="hostname" label="主机名" min-width="140" />
          <el-table-column prop="asset_type" label="资产类型" width="120">
            <template #default="{ row }">
              <el-tag size="small">{{ row.asset_type || '未知' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="开放端口" min-width="150">
            <template #default="{ row }">
              <span v-if="row.open_ports">{{ row.open_ports.join(', ') }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="os_info" label="操作系统" min-width="140" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="(resultStatusType(row.status)) as TagType" size="small">{{ resultStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="discovered_at" label="发现时间" width="170">
            <template #default="{ row }">{{ formatTime(row.discovered_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.status === 'discovered' || row.status === 'new'" size="small" type="primary" @click="startOnboard([row])">纳管</el-button>
              <el-button v-if="row.status === 'managed' || row.status === 'onboarded'" size="small" @click="viewAsset(row)">查看</el-button>
              <el-button v-if="row.status === 'discovered' || row.status === 'new'" size="small" @click="ignoreResult(row)">忽略</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 纳管向导 -->
      <el-tab-pane label="纳管向导" name="wizard" v-if="wizardActive">
        <el-steps :active="wizardStep" finish-status="success" class="wizard-steps">
          <el-step title="选择资产" /><el-step title="配置凭证" />
          <el-step title="采集配置" /><el-step title="确认纳管" />
        </el-steps>

        <!-- 步骤1：选择资产 -->
        <div v-if="wizardStep === 0" class="wizard-content">
          <el-table stripe :data="wizardAssets"@selection-change="(s: any[]) => wizardSelected = s">
            <el-table-column type="selection" width="50" />
            <el-table-column prop="ip" label="IP地址" width="150" />
            <el-table-column prop="hostname" label="主机名" min-width="140" />
            <el-table-column prop="asset_type" label="类型" width="120" />
            <el-table-column prop="open_ports" label="开放端口" min-width="120">
              <template #default="{ row }">
                <span v-if="row.open_ports">{{ row.open_ports.join(', ') }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
          <div class="wizard-actions">
            <el-button @click="wizardActive = false">取消</el-button>
            <el-button type="primary" :disabled="!wizardSelected.length" @click="wizardStep = 1">下一步 ({{ wizardSelected.length }} 个资产)</el-button>
          </div>
        </div>

        <!-- 步骤2：配置凭证 -->
        <div v-if="wizardStep === 1" class="wizard-content">
          <el-form label-width="100px">
            <el-form-item label="选择凭证">
              <el-select v-model="wizardCredential" placeholder="选择已有凭证" style="width:300px">
                <el-option v-for="c in credentials" :key="c.id" :label="c.name + ' (' + c.credential_type + ')'" :value="c.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="或新建凭证">
              <el-button @click="showNewCredDialog = true">创建新凭证</el-button>
            </el-form-item>
            <el-form-item label="连接测试">
              <el-button @click="testConnection" :loading="testing" type="success">测试连接</el-button>
              <el-tag v-if="testResult === 'success'" type="success" style="margin-left:10px">连接成功</el-tag>
              <el-tag v-if="testResult === 'failed'" type="danger" style="margin-left:10px">连接失败</el-tag>
            </el-form-item>
          </el-form>
          <div class="wizard-actions">
            <el-button @click="wizardStep = 0">上一步</el-button>
            <el-button type="primary" @click="wizardStep = 2">下一步</el-button>
          </div>
        </div>

        <!-- 步骤3：采集配置 -->
        <div v-if="wizardStep === 2" class="wizard-content">
          <el-form label-width="120px">
            <el-form-item label="采集模板">
              <el-select v-model="wizardCollectionTemplate" placeholder="选择采集模板" style="width:300px" clearable>
                <el-option label="默认Linux采集" value="default_linux" />
                <el-option label="默认Windows采集" value="default_windows" />
                <el-option label="数据库巡检" value="database_check" />
                <el-option label="Web服务检查" value="web_check" />
              </el-select>
            </el-form-item>
            <el-form-item label="采集频率">
              <el-select v-model="wizardInterval" style="width:200px">
                <el-option label="每5分钟" value="300" /><el-option label="每15分钟" value="900" />
                <el-option label="每30分钟" value="1800" /><el-option label="每小时" value="3600" />
              </el-select>
            </el-form-item>
            <el-form-item label="资产分组">
              <el-select v-model="wizardGroup" placeholder="选择分组" style="width:300px" clearable>
                <el-option v-for="g in assetGroups" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
          </el-form>
          <div class="wizard-actions">
            <el-button @click="wizardStep = 1">上一步</el-button>
            <el-button type="primary" @click="wizardStep = 3">下一步</el-button>
          </div>
        </div>

        <!-- 步骤4：确认纳管 -->
        <div v-if="wizardStep === 3" class="wizard-content">
          <el-descriptions title="纳管确认" :column="2" border>
            <el-descriptions-item label="资产数量">{{ wizardSelected.length }} 个</el-descriptions-item>
            <el-descriptions-item label="凭证">{{ getCredentialName(wizardCredential) }}</el-descriptions-item>
            <el-descriptions-item label="采集模板">{{ wizardCollectionTemplate || '不配置' }}</el-descriptions-item>
            <el-descriptions-item label="采集频率">{{ wizardInterval }}秒</el-descriptions-item>
            <el-descriptions-item label="资产分组">{{ getGroupName(wizardGroup) || '不分组' }}</el-descriptions-item>
          </el-descriptions>
          <div class="wizard-assets-preview">
            <h4>待纳管资产列表</h4>
            <el-table stripe :data="wizardSelected"size="small">
              <el-table-column prop="ip" label="IP" width="150" />
              <el-table-column prop="hostname" label="主机名" min-width="140" />
              <el-table-column prop="asset_type" label="类型" width="120" />
            </el-table>
          </div>
          <div class="wizard-actions">
            <el-button @click="wizardStep = 2">上一步</el-button>
            <el-button type="primary" @click="executeOnboard" :loading="onboarding" size="large">确认纳管</el-button>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 创建发现任务对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建发现任务" width="600px">
      <el-form :model="newTask" label-width="100px" :rules="taskRules" ref="taskFormRef">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="newTask.name" placeholder="例如: 办公网段扫描" />
        </el-form-item>
        <el-form-item label="IP范围">
          <el-radio-group v-model="newTask.ipMode">
            <el-radio value="range">起止IP</el-radio>
            <el-radio value="cidr">CIDR</el-radio>
          </el-radio-group>
          <div v-if="newTask.ipMode === 'range'" style="display:flex;gap:8px;margin-top:8px">
            <el-input v-model="newTask.ip_start" placeholder="起始IP" />
            <span>-</span>
            <el-input v-model="newTask.ip_end" placeholder="结束IP" />
          </div>
          <el-input v-if="newTask.ipMode === 'cidr'" v-model="newTask.cidr" placeholder="192.168.1.0/24" style="margin-top:8px" />
        </el-form-item>
        <el-form-item label="发现模板">
          <el-select
            v-model="newTask.template_id"
            placeholder="可选：选择模板自动套用协议/端口/凭据"
            clearable
            style="width:100%"
            @change="onTemplatePick"
          >
            <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="协议">
          <el-checkbox-group v-model="newTask.protocols">
            <el-tooltip content="ICMP Ping：探测主机可达性（在线/离线）" placement="top">
              <el-checkbox value="icmp" label="ICMP" />
            </el-tooltip>
            <el-tooltip content="TCP 端口扫描：探测开放端口、推断资产类型" placement="top">
              <el-checkbox value="tcp" label="TCP" />
            </el-tooltip>
            <el-tooltip content="SNMP：采集网络设备指纹（需 community/凭证）" placement="top">
              <el-checkbox value="snmp" label="SNMP" />
            </el-tooltip>
            <el-tooltip content="SSH：探测可登录性（需 SSH 凭证）" placement="top">
              <el-checkbox value="ssh" label="SSH" />
            </el-tooltip>
          </el-checkbox-group>
          <div style="font-size:12px;color:var(--autops-info);margin-top:4px">
            勾选探测协议；ICMP 判在线性，TCP 扫端口推断类型。
          </div>
        </el-form-item>
        <el-form-item label="端口范围">
          <el-input v-model="newTask.ports" placeholder="22,80,443,3389 或留空" />
        </el-form-item>
        <el-form-item label="凭证">
          <el-select v-model="newTask.credential_id" placeholder="选择凭证(可选)" clearable style="width:100%">
            <el-option v-for="c in credentials" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="超时(秒)">
          <el-input-number v-model="newTask.timeout" :min="5" :max="600" />
        </el-form-item>
        <el-form-item label="自动纳管">
          <el-switch v-model="newTask.auto_onboard" />
          <span style="margin-left:8px;color:var(--autops-text-3);font-size:12px">开启后建任务即自动扫描，扫描完成自动纳管全部存活IP</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createTask">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import type { TagType } from '@/shared/types'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Search, CircleCheckFilled, Clock } from '@element-plus/icons-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import { useWorkflowNav } from '@/shared/composables/useWorkflowNav'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()
const route = useRoute()

const { navToDiscovery } = useWorkflowNav()

// === 统计 ===
const stats = reactive({ total_discovered: 0, onboarded: 0, pending_review: 0, today: 0 })

// === Tab ===
// 支持 ?tab=results 深链（去重后 /resources/discovery-results 重定向至此）
const activeTab = ref(route.query.tab === 'results' ? 'results' : 'tasks')

// === 发现任务 ===
const tasks = ref<any[]>([])
const loading = ref(false)
const taskTotal = ref(0)
const taskPagination = reactive({ page: 1, pageSize: 20 })
const showCreateDialog = ref(false)
const taskFormRef = ref()
const newTask = reactive({
  name: '', ipMode: 'range' as 'range' | 'cidr',
  ip_start: '', ip_end: '', cidr: '',
  protocols: ['icmp', 'tcp'] as string[], ports: '',
  template_id: '', credential_id: '', timeout: 30,
  auto_onboard: true,
})
const taskRules = { name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }] }

// === 发现结果 ===
const results = ref<any[]>([])
const resultLoading = ref(false)
const selectedResults = ref<any[]>([])
const resultFilter = reactive({ status: '', asset_type: '', keyword: ''})

// === 纳管向导 ===
const wizardActive = ref(false)
const wizardStep = ref(0)
const wizardAssets = ref<any[]>([])
const wizardSelected = ref<any[]>([])
const wizardCredential = ref('')
const wizardCollectionTemplate = ref('default_linux')
const wizardInterval = ref('900')
const wizardGroup = ref('')
const credentials = ref<any[]>([])
const templates = ref<any[]>([])
const assetGroups = ref<any[]>([])
const testing = ref(false)
const testResult = ref('')
const onboarding = ref(false)
const showNewCredDialog = ref(false)

// === 加载函数 ===
async function loadStats() {
  // 已发现资产总数、已纳管、待审核、今日发现 均来自发现结果（discovery results），
  // 而非发现任务（tasks）。任务数 ≠ 资产数。
  try {
    const res = await api.get(API.DISCOVERY_RESULTS, { params: { page_size: 100 } })
    if (res.data?.code === 0) {
      const all = res.data.data?.items || res.data.data || []
      const total = res.data.data?.total ?? all.length
      stats.total_discovered = total
      stats.onboarded = all.filter((r: any) => r.status === 'managed').length
      stats.pending_review = all.filter((r: any) => r.status === 'new').length
      stats.today = all.filter((r: any) => {
        if (!r.discovered_at) return false
        return new Date(r.discovered_at).toDateString() === new Date().toDateString()
      }).length
    }
  } catch (e) {
    console.warn('loadStats 加载失败', e)
  }
}

async function loadTasks(silent = false) {
  if (!silent) loading.value = true
  try {
    const res = await api.get(API.DISCOVERY_TASKS, { params: { page: taskPagination.page, page_size: taskPagination.pageSize } })
    if (res.data?.code === 0) {
      tasks.value = res.data.data?.items || res.data.data || []
      taskTotal.value = res.data.data?.total || tasks.value.length
    }
  } catch { if (!silent) ElMessage.error('加载任务失败') }
  finally { if (!silent) loading.value = false }
}

// 有 pending/running 任务时静默轮询，完成后自动停止（无需手动刷新）
const hasRunningTasks = computed(() => tasks.value.some((t: any) => t.status === 'pending' || t.status === 'running'))
let pollTimer: ReturnType<typeof setInterval> | null = null
function startPolling() {
  if (pollTimer) return
  pollTimer = setInterval(() => {
    if (hasRunningTasks.value) {
      loadTasks(true); loadResults(); loadStats()
    }
  }, 5000)
}
function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

async function loadResults() {
  resultLoading.value = true
  try {
    const params: any = { page_size: 100 }
    if (resultFilter.status) params.status = resultFilter.status
    if (resultFilter.asset_type) params.asset_type = resultFilter.asset_type
    if (resultFilter.keyword) params.keyword = resultFilter.keyword
    const res = await api.get(API.DISCOVERY_RESULTS, { params })
    if (res.data?.code === 0) results.value = res.data.data?.items || res.data.data || []
  } catch { ElMessage.error('加载结果失败') }
  finally { resultLoading.value = false }
}

async function loadCredentials() {
  try {
    const res = await api.get(API.CREDENTIALS)
    if (res.data?.code === 0) credentials.value = res.data.data?.items || res.data.data || []
  } catch {}
}

async function loadTemplates() {
  try {
    const res = await api.get(API.DISCOVERY_TEMPLATES)
    if (res.data?.code === 0) templates.value = res.data.data?.items || res.data.data || []
  } catch {}
}

// 选模板后清空协议勾选，交由后端从模板继承（再勾选则视为覆盖）
function onTemplatePick(id: string) {
  if (id) newTask.protocols = []
}

async function loadAssetGroups() {
  try {
    const res = await api.get(API.ASSET_GROUPS)
    if (res.data?.code === 0) assetGroups.value = res.data.data?.items || res.data.data || []
  } catch {}
}

// === 任务操作 ===
async function createTask() {
  try {
    await taskFormRef.value?.validate()
    const payload: any = {
      name: newTask.name,
      timeout: newTask.timeout, auto_onboard: newTask.auto_onboard,
    }
    // 选了模板就让协议留空（由后端从模板继承）；否则用所选协议
    if (newTask.template_id) payload.template_id = newTask.template_id
    if (!newTask.template_id || (newTask.protocols && newTask.protocols.length)) {
      payload.protocols = newTask.protocols
    }
    if (newTask.ipMode === 'range') { payload.ip_start = newTask.ip_start; payload.ip_end = newTask.ip_end }
    else { payload.cidr = newTask.cidr }
    if (newTask.ports) payload.ports = newTask.ports
    if (newTask.credential_id) payload.credential_id = newTask.credential_id
    await api.post(API.DISCOVERY_TASKS, payload)
    ElMessage.success(newTask.auto_onboard ? '任务已创建并自动启动扫描' : '任务创建成功')
    showCreateDialog.value = false
    loadTasks()
  } catch (e: any) { ElMessage.error(e?.message || '创建失败') }
}

async function startTask(task: any) {
  try {
    await api.post(API.DISCOVERY_TASKS + '/' + task.id + '/start')
    ElMessage.success('任务已启动')
    loadTasks()
  } catch { ElMessage.error('启动失败') }
}

async function stopTask(task: any) {
  try {
    await api.post(API.DISCOVERY_TASKS + '/' + task.id + '/stop')
    ElMessage.success('任务已停止')
    loadTasks()
  } catch { ElMessage.error('停止失败') }
}

async function deleteTask(task: any) {
  try {
    await ElMessageBox.confirm('确定删除此任务？', '确认')
    await api.delete(API.DISCOVERY_TASKS + '/' + task.id)
    ElMessage.success('已删除')
    loadTasks()
  } catch (e: any) { if (e !== 'cancel' && e?.action !== 'cancel' && e?.message !== 'cancel') ElMessage.error('删除失败') }
}

function viewResults(task: any) {
  router.push({ path: '/resource-center/discovery/results', query: { task_id: task.id } })
}

// === 结果操作 ===
function startOnboard(items: any[]) {
  wizardActive.value = true
  wizardStep.value = 0
  wizardAssets.value = items
  wizardSelected.value = []
}

function batchOnboard() {
  if (!selectedResults.value.length) return
  startOnboard(selectedResults.value.filter(r => r.status === 'new' || r.status === 'discovered'))
}

async function ignoreResult(item: any) {
  try {
    await api.patch(API.DISCOVERY_RESULTS + '/' + item.id, { status: 'ignored' })
    ElMessage.success('已忽略')
    loadResults()
  } catch { ElMessage.error('操作失败') }
}

function viewAsset(item: any) {
  if (item.asset_id) router.push('/assets/' + item.asset_id)
}

async function testConnection() {
  if (!wizardCredential.value || !wizardSelected.value.length) return ElMessage.warning('请先选择凭证和资产')
  testing.value = true; testResult.value = ''
  try {
    const res = await api.post(API.CREDENTIALS + '/test', {
      credential_id: wizardCredential.value,
      target: wizardSelected.value[0]?.ip,
    })
    testResult.value = res.data?.code === 0 ? 'success' : 'failed'
  } catch { testResult.value = 'failed' }
  finally { testing.value = false }
}

async function executeOnboard() {
  onboarding.value = true
  try {
    for (const item of wizardSelected.value) {
      // 字段须与后端 AssetCreate 对齐：ip（非 ip_address）、os_type（非 os_info），
      // 否则纳管出的资产 IP/OS 为空，导致"资产已存在但部分页面不显示/无 IP"。
      await api.post(API.ASSETS, {
        name: item.hostname || item.ip,
        asset_type: item.asset_type || 'linux_server',
        ip: item.ip,
        hostname: item.hostname,
        os_type: item.os_info || item.os_type,
      })
    }
    ElMessage.success('成功纳管 ' + wizardSelected.value.length + ' 个资产')
    wizardActive.value = false
    wizardStep.value = 0
    loadResults(); loadStats()
  } catch (e: any) { ElMessage.error(e?.message || '纳管失败') }
  finally { onboarding.value = false }
}

// === 辅助 ===
function taskStatusType(s: string): TagType {
  const m: Record<string, TagType> = { pending: 'info', running: 'warning', completed: 'success', failed: 'danger' }
  return m[s] || 'info'
}
function taskStatusLabel(s: string) {
  const m: Record<string, string> = { pending: '待执行', running: '执行中', completed: '已完成', failed: '失败' }
  return m[s] || s
}
function resultStatusType(s: string): TagType {
  const m: Record<string, TagType> = { new: 'warning', discovered: 'warning', managed: 'success', onboarded: 'success', changed: 'danger', ignored: 'info' }
  return m[s] || 'info'
}
function resultStatusLabel(s: string) {
  const m: Record<string, string> = { new: '新发现', discovered: '新发现', managed: '已纳管', onboarded: '已纳管', changed: '已变更', ignored: '已忽略' }
  return m[s] || s
}
function formatTime(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '-' }
function getCredentialName(id: string) { return credentials.value.find(c => c.id === id)?.name || '-' }
function getGroupName(id: string) { return assetGroups.value.find(g => g.id === id)?.name || '-' }

// === 生命周期 ===
onMounted(() => { loadTasks(); loadResults(); loadStats(); loadCredentials(); loadAssetGroups(); loadTemplates(); startPolling() })
onBeforeUnmount(() => stopPolling())
</script>

<style scoped>
.stat-row { margin-bottom: var(--autops-space-xl); }
.autops-metric-card 
.autops-metric-card.success .stat-value { color: var(--autops-success); }
.autops-metric-card.warning .stat-value { color: var(--autops-warning); }
.autops-metric-card.primary .stat-value { color: var(--autops-primary); }
.autops-metric-card 
.toolbar { margin-bottom: var(--autops-space-lg); display: flex; gap: 8px; align-items: center; }
.pagination { margin-top: var(--autops-space-lg); display: flex; justify-content: flex-end; }
.wizard-steps { margin: 20px 0; }
.wizard-content { padding: var(--autops-space-xl); min-height: 300px; }
.wizard-actions { margin-top: 24px; display: flex; justify-content: flex-end; gap: 8px; }
.wizard-assets-preview { margin-top: var(--autops-space-xl); }
.wizard-assets-preview h4 { margin-bottom: 10px; color: var(--autops-text-2); }
.main-tabs { margin-top: var(--autops-space-lg); }
.polling-hint { margin-left: 12px; color: var(--autops-text-secondary, #909399); font-size: 13px; display: inline-flex; align-items: center; gap: 4px; }
.mb-2 { margin-bottom: 12px; }
</style>
