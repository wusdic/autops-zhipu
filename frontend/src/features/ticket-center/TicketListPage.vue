<template>
  <div class="ticket-list-page">
    <!-- ========== Page Header ========== -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">工单列表</div>
        <div class="autops-page-desc">统一管理事件工单，支持指派、升级、关闭与 SLA 跟踪</div>
      </div>
    </div>

    <!-- ========== Statistics Row ========== -->
    <el-row :gutter="16" class="stats-row mb-lg">
      <el-col :span="4">
        <div class="autops-card stat-card stat-card--total">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="28"><Tickets /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.total }}</div>
              <div class="stat-card__label">全部工单</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="autops-card stat-card stat-card--open">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="28"><Bell /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.open }}</div>
              <div class="stat-card__label">待处理</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="autops-card stat-card stat-card--progress">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="28"><Loading /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.inProgress }}</div>
              <div class="stat-card__label">处理中</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="autops-card stat-card stat-card--closed">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="28"><CircleCheckFilled /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.closed }}</div>
              <div class="stat-card__label">已关闭</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="autops-card stat-card stat-card--overdue">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="28"><WarningFilled /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.overdue }}</div>
              <div class="stat-card__label">SLA超时</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="autops-card stat-card stat-card--sla">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="28"><Timer /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ slaPercent }}%</div>
              <div class="stat-card__label">SLA达标率</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- ========== SLA Summary Bar ========== -->
    <div v-if="stats.total > 0" class="autops-card sla-bar-card mb-lg">
      <div class="autops-card-body">
        <div class="sla-bar">
          <span class="sla-bar__label">SLA 达标统计</span>
          <el-progress
            :percentage="slaPercent"
            :color="slaPercent >= 90 ? '#00b42a' : slaPercent >= 70 ? '#ff7d00' : '#f53f3f'"
            :stroke-width="18"
            :text-inside="true"
            style="flex: 1; margin: 0 16px"
          />
          <span class="sla-bar__detail">
            达标 <strong>{{ stats.withinSla }}</strong> / {{ stats.total }} 工单
          </span>
        </div>
      </div>
    </div>

    <!-- ========== Main Card ========== -->
    <div class="autops-card main-card">
      <div class="autops-card-header">
        <span class="autops-card-title">工单列表</span>
        <div class="card-header__actions">
          <el-button type="primary" :icon="Plus" @click="openCreateDialog">新建工单</el-button>
          <el-button :icon="Download" @click="exportTickets">导出</el-button>
          <el-button :icon="Refresh" circle size="small" @click="loadTickets" />
        </div>
      </div>
      <div class="autops-card-body">
        <!-- ========== Filters ========== -->
        <el-form :inline="true" class="autops-toolbar filter-form" @submit.prevent="handleSearch">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 140px">
            <el-option label="待处理" value="open" />
            <el-option label="处理中" value="in_progress" />
            <el-option label="待审批" value="pending_approval" />
            <el-option label="已解决" value="resolved" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="filters.priority" placeholder="全部优先级" clearable style="width: 130px">
            <el-option label="紧急" value="critical" />
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="filters.source" placeholder="全部来源" clearable style="width: 130px">
            <el-option label="手动创建" value="manual" />
            <el-option label="告警触发" value="alert" />
            <el-option label="自动化" value="automation" />
            <el-option label="策略触发" value="policy" />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人">
          <el-input
            v-model="filters.assignee"
            placeholder="搜索负责人"
            clearable
            :prefix-icon="Search"
            style="width: 150px"
          />
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="filters.dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DDTHH:mm:ssZ"
            style="width: 360px"
          />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索工单标题/描述"
            clearable
            :prefix-icon="Search"
            style="width: 180px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="RefreshLeft" @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- ========== Batch Operations Bar ========== -->
      <transition name="el-fade-in">
        <div v-if="selectedIds.length > 0" class="batch-bar">
          <span class="batch-bar__info">
            已选择 <strong>{{ selectedIds.length }}</strong> 条工单
          </span>
          <el-button type="primary" size="small" :icon="User" @click="batchAssign">
            批量指派
          </el-button>
          <el-button type="success" size="small" :icon="CircleCheck" @click="batchClose">
            批量关闭
          </el-button>
          <el-button size="small" @click="clearSelection">取消选择</el-button>
        </div>
      </transition>

      <!-- ========== Ticket Table ========== -->
      <el-table stripe
 ref="tableRef"
 :data="tickets"
 v-loading="loading"border
 row-key="id"
 @selection-change="handleSelectionChange"
 @row-click="handleRowClick"
 class="ticket-table"
 >
        <el-table-column type="selection" width="45" fixed="left" />
        <el-table-column prop="id" label="ID" width="90" show-overflow-tooltip>
          <template #default="{ row }">
            <el-button plain type="primary" size="small" @click.stop="viewDetail(row)">
              #{{ row.id?.slice(0, 8) || '-' }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="ticket-title" @click.stop="viewDetail(row)">{{ row.title || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="100" align="center">
          <template #default="{ row }">
            <el-tooltip :content="sourceTooltip(row.source)" placement="top">
              <el-icon :size="18">
                <component :is="sourceIcon(row.source)" />
              </el-icon>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="(priorityType(row.priority)) as TagType" size="small" effect="dark">
              {{ priorityLabel(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="(statusType(row.status)) as TagType" size="small">
              <el-icon v-if="row.status === 'overdue'" style="margin-right: 2px"><WarningFilled /></el-icon>
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="assigned_to" label="负责人" width="110" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ row.assigned_to || row.assigned_to_name || '未分配' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="SLA倒计时" width="130" align="center">
          <template #default="{ row }">
            <template v-if="row.sla_deadline && !['resolved', 'closed'].includes(row.status)">
              <el-tag
                v-if="isSlaOverdue(row.sla_deadline)"
                type="danger"
                effect="dark"
                size="small"
              >
                <el-icon><WarningFilled /></el-icon>
                超时
              </el-tag>
              <el-tag v-else type="warning" size="small">
                {{ slaCountdown(row.sla_deadline) }}
              </el-tag>
            </template>
            <span v-else style="color: #c9cdd4">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              type="primary" plain
              @click.stop="viewDetail(row)"
            >详情</el-button>
            <el-button
              type="warning" plain
              @click.stop="assignToMe(row)"
            >认领</el-button>
            <el-button
              type="success" plain
              @click.stop="closeTicket(row)"
            >关闭</el-button>
            <el-button
              type="danger" plain
              @click.stop="escalateTicket(row)"
            >升级</el-button>
          </template>
        </el-table-column>
      </el-table>

        <!-- ========== Pagination ========== -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            background
            @change="loadTickets"
          />
        </div>
      </div>
    </div>

    <!-- ========== Create Ticket Dialog ========== -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建工单"
      width="600px"
      destroy-on-close
      :close-on-click-modal="false"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="标题" prop="title">
          <el-input v-model="createForm.title" placeholder="请输入工单标题" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入工单描述"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="createForm.priority" style="width: 100%">
            <el-option label="紧急" value="critical" />
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="指派给">
          <el-select
            v-model="createForm.assigned_to"
            filterable
            remote
            reserve-keyword
            placeholder="搜索用户（可选）"
            :remote-method="searchUsers"
            :loading="usersLoading"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="user in userOptions"
              :key="user.id"
              :label="user.display_name || user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关联告警ID">
          <el-input v-model="createForm.related_alert_id" placeholder="关联告警ID（可选）" clearable />
        </el-form-item>
        <el-form-item label="关联资产ID">
          <el-input v-model="createForm.related_asset_id" placeholder="关联资产ID（可选）" clearable />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreate" :loading="createSubmitting">创建</el-button>
      </template>
    </el-dialog>

    <!-- ========== Batch Assign Dialog ========== -->
    <el-dialog
      v-model="batchAssignDialogVisible"
      title="批量指派"
      width="480px"
      destroy-on-close
    >
      <el-form label-width="80px">
        <el-form-item label="选中数量">
          <span>{{ selectedIds.length }} 条工单</span>
        </el-form-item>
        <el-form-item label="指派给">
          <el-select
            v-model="batchAssignee"
            filterable
            remote
            reserve-keyword
            placeholder="搜索用户"
            :remote-method="searchUsers"
            :loading="usersLoading"
            style="width: 100%"
          >
            <el-option
              v-for="user in userOptions"
              :key="user.id"
              :label="user.display_name || user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchAssignDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitBatchAssign" :loading="batchSubmitting" :disabled="!batchAssignee">
          确认指派
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  Search,
  Refresh,
  RefreshLeft,
  Plus,
  Download,
  CircleCheck,
  CircleCheckFilled,
  WarningFilled,
  Bell,
  Tickets,
  Timer,
  Loading,
  User,
  EditPen,
  Promotion,
  Notification,
  Monitor,
  SetUp,
  Operation,
} from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import {
  ticketStatusLabel, ticketStatusTag,
  priorityTag, priorityLabel as priorityLabelFn,
} from '@/shared/utils/labels'

const router = useRouter()

// ── State ──────────────────────────────────────────────────────────
const loading = ref(false)
const tickets = ref<any[]>([])
const selectedRows = ref<any[]>([])
const selectedIds = ref<string[]>([])
const tableRef = ref()

const stats = reactive({
  total: 0,
  open: 0,
  inProgress: 0,
  closed: 0,
  overdue: 0,
  withinSla: 0,
})

const filters = reactive({
  status: '',
  priority: '',
  source: '',
  assignee: '',
  dateRange: null as [string, string] | null,
  keyword: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

// ── Computed ────────────────────────────────────────────────────────
const slaPercent = computed(() => {
  if (stats.total === 0) return 100
  return Math.round((stats.withinSla / stats.total) * 100)
})

// ── Helpers ─────────────────────────────────────────────────────────
function formatTime(val: string | null | undefined): string {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds())
}

// 状态/优先级统一取自 shared/utils/labels.ts（单一事实源）
const priorityType = (p: string): TagType => priorityTag(p) as TagType
const priorityLabel = (p: string): string => priorityLabelFn(p)
const statusType = (s: string): TagType => ticketStatusTag(s) as TagType
const statusLabel = (s: string): string => ticketStatusLabel(s)

function sourceIcon(s: string) {
  const map: Record<string, string> = {
    manual: 'EditPen',
    alert: 'Bell',
    automation: 'SetUp',
    policy: 'Operation',
  }
  return map[s] || 'Notification'
}

function sourceTooltip(s: string): string {
  const map: Record<string, string> = {
    manual: '手动创建',
    alert: '告警触发',
    automation: '自动化',
    policy: '策略触发',
  }
  return map[s] || s || '未知'
}

function isSlaOverdue(deadline: string): boolean {
  return new Date(deadline).getTime() < Date.now()
}

function slaCountdown(deadline: string): string {
  const diff = new Date(deadline).getTime() - Date.now()
  if (diff <= 0) return '超时'
  const hours = Math.floor(diff / 3600000)
  const minutes = Math.floor((diff % 3600000) / 60000)
  if (hours >= 24) {
    const days = Math.floor(hours / 24)
    return days + '天' + hours % 24 + '时'
  }
  if (hours > 0) return hours + '时' + minutes + '分'
  return minutes + '分'
}

// ── Statistics ──────────────────────────────────────────────────────
async function loadStats() {
  try {
    const { data } = await api.get(R.TICKET_STATS)
    if (data.code === 0 && data.data) {
      const d = data.data
      stats.total = d.total ?? 0
      stats.open = d.open ?? 0
      stats.inProgress = d.in_progress ?? 0
      stats.closed = (d.closed ?? 0) + (d.resolved ?? 0)
    }
  } catch {
    // Fallback: get total from list
    try {
      const { data } = await api.get(R.TICKETS, { params: { page_size: 1 } })
      if (data.code === 0) stats.total = data.data?.total || 0
    } catch { /* ignore */ }
  }
}

async function loadFullStats() {
  try {
    // Try a dedicated stats endpoint first
    const { data } = await api.get(R.TICKET_STATS)
    if (data.code === 0 && data.data) {
      const s = data.data
      stats.total = s.total ?? 0
      stats.open = s.open_count ?? s.open ?? 0
      stats.inProgress = s.in_progress_count ?? s.in_progress ?? 0
      stats.closed = s.closed_count ?? s.closed ?? 0
      stats.overdue = s.overdue_count ?? s.overdue ?? 0
      stats.withinSla = s.within_sla ?? s.withinSla ?? stats.total
    }
  } catch {
    // Fallback: derive stats from individual count queries
    try {
      const [openRes, progressRes, closedRes, overdueRes] = await Promise.allSettled([
        api.get(R.TICKETS, { params: { status: 'open', page: 1, page_size: 1 } }),
        api.get(R.TICKETS, { params: { status: 'in_progress', page: 1, page_size: 1 } }),
        api.get(R.TICKETS, { params: { status: 'closed', page: 1, page_size: 1 } }),
        api.get(R.TICKETS, { params: { sla_overdue: true, page: 1, page_size: 1 } }),
      ])
      const extract = (r: PromiseSettledResult<any>) =>
        r.status === 'fulfilled' && r.value.data?.code === 0 ? r.value.data.data?.total || 0 : 0

      stats.open = extract(openRes)
      stats.inProgress = extract(progressRes)
      stats.closed = extract(closedRes)
      stats.overdue = extract(overdueRes)
      stats.total = stats.open + stats.inProgress + stats.closed
      stats.withinSla = Math.max(0, stats.total - stats.overdue)
    } catch {
      // silently ignore
    }
  }
}

// ── Ticket List ─────────────────────────────────────────────────────
async function loadTickets() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.status) params.status = filters.status
    if (filters.priority) params.priority = filters.priority
    if (filters.source) params.source = filters.source
    if (filters.assignee) params.assignee = filters.assignee
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_time = filters.dateRange[0]
      params.end_time = filters.dateRange[1]
    }
    const { data } = await api.get(R.TICKETS, { params })
    if (data.code === 0) {
      tickets.value = data.data.items || data.data.list || []
      pagination.total = data.data.total || 0
    }
  } catch {
    ElMessage.error('加载工单列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  loadTickets()
}

function resetFilters() {
  filters.status = ''
  filters.priority = ''
  filters.source = ''
  filters.assignee = ''
  filters.dateRange = null
  filters.keyword = ''
  pagination.page = 1
  loadTickets()
}

// ── Selection ───────────────────────────────────────────────────────
function handleSelectionChange(rows: any[]) {
  selectedRows.value = rows
  selectedIds.value = rows.map((r) => r.id)
}

function clearSelection() {
  tableRef.value?.clearSelection()
}

// ── Navigation ──────────────────────────────────────────────────────
function handleRowClick(row: any) {
  viewDetail(row)
}

function viewDetail(row: any) {
  router.push({ name: 'ticket-detail', params: { id: row.id } })
}

// ── Create Ticket ───────────────────────────────────────────────────
const createDialogVisible = ref(false)
const createSubmitting = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive({
  title: '',
  description: '',
  priority: 'medium',
  assigned_to: '',
  related_alert_id: '',
  related_asset_id: '',
})

const createRules: FormRules = {
  title: [{ required: true, message: '请输入工单标题', trigger: 'blur' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }],
}

function openCreateDialog() {
  createForm.title = ''
  createForm.description = ''
  createForm.priority = 'medium'
  createForm.assigned_to = ''
  createForm.related_alert_id = ''
  createForm.related_asset_id = ''
  createDialogVisible.value = true
}

async function submitCreate() {
  if (!createFormRef.value) return
  await createFormRef.value.validate(async (valid) => {
    if (!valid) return
    createSubmitting.value = true
    try {
      const payload: Record<string, any> = {
        title: createForm.title,
        description: createForm.description,
        priority: createForm.priority,
      }
      if (createForm.assigned_to) payload.assigned_to = createForm.assigned_to
      if (createForm.related_alert_id) payload.alert_ids = JSON.stringify([createForm.related_alert_id])
      if (createForm.related_asset_id) payload.asset_id = createForm.related_asset_id

      const { data } = await api.post(R.TICKETS, payload)
      if (data.code === 0) {
        ElMessage.success('工单创建成功')
        createDialogVisible.value = false
        loadTickets()
        loadFullStats()
      } else {
        ElMessage.error(data.message || '创建失败')
      }
    } catch (err: any) {
      ElMessage.error(err.message || '创建工单失败')
    } finally {
      createSubmitting.value = false
    }
  })
}

// ── User Search ─────────────────────────────────────────────────────
const userOptions = ref<any[]>([])
const usersLoading = ref(false)

async function searchUsers(query: string) {
  usersLoading.value = true
  try {
    const params: Record<string, string> = {}
    if (query) params.keyword = query
    const { data } = await api.get(R.GOVERNANCE.USERS, { params })
    if (data.code === 0) {
      const list = Array.isArray(data.data) ? data.data : data.data?.items || []
      userOptions.value = list
    }
  } catch {
    userOptions.value = []
  } finally {
    usersLoading.value = false
  }
}

// ── Quick Actions ───────────────────────────────────────────────────
async function assignToMe(row: any) {
  try {
    await ElMessageBox.confirm('确认将此工单指派给自己？', '认领工单', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'info',
    })
    const { data } = await api.patch(R.TICKET_DETAIL(row.id), {
      assigned_to: 'me',
      status: 'in_progress',
    })
    if (data.code === 0) {
      ElMessage.success('已认领工单')
      loadTickets()
      loadFullStats()
    }
  } catch {
    // cancelled or error
  }
}

