<template>
  <div class="collector-page">
    <!-- 页面头部 -->
    <div class="autops-page-header">
      <span class="autops-page-title">采集器管理</span>
    </div>

    <!-- ========== Tab 切换：本地采集器 / Edge采集器 ========== -->
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <!-- ========== 本地采集器 Tab ========== -->
      <el-tab-pane label="本地采集器" name="local">
    <div class="autops-card mb-lg">
      <div class="autops-card-header">
        <span class="autops-card-title">采集器管理</span>
        <div class="autops-toolbar-right">
          <el-button type="primary" @click="openTriggerDialog">
            <el-icon><VideoPlay /></el-icon> 手动触发采集
          </el-button>
          <el-button @click="loadCollectors">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>
      </div>
      <div class="autops-card-body">

      <!-- Filters -->
      <el-form :inline="true" class="autops-toolbar">
        <el-form-item label="搜索">
          <el-input
            v-model="collectorFilters.search"
            placeholder="名称搜索"
            clearable
            style="width: 200px"
            @clear="loadCollectors"
            @keyup.enter="loadCollectors"
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="collectorFilters.collector_type" placeholder="全部" clearable @change="loadCollectors">
            <el-option v-for="t in collectorTypes" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="collectorFilters.status" placeholder="全部" clearable @change="loadCollectors">
            <el-option label="健康" value="healthy" />
            <el-option label="降级" value="degraded" />
            <el-option label="离线" value="offline" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadCollectors">查询</el-button>
        </el-form-item>
      </el-form>

      <!-- Table -->
      <el-table stripe :data="collectors" v-loading="collectorLoading"row-key="id">
        <el-table-column prop="name" label="名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="collector_type" label="类型" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="typeTagMap[row.collector_type] || 'info'">
              {{ formatCollectorType(row.collector_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="protocol" label="协议" width="90">
          <template #default="{ row }">{{ row.protocol || '-' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <StatusBadge :status="row.status" show-icon size="small" />
          </template>
        </el-table-column>
        <el-table-column label="能力" min-width="180">
          <template #default="{ row }">
            <div class="capability-tags">
              <el-tag
                v-for="cap in (row.capabilities || []).slice(0, 3)"
                :key="cap"
                size="small"
                type="info"
                effect="plain"
                class="cap-tag"
              >
                {{ cap }}
              </el-tag>
              <el-tag v-if="(row.capabilities || []).length > 3" size="small" type="info" effect="plain">
                +{{ row.capabilities.length - 3 }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="last_seen_at" label="最后上报" width="170">
          <template #default="{ row }">{{ formatTime(row.last_seen_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openDetailDialog(row)">详情</el-button>
            <el-button size="small" type="warning" @click="triggerSingleCollector(row)">触发</el-button>
            <el-popconfirm title="确定删除此采集器？" @confirm="deleteCollector(row.id)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="collectorPagination.page"
        v-model:page-size="collectorPagination.pageSize"
        :total="collectorPagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        class="pagination"
        @change="loadCollectors"
      />
      </div>
    </div>

    <!-- ========== 采集任务列表 ========== -->
    <div class="autops-card">
      <div class="autops-card-header">
        <span class="autops-card-title">采集任务</span>
        <el-select
          v-model="jobFilters.status"
          placeholder="全部状态"
          clearable
          style="width: 150px"
          @change="loadJobs"
        >
          <el-option label="待执行" value="pending" />
          <el-option label="运行中" value="running" />
          <el-option label="成功" value="success" />
          <el-option label="失败" value="failed" />
        </el-select>
      </div>
      <div class="autops-card-body">

      <el-table stripe :data="jobs" v-loading="jobLoading"row-key="id" size="default">
        <el-table-column prop="collector_name" label="采集器" min-width="130" show-overflow-tooltip />
        <el-table-column prop="asset_name" label="资产" min-width="130" show-overflow-tooltip />
        <el-table-column prop="job_type" label="任务类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ formatJobType(row.job_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <StatusBadge :status="row.status" show-icon size="small" />
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="170">
          <template #default="{ row }">{{ formatTime(row.started_at) }}</template>
        </el-table-column>
        <el-table-column label="耗时" width="100">
          <template #default="{ row }">
            <span v-if="row.duration">{{ row.duration }}s</span>
            <span v-else-if="row.started_at && row.status === 'running'">
              {{ calcRunningDuration(row.started_at) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="结果预览" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.result_preview" class="result-preview">{{ row.result_preview }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewJobResult(row)" :disabled="row.status !== 'success'">
              结果
            </el-button>
            <el-button size="small" type="info" @click="viewJobLogs(row)">日志</el-button>
            <el-button
              size="small"
              type="warning"
              @click="retryJob(row)"
              :disabled="row.status !== 'failed'"
            >
              重试
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="jobPagination.page"
        v-model:page-size="jobPagination.pageSize"
        :total="jobPagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        class="pagination"
        @change="loadJobs"
      />
      </div>
    </div>

    <!-- ========== 采集器详情对话框 ========== -->
    <el-dialog v-model="showDetailDialog" title="采集器详情" width="780px" destroy-on-close>
      <template v-if="currentCollector">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ currentCollector.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag size="small">{{ formatCollectorType(currentCollector.collector_type) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="协议">{{ currentCollector.protocol || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusBadge :status="currentCollector.status" show-icon />
          </el-descriptions-item>
          <el-descriptions-item label="最后上报">{{ formatTime(currentCollector.last_seen_at) }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTime(currentCollector.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="ID" :span="2">{{ currentCollector.id }}</el-descriptions-item>
        </el-descriptions>

        <!-- Capabilities -->
        <div class="detail-section">
          <h4 class="detail-subtitle">采集能力</h4>
          <div class="capability-list">
            <el-tag
              v-for="cap in (currentCollector.capabilities || [])"
              :key="cap"
              class="cap-tag"
              effect="plain"
            >
              {{ cap }}
            </el-tag>
            <span v-if="!currentCollector.capabilities?.length" class="text-muted">暂无能力信息</span>
          </div>
        </div>

        <!-- Recent Health Checks -->
        <div class="detail-section">
          <h4 class="detail-subtitle">最近健康检查</h4>
          <el-table stripe
 v-if="healthChecks.length"
 :data="healthChecks"
 size="small"max-height="200"
 >
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <StatusBadge :status="row.status" size="small" />
              </template>
            </el-table-column>
            <el-table-column prop="message" label="信息" min-width="200" show-overflow-tooltip />
            <el-table-column prop="checked_at" label="检查时间" width="170">
              <template #default="{ row }">{{ formatTime(row.checked_at) }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无健康检查记录" :image-size="60" />
        </div>

        <!-- Configuration -->
        <div class="detail-section">
          <h4 class="detail-subtitle">配置信息</h4>
          <JsonViewer
            v-if="currentCollector.config"
            :data="currentCollector.config"
          />
          <span v-else class="text-muted">暂无配置信息</span>
        </div>
      </template>
    </el-dialog>

    <!-- ========== 任务结果对话框 ========== -->
    <el-dialog v-model="showResultDialog" title="采集结果" width="780px" destroy-on-close>
      <template v-if="currentJob">
        <el-descriptions :column="2" border size="small" style="margin-bottom: 16px">
          <el-descriptions-item label="采集器">{{ currentJob.collector_name }}</el-descriptions-item>
          <el-descriptions-item label="资产">{{ currentJob.asset_name }}</el-descriptions-item>
          <el-descriptions-item label="任务类型">{{ formatJobType(currentJob.job_type) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusBadge :status="currentJob.status" show-icon size="small" />
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatTime(currentJob.started_at) }}</el-descriptions-item>
          <el-descriptions-item label="耗时">{{ currentJob.duration ? currentJob.duration + 's' : '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="detail-section">
          <h4 class="detail-subtitle">结果数据</h4>
          <JsonViewer v-if="jobResultData" :data="jobResultData" />
          <el-empty v-else description="暂无结果数据" :image-size="60" />
        </div>
      </template>
    </el-dialog>

    <!-- ========== 任务日志对话框 ========== -->
    <el-dialog v-model="showLogDialog" title="采集日志" width="780px" destroy-on-close>
      <template v-if="currentJob">
        <el-descriptions :column="2" border size="small" style="margin-bottom: 16px">
          <el-descriptions-item label="采集器">{{ currentJob.collector_name }}</el-descriptions-item>
          <el-descriptions-item label="资产">{{ currentJob.asset_name }}</el-descriptions-item>
        </el-descriptions>
        <div class="log-container">
          <pre v-if="jobLogs" class="log-content">{{ jobLogs }}</pre>
          <el-empty v-else description="暂无日志" :image-size="60" />
        </div>
      </template>
    </el-dialog>

    <!-- ========== 手动触发对话框 ========== -->
    <el-dialog v-model="showTriggerDialog" title="手动触发采集" width="600px" destroy-on-close>
      <el-form :model="triggerForm" label-width="90px">
        <el-form-item label="采集器" required>
          <el-select
            v-model="triggerForm.collector_id"
            placeholder="选择采集器"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="c in collectors"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            >
              <span>{{ c.name }}</span>
              <el-tag size="small" style="margin-left: 8px">{{ formatCollectorType(c.collector_type) }}</el-tag>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="资产ID" required>
          <el-input v-model="triggerForm.asset_id" placeholder="输入资产 ID" />
        </el-form-item>
        <el-form-item label="任务类型">
          <el-select v-model="triggerForm.job_type" placeholder="选择任务类型" style="width: 100%">
            <el-option label="全量采集" value="full_collect" />
            <el-option label="增量采集" value="incremental_collect" />
            <el-option label="状态检查" value="health_check" />
            <el-option label="配置采集" value="config_collect" />
          </el-select>
        </el-form-item>
        <el-form-item label="参数">
          <el-input
            v-model="triggerForm.params"
            type="textarea"
            :rows="3"
            placeholder="可选，JSON 格式参数"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTriggerDialog = false">取消</el-button>
        <el-button type="primary" :loading="triggering" @click="submitTrigger">触发采集</el-button>
      </template>
    </el-dialog>
      </el-tab-pane>

      <!-- ========== Edge 采集器 Tab ========== -->
      <el-tab-pane label="Edge采集器" name="edge">
        <!-- Edge 状态统计 + 刷新 -->
        <div class="autops-card">
          <div class="autops-card-header">
            <span class="autops-card-title">Edge 采集器管理</span>
            <div class="autops-toolbar-right">
              <el-tag type="success" class="edge-stat-tag">在线: {{ edgeOnlineCount }}</el-tag>
              <el-tag type="danger" class="edge-stat-tag">离线: {{ edgeOfflineCount }}</el-tag>
              <el-button @click="loadEdgeCollectors">
                <el-icon><Refresh /></el-icon> 刷新
              </el-button>
            </div>
          </div>
          <div class="autops-card-body">

          <!-- Edge 采集器表格 -->
          <el-table stripe :data="edgeCollectors" v-loading="edgeLoading"row-key="collector_id">
            <el-table-column prop="collector_id" label="Collector ID" min-width="180" show-overflow-tooltip />
            <el-table-column prop="name" label="名称" min-width="130" show-overflow-tooltip>
              <template #default="{ row }">{{ row.name || '-' }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="110">
              <template #default="{ row }">
                <el-tag
                  size="small"
                  :type="edgeStatusTagType(row.status)"
                >
                  {{ edgeStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="last_heartbeat" label="最后心跳" width="170">
              <template #default="{ row }">{{ formatTime(row.last_heartbeat) }}</template>
            </el-table-column>
            <el-table-column prop="ip" label="IP" width="140">
              <template #default="{ row }">{{ row.ip || '-' }}</template>
            </el-table-column>
            <el-table-column prop="version" label="版本" width="100">
              <template #default="{ row }">{{ row.version || '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="viewEdgeStatus(row)">查看状态</el-button>
                <el-button size="small" type="primary" @click="viewEdgeTasks(row)">查看任务</el-button>
                <el-popconfirm title="确定删除此 Edge 采集器？" @confirm="deleteEdgeCollector(row.collector_id)">
                  <template #reference>
                    <el-button size="small" type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- ========== Edge 查看状态对话框 ========== -->
    <el-dialog v-model="showEdgeStatusDialog" title="Edge 采集器状态" width="780px" destroy-on-close>
      <div v-if="edgeStatusData" class="detail-section">
        <JsonViewer :data="edgeStatusData" />
      </div>
      <el-empty v-else description="暂无状态数据" :image-size="60" />
    </el-dialog>

    <!-- ========== Edge 查看任务对话框 ========== -->
    <el-dialog v-model="showEdgeTasksDialog" title="Edge 采集器任务" width="780px" destroy-on-close>
      <template v-if="currentEdgeCollector">
        <el-descriptions :column="2" border size="small" style="margin-bottom: 16px">
          <el-descriptions-item label="Collector ID">{{ currentEdgeCollector.collector_id }}</el-descriptions-item>
          <el-descriptions-item label="名称">{{ currentEdgeCollector.name || '-' }}</el-descriptions-item>
        </el-descriptions>
      </template>
      <el-table stripe :data="edgeTasks" v-loading="edgeTasksLoading"size="default">
        <el-table-column prop="task_id" label="任务ID" min-width="160" show-overflow-tooltip />
        <el-table-column prop="task_type" label="类型" width="120">
          <template #default="{ row }">{{ row.task_type || '-' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="edgeTaskStatusTagType(row.status)">{{ row.status || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="result" label="结果" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ row.result || '-' }}</template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Refresh, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import JsonViewer from '@/shared/components/JsonViewer.vue'

// ---------- Types ----------
interface Collector {
  id: string
  name: string
  collector_type: string
  protocol: string
  status: string
  capabilities: string[]
  last_seen_at: string
  created_at: string
  config?: Record<string, any>
}

interface CollectionJob {
  id: string
  collector_id: string
  collector_name: string
  asset_id: string
  asset_name: string
  job_type: string
  status: string
  started_at: string
  duration?: number
  result_preview?: string
  result_data?: any
  logs?: string
}

interface HealthCheck {
  status: string
  message: string
  checked_at: string
}

// ---------- Edge Types ----------
interface EdgeCollector {
  collector_id: string
  name: string
  status: string
  last_heartbeat: string
  ip: string
  version: string
  [key: string]: any
}

interface EdgeTask {
  task_id: string
  task_type: string
  status: string
  created_at: string
  result: string
  [key: string]: any
}

// ---------- Constants ----------
const collectorTypes = [
  { label: 'SSH', value: 'ssh' },
  { label: 'WMI', value: 'wmi' },
  { label: 'HTTP', value: 'http' },
  { label: 'TCP', value: 'tcp' },
  { label: '数据库', value: 'db' },
  { label: '证书', value: 'cert' },
]

const typeTagMap: Record<string, string> = {
  ssh: '', wmi: 'success', http: 'warning', tcp: 'info', db: 'danger', cert: '',
}

const jobTypeMap: Record<string, string> = {
  full_collect: '全量采集',
  incremental_collect: '增量采集',
  health_check: '状态检查',
  config_collect: '配置采集',
}

// ---------- Collector State ----------
const collectorLoading = ref(false)
const collectors = ref<Collector[]>([])
const collectorFilters = reactive({
  search: '',
  collector_type: '',
  status: '',
})
const collectorPagination = reactive({ page: 1, pageSize: 20, total: 0 })

// ---------- Job State ----------
const jobLoading = ref(false)
const jobs = ref<CollectionJob[]>([])
const jobFilters = reactive({ status: '' })
const jobPagination = reactive({ page: 1, pageSize: 20, total: 0 })

// ---------- Dialog State ----------
const showDetailDialog = ref(false)
const currentCollector = ref<Collector | null>(null)
const healthChecks = ref<HealthCheck[]>([])

const showResultDialog = ref(false)
const currentJob = ref<CollectionJob | null>(null)
const jobResultData = ref<any>(null)

const showLogDialog = ref(false)
const jobLogs = ref<string>('')

const showTriggerDialog = ref(false)
const triggering = ref(false)
const triggerForm = reactive({
  collector_id: '',
  asset_id: '',
  job_type: 'full_collect',
  params: '',
})

// ---------- Tab State ----------
const activeTab = ref('local')

// ---------- Edge Collector State ----------
const edgeLoading = ref(false)
const edgeCollectors = ref<EdgeCollector[]>([])
const showEdgeStatusDialog = ref(false)
const edgeStatusData = ref<any>(null)
const showEdgeTasksDialog = ref(false)
const currentEdgeCollector = ref<EdgeCollector | null>(null)
const edgeTasks = ref<EdgeTask[]>([])
const edgeTasksLoading = ref(false)

// ---------- Helpers ----------
function formatTime(t: string | undefined | null): string {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

function formatCollectorType(type: string): string {
  const found = collectorTypes.find(t => t.value === type)
  return found ? found.label : type
}

function formatJobType(type: string): string {
  return jobTypeMap[type] || type
}

function calcRunningDuration(startedAt: string): string {
  const diff = Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000)
  if (diff < 60) return `${diff}s`
  const min = Math.floor(diff / 60)
  const sec = diff % 60
  return `${min}m${sec}s`
}

// ---------- Collector API ----------
async function loadCollectors() {
  collectorLoading.value = true
  try {
    const params: Record<string, any> = {
      page: collectorPagination.page,
      page_size: collectorPagination.pageSize,
    }
    if (collectorFilters.search) params.search = collectorFilters.search
    if (collectorFilters.collector_type) params.collector_type = collectorFilters.collector_type
    if (collectorFilters.status) params.status = collectorFilters.status

    const { data } = await api.get(R.COLLECTORS, { params })
    if (data.code === 0) {
      collectors.value = data.data.items || []
      collectorPagination.total = data.data.total || 0
    }
  } catch (e: any) {
    ElMessage.error('加载采集器失败: ' + (e.message || e))
  } finally {
    collectorLoading.value = false
  }
}

async function deleteCollector(id: string) {
  try {
    const { data } = await api.delete(`${R.COLLECTORS}/${id}`)
    if (data.code === 0) {
      ElMessage.success('已删除')
      loadCollectors()
    } else {
      ElMessage.error(data.message || '删除失败')
    }
  } catch (e: any) {
    ElMessage.error('删除失败: ' + (e.message || e))
  }
}

// ---------- Collector Detail ----------
async function openDetailDialog(row: Collector) {
  currentCollector.value = row
  showDetailDialog.value = true
  healthChecks.value = []

  try {
    const { data } = await api.get(`${R.COLLECTORS}/${row.id}/health-checks`, {
      params: { page: 1, page_size: 10 },
    })
    if (data.code === 0) {
      healthChecks.value = data.data.items || data.data || []
    }
  } catch {
    // health checks are optional, silently ignore
  }
}

// ---------- Trigger Single Collector ----------
function triggerSingleCollector(row: Collector) {
  triggerForm.collector_id = row.id
  triggerForm.asset_id = ''
  triggerForm.job_type = 'full_collect'
  triggerForm.params = ''
  showTriggerDialog.value = true
}

function openTriggerDialog() {
  triggerForm.collector_id = ''
  triggerForm.asset_id = ''
  triggerForm.job_type = 'full_collect'
  triggerForm.params = ''
  showTriggerDialog.value = true
}

async function submitTrigger() {
  if (!triggerForm.collector_id || !triggerForm.asset_id) {
    ElMessage.warning('请选择采集器并输入资产 ID')
    return
  }

  triggering.value = true
  try {
    const payload: Record<string, any> = {
      collector_id: triggerForm.collector_id,
      asset_id: triggerForm.asset_id,
      job_type: triggerForm.job_type,
    }
    if (triggerForm.params) {
      try {
        payload.params = JSON.parse(triggerForm.params)
      } catch {
        ElMessage.warning('参数必须是合法的 JSON 格式')
        triggering.value = false
        return
      }
    }

    const { data } = await api.post(R.COLLECTION_JOBS, payload)
    if (data.code === 0) {
      ElMessage.success('采集任务已触发')
      showTriggerDialog.value = false
      loadJobs()
    } else {
      ElMessage.error(data.message || '触发失败')
    }
  } catch (e: any) {
    ElMessage.error('触发失败: ' + (e.message || e))
  } finally {
    triggering.value = false
  }
}

// ---------- Jobs API ----------
async function loadJobs() {
  jobLoading.value = true
  try {
    const params: Record<string, any> = {
      page: jobPagination.page,
      page_size: jobPagination.pageSize,
    }
    if (jobFilters.status) params.status = jobFilters.status

    const { data } = await api.get(R.COLLECTION_JOBS, { params })
    if (data.code === 0) {
      jobs.value = data.data.items || []
      jobPagination.total = data.data.total || 0
    }
  } catch (e: any) {
    ElMessage.error('加载采集任务失败: ' + (e.message || e))
  } finally {
    jobLoading.value = false
  }
}

async function viewJobResult(job: CollectionJob) {
  currentJob.value = job
  jobResultData.value = null
  showResultDialog.value = true

  try {
    const { data } = await api.get(R.COLLECTION_JOB_RESULTS(job.id))
    if (data.code === 0) {
      jobResultData.value = data.data
    }
  } catch {
    // fallback to inline data if endpoint fails
    if (job.result_data) {
      jobResultData.value = job.result_data
    }
  }
}

async function viewJobLogs(job: CollectionJob) {
  currentJob.value = job
  jobLogs.value = ''
  showLogDialog.value = true

  try {
    const { data } = await api.get(`${R.COLLECTION_JOBS}/${job.id}/logs`)
    if (data.code === 0) {
      jobLogs.value = typeof data.data === 'string' ? data.data : JSON.stringify(data.data, null, 2)
    }
  } catch {
    // fallback to inline logs
    if (job.logs) {
      jobLogs.value = job.logs
    }
  }
}

async function retryJob(job: CollectionJob) {
  try {
    await ElMessageBox.confirm(
      `确定重试采集任务「${job.collector_name} - ${job.asset_name}」？`,
      '确认重试',
      { type: 'warning' },
    )

    const { data } = await api.post(`${R.COLLECTION_JOBS}/${job.id}/retry`)
    if (data.code === 0) {
      ElMessage.success('已重新触发')
      loadJobs()
    } else {
      ElMessage.error(data.message || '重试失败')
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('重试失败: ' + (e.message || e))
    }
  }
}

// ---------- Edge Computed ----------
const edgeOnlineCount = computed(() => {
  return edgeCollectors.value.filter(c => c.status === 'healthy' || c.status === 'degraded').length
})

const edgeOfflineCount = computed(() => {
  return edgeCollectors.value.filter(c => c.status === 'offline').length
})

// ---------- Edge Helpers ----------
function edgeStatusTagType(status: string): string {
  switch (status) {
    case 'healthy': return 'success'
    case 'degraded': return 'warning'
    case 'offline': return 'danger'
    default: return 'info'
  }
}

function edgeStatusLabel(status: string): string {
  switch (status) {
    case 'healthy': return '健康'
    case 'degraded': return '降级'
    case 'offline': return '离线'
    default: return status || '未知'
  }
}

function edgeTaskStatusTagType(status: string): string {
  switch (status) {
    case 'success': return 'success'
    case 'running': return ''
    case 'pending': return 'info'
    case 'failed': return 'danger'
    default: return 'info'
  }
}

// ---------- Edge API ----------
async function loadEdgeCollectors() {
  edgeLoading.value = true
  try {
    // 调用 Edge 状态列表接口
    const { data } = await api.get(R.COLLECTOR_EDGE)
    if (data.code === 0) {
      edgeCollectors.value = data.data?.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载 Edge 采集器失败: ' + (e.message || e))
  } finally {
    edgeLoading.value = false
  }
}

async function viewEdgeStatus(row: EdgeCollector) {
  edgeStatusData.value = null
  showEdgeStatusDialog.value = true
  try {
    const { data } = await api.get(R.EDGE_STATUS(row.collector_id))
    if (data.code === 0) {
      edgeStatusData.value = data.data
    }
  } catch (e: any) {
    ElMessage.error('获取 Edge 状态失败: ' + (e.message || e))
  }
}

async function viewEdgeTasks(row: EdgeCollector) {
  currentEdgeCollector.value = row
  edgeTasks.value = []
  edgeTasksLoading.value = true
  showEdgeTasksDialog.value = true
  try {
    const { data } = await api.get(R.EDGE_TASKS(row.collector_id))
    if (data.code === 0) {
      edgeTasks.value = data.data?.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('获取 Edge 任务失败: ' + (e.message || e))
  } finally {
    edgeTasksLoading.value = false
  }
}

async function deleteEdgeCollector(collectorId: string) {
  try {
    const { data } = await api.delete(R.COLLECTOR_EDGE_DETAIL(collectorId))
    if (data.code === 0) {
      ElMessage.success('Edge 采集器已删除')
      loadEdgeCollectors()
    } else {
      ElMessage.error(data.message || '删除失败')
    }
  } catch (e: any) {
    ElMessage.error('删除 Edge 采集器失败: ' + (e.message || e))
  }
}

// ---------- Tab Change ----------
function handleTabChange(tab: string | number) {
  if (tab === 'edge' && edgeCollectors.value.length === 0) {
    loadEdgeCollectors()
  }
}

// ---------- Init ----------
onMounted(() => {
  loadCollectors()
  loadJobs()
  // 如果当前 Tab 为 edge，也加载 Edge 数据
  if (activeTab.value === 'edge') {
    loadEdgeCollectors()
  }
})
</script>

<style scoped>
.collector-page {
  padding: 0;
}

.section-card {
  margin-bottom: 20px;
}
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.filter-form {
  margin-bottom: 16px;
}

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

.capability-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.cap-tag {
  font-size: 12px;
}

.result-preview {
  font-size: 12px;
  color: #4e5969;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
}

.text-muted {
  color: #86909c;
  font-size: 13px;
}

.detail-section {
  margin-top: 20px;
}

.detail-subtitle {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid #e5e6eb;
}

.capability-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.log-container {
  background: #f7f8fa;
  border-radius: 6px;
  padding: 12px;
  max-height: 400px;
  overflow: auto;
}

.log-content {
  font-size: 13px;
  line-height: 1.6;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  color: #1d2129;
}

/* Element Plus overrides for consistency */
:deep(.el-descriptions__label) {
  width: 100px;
  font-weight: 500;
}

:deep(.el-dialog__body) {
  padding-top: 16px;
  padding-bottom: 8px;
}

.edge-stat-tag {
  font-size: 13px;
  padding: 0 12px;
  height: 32px;
  line-height: 30px;
}
</style>