async function closeTicket(row: any) {
  try {
    const { value: reason } = await ElMessageBox.prompt(
      '请输入关闭原因（可选）',
      '关闭工单',
      {
        confirmButtonText: '关闭',
        cancelButtonText: '取消',
        inputPlaceholder: '关闭原因',
        inputValidator: (val: string) => true,
      },
    )
    const { data } = await api.patch(R.TICKET_DETAIL(row.id), {
      status: 'closed',
      resolution: reason || '',
    })
    if (data.code === 0) {
      ElMessage.success('工单已关闭')
      loadTickets()
      loadFullStats()
    }
  } catch {
    // cancelled
  }
}

async function escalateTicket(row: any) {
  try {
    const { value: reason } = await ElMessageBox.prompt(
      '请输入升级原因',
      '升级工单',
      {
        confirmButtonText: '升级',
        cancelButtonText: '取消',
        inputPlaceholder: '升级原因',
        inputValidator: (val: string) => (val.trim() ? true : '请输入升级原因'),
      },
    )
    // Escalate by increasing priority
    const priorityOrder = ['low', 'medium', 'high', 'critical']
    const currentIdx = priorityOrder.indexOf(row.priority)
    const newPriority = priorityOrder[Math.min(currentIdx + 1, priorityOrder.length - 1)]

    const { data } = await api.patch(R.TICKET_DETAIL(row.id), {
      priority: newPriority,
      escalation_reason: reason,
    })
    if (data.code === 0) {
      ElMessage.success('工单已升级')
      loadTickets()
      loadFullStats()
    }
  } catch {
    // cancelled
  }
}

// ── Batch Operations ────────────────────────────────────────────────
const batchAssignDialogVisible = ref(false)
const batchAssignee = ref('')
const batchSubmitting = ref(false)

function batchAssign() {
  batchAssignee.value = ''
  batchAssignDialogVisible.value = true
  searchUsers('')
}

async function submitBatchAssign() {
  if (!batchAssignee.value || !selectedIds.value.length) return
  batchSubmitting.value = true
  try {
    const promises = selectedIds.value.map((id) =>
      api.patch(R.TICKET_DETAIL(id), { assigned_to: batchAssignee.value }),
    )
    const results = await Promise.allSettled(promises)
    const failed = results.filter((r) => r.status === 'rejected').length
    if (failed === 0) {
      ElMessage.success(selectedIds.value.length + ' 条工单已全部指派')
    } else {
      ElMessage.warning(selectedIds.value.length - failed + ' 条成功，' + failed + ' 条失败')
    }
    clearSelection()
    batchAssignDialogVisible.value = false
    loadTickets()
    loadFullStats()
  } catch {
    ElMessage.error('批量指派失败')
  } finally {
    batchSubmitting.value = false
  }
}

async function batchClose() {
  const ids = selectedIds.value
  if (!ids.length) return
  try {
    await ElMessageBox.confirm('确认批量关闭 ' + ids.length + ' 条工单？', '批量关闭', {
      confirmButtonText: '关闭',
      cancelButtonText: '取消',
      type: 'warning',
    })
    const promises = ids.map((id) =>
      api.patch(R.TICKET_DETAIL(id), { status: 'closed' }),
    )
    const results = await Promise.allSettled(promises)
    const failed = results.filter((r) => r.status === 'rejected').length
    if (failed === 0) {
      ElMessage.success(ids.length + ' 条工单已全部关闭')
    } else {
      ElMessage.warning(ids.length - failed + ' 条成功，' + failed + ' 条失败')
    }
    clearSelection()
    loadTickets()
    loadFullStats()
  } catch {
    // cancelled
  }
}

// ── Export ───────────────────────────────────────────────────────────
async function exportTickets() {
  try {
    const params: Record<string, any> = {
      page: 1,
      page_size: 100,
      export: true,
    }
    if (filters.status) params.status = filters.status
    if (filters.priority) params.priority = filters.priority
    if (filters.source) params.source = filters.source
    if (filters.keyword) params.keyword = filters.keyword

    const { data } = await api.get(R.TICKETS, {
      params,
      responseType: 'blob',
    })

    // If the response is actually JSON (not a blob export), fall back to CSV generation
    if (data instanceof Blob && data.type?.includes('json')) {
      // Backend doesn't support export param, generate CSV client-side
      generateCsv()
      return
    }

    if (data instanceof Blob) {
      const url = URL.createObjectURL(data)
      const link = document.createElement('a')
      link.href = url
      link.download = 'tickets_' + new Date().toISOString().slice(0, 10) + '.csv'
      link.click()
      URL.revokeObjectURL(url)
      ElMessage.success('导出成功')
      return
    }

    // Fallback: client-side CSV
    generateCsv()
  } catch {
    // Fallback to client-side CSV generation
    generateCsv()
  }
}

function generateCsv() {
  if (!tickets.value.length) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  const headers = ['ID', '标题', '来源', '优先级', '状态', '负责人', 'SLA截止', '创建时间']
  const rows = tickets.value.map((t) => [
    t.id || '',
    '"' + (t.title || '').replace(/"/g, '""') + '"',
    t.source || '',
    t.priority || '',
    t.status || '',
    t.assigned_to || t.assigned_to_name || '',
    t.sla_deadline ? formatTime(t.sla_deadline) : 'primary',
    formatTime(t.created_at),
  ])
  const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'tickets_' + new Date().toISOString().slice(0, 10) + '.csv'
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// ── Lifecycle ───────────────────────────────────────────────────────
let statsTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  loadFullStats()
  loadTickets()
  // Auto-refresh stats every 30s
  statsTimer = setInterval(loadFullStats, 30_000)
})

onBeforeUnmount(() => {
  if (statsTimer) {
    clearInterval(statsTimer)
    statsTimer = null
  }
})
</script>

<style scoped>
.ticket-list-page {
  padding: var(--autops-space-xl);
}

/* ── Statistics Cards ── */
.stats-row {
  margin-bottom: var(--autops-space-lg);
}
.stat-card__body {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-card__icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-card__info {
  flex: 1;
  min-width: 0;
}

.stat-card__value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-card__label {
  font-size: var(--autops-font-12);
  color: var(--autops-info);
  margin-top: 2px;
}

.autops-metric-card--total .stat-card__icon {
  background: rgba(144, 147, 153, 0.12);
  color: var(--autops-info);
}
.autops-metric-card--total .stat-card__value {
  color: var(--autops-text-2);
}

.autops-metric-card--open .stat-card__icon {
  background: rgba(230, 162, 60, 0.12);
  color: var(--autops-warning);
}
.autops-metric-card--open .stat-card__value {
  color: var(--autops-warning);
}

.autops-metric-card--progress .stat-card__icon {
  background: rgba(64, 158, 255, 0.12);
  color: var(--autops-primary);
}
.autops-metric-card--progress .stat-card__value {
  color: var(--autops-primary);
}

.autops-metric-card--closed .stat-card__icon {
  background: rgba(103, 194, 58, 0.12);
  color: var(--autops-success);
}
.autops-metric-card--closed .stat-card__value {
  color: var(--autops-success);
}

.autops-metric-card--overdue .stat-card__icon {
  background: rgba(245, 108, 108, 0.12);
  color: var(--autops-danger);
}
.autops-metric-card--overdue .stat-card__value {
  color: var(--autops-danger);
}

.autops-metric-card--sla .stat-card__icon {
  background: rgba(103, 194, 58, 0.12);
  color: var(--autops-success);
}
.autops-metric-card--sla .stat-card__value {
  color: var(--autops-success);
}

/* ── SLA Summary Bar ── */
.sla-bar-card {
  margin-bottom: var(--autops-space-lg);
  border-radius: var(--autops-radius-md);
}

.sla-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sla-bar__label {
  font-size: var(--autops-font-14);
  font-weight: 500;
  color: var(--autops-text-2);
  white-space: nowrap;
}

.sla-bar__detail {
  font-size: var(--autops-font-13);
  color: var(--autops-info);
  white-space: nowrap;
}

/* ── Main Card ── */
.main-card {
  border-radius: var(--autops-radius-md);
}
/* ── Filter Form ── */
.filter-form {
  margin-bottom: var(--autops-space-lg);
  padding-bottom: 16px;
  border-bottom: 1px solid var(--autops-bg-4);
}

.filter-form :deep(.el-form-item) {
  margin-bottom: var(--autops-space-md);
}

/* ── Batch Operations Bar ── */
.batch-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  margin-bottom: var(--autops-space-md);
  background: var(--autops-primary-light-5);
  border: 1px solid var(--autops-primary-light-5);
  border-radius: 6px;
}

.batch-bar__info {
  margin-right: auto;
  font-size: var(--autops-font-14);
  color: var(--autops-text-2);
}

/* ── Table ── */
.ticket-table {
  width: 100%;
}

.ticket-table :deep(.el-table__fixed-right) {
  right: 0 !important;
}

.ticket-title {
  cursor: pointer;
  color: var(--autops-primary);
}

.ticket-title:hover {
  text-decoration: underline;
}

/* ── Pagination ── */
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--autops-space-lg);
}

/* ── Responsive ── */
@media (max-width: 1200px) {
  .filter-form :deep(.el-form-item__content) {
    max-width: 160px;
  }
  .filter-form :deep(.el-date-editor) {
    width: 280px !important;
  }
}
</style>
