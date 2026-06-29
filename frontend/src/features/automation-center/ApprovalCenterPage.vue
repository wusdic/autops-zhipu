<template>
  <div class="autops-page-container">
    <PageHeader title="审批中心" desc="审批自动化执行请求，管控操作风险" />

    <!-- Status Tabs -->
    <el-card shadow="never" class="tabs-card">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane name="pending">
          <template #label>
            <span>待审批 <el-badge v-if="pendingCount > 0" :value="pendingCount" class="tab-badge" /></span>
          </template>
        </el-tab-pane>
        <el-tab-pane label="已批准" name="approved" />
        <el-tab-pane label="已拒绝" name="rejected" />
      </el-tabs>

      <!-- Filter Row -->
      <el-row :gutter="16" align="middle" class="mb-lg">
        <el-col :span="6">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索请求名称、请求人..."
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
          <el-select v-model="filterRisk" placeholder="风险等级" clearable @change="handleSearch">
            <el-option label="高风险" value="high" />
            <el-option label="中风险" value="medium" />
            <el-option label="低风险" value="low" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterType" placeholder="请求类型" clearable @change="handleSearch">
            <el-option label="脚本执行" value="script" />
            <el-option label="Playbook 执行" value="playbook" />
            <el-option label="配置变更" value="config" />
            <el-option label="巡检任务" value="inspection" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-col>
      </el-row>

      <!-- Data Table -->
      <el-table stripe
 :data="approvals"
v-loading="loading"
 empty-text="暂无审批记录"
 @sort-change="handleSortChange"
 >
        <el-table-column prop="name" label="请求名称" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="request-name" @click="viewDetail(row)">{{ row.name || row.title || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ typeLabel(row.type || row.execution_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险等级" width="100" align="center">
          <template #default="{ row }">
            <StatusBadge :status="row.risk_level" />
          </template>
        </el-table-column>
        <el-table-column prop="requester" label="请求人" width="110">
          <template #default="{ row }">
            {{ row.requester || row.applicant || row.created_by || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="原因" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="text-tertiary">{{ row.reason || row.description || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="请求时间" width="170" sortable="custom">
          <template #default="{ row }">
            <span class="text-tertiary">{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <StatusBadge :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button plain type="success" size="small" @click="openActionDialog(row, 'approve')">
                批准
              </el-button>
              <el-button plain type="danger" size="small" @click="openActionDialog(row, 'reject')">
                拒绝
              </el-button>
            </template>
            <template v-else>
              <el-button plain type="primary" size="small" @click="viewDetail(row)">查看</el-button>
            </template>
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
          @size-change="fetchApprovals"
          @current-change="fetchApprovals"
        />
      </div>
    </el-card>

    <!-- Approve / Reject Dialog -->
    <el-dialog
      v-model="actionDialogVisible"
      :title="actionType === 'approve' ? '批准请求' : '拒绝请求'"
      width="600px"
      :close-on-click-modal="false"
      @closed="resetActionForm"
    >
      <div class="action-dialog-content">
        <el-descriptions :column="1" border size="small" class="mb-lg">
          <el-descriptions-item label="请求名称">{{ currentAction?.name || currentAction?.title || '-' }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ typeLabel(currentAction?.type || currentAction?.execution_type) }}</el-descriptions-item>
          <el-descriptions-item label="风险等级">
            <StatusBadge :status="currentAction?.risk_level ?? ''" />
          </el-descriptions-item>
          <el-descriptions-item label="请求人">{{ currentAction?.requester || currentAction?.applicant || '-' }}</el-descriptions-item>
        </el-descriptions>

        <el-form label-position="top">
          <el-form-item :label="actionType === 'approve' ? '批准备注（可选）' : '拒绝原因'">
            <el-input
              v-model="actionComment"
              type="textarea"
              :rows="4"
              :placeholder="actionType === 'approve' ? '请输入批准备注...' : '请输入拒绝原因...'"
              maxlength="256"
              show-word-limit
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="actionDialogVisible = false">取消</el-button>
        <el-button
          :type="actionType === 'approve' ? 'success' : 'danger'"
          :loading="actionSubmitting"
          @click="submitAction"
        >
          {{ actionType === 'approve' ? '确认批准' : '确认拒绝' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Detail Drawer -->
    <el-drawer v-model="drawerVisible" title="审批详情" size="520px">
      <template v-if="currentDetail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="请求名称">{{ currentDetail.name || currentDetail.title || '-' }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ typeLabel(currentDetail.type || currentDetail.execution_type) }}</el-descriptions-item>
          <el-descriptions-item label="风险等级">
            <StatusBadge :status="currentDetail.risk_level" />
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusBadge :status="currentDetail.status" />
          </el-descriptions-item>
          <el-descriptions-item label="请求人">{{ currentDetail.requester || currentDetail.applicant || '-' }}</el-descriptions-item>
          <el-descriptions-item label="请求时间">{{ formatTime(currentDetail.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="原因/说明">{{ currentDetail.reason || currentDetail.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="审批人" v-if="currentDetail.reviewer">{{ currentDetail.reviewer }}</el-descriptions-item>
          <el-descriptions-item label="审批时间" v-if="currentDetail.reviewed_at">{{ formatTime(currentDetail.reviewed_at) }}</el-descriptions-item>
          <el-descriptions-item label="审批备注" v-if="currentDetail.comment">{{ currentDetail.comment }}</el-descriptions-item>
        </el-descriptions>

        <!-- Execution Targets -->
        <div v-if="currentDetail.targets && currentDetail.targets.length" class="mt-lg">
          <div class="section-title">执行目标</div>
          <el-table stripe  :data="currentDetail.targets" size="small" border>
            <el-table-column prop="name" label="名称" min-width="120" />
            <el-table-column prop="type" label="类型" width="100" />
            <el-table-column prop="action" label="操作" width="180" />
          </el-table>
        </div>

        <!-- Quick Actions for Pending -->
        <div v-if="currentDetail.status === 'pending'" class="mt-lg" style="display: flex; gap: 12px;">
          <el-button type="success" @click="openActionDialog(currentDetail, 'approve'); drawerVisible = false">
            批准
          </el-button>
          <el-button type="danger" @click="openActionDialog(currentDetail, 'reject'); drawerVisible = false">
            拒绝
          </el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import { automationService } from '@/shared/api'
import { riskLabel as riskLabelFn, approvalStatusTag, approvalStatusLabel } from '@/shared/utils/labels'

// ---------- Types ----------
interface Approval {
  id: string
  name?: string
  title?: string
  type?: string
  execution_type?: string
  risk_level: 'high' | 'medium' | 'low'
  status: 'pending' | 'approved' | 'rejected'
  requester?: string
  applicant?: string
  created_by?: string
  reason?: string
  description?: string
  created_at: string
  reviewed_at?: string
  reviewer?: string
  comment?: string
  targets?: Array<{ name: string; type: string; action: string }>
}

// ---------- State ----------
const loading = ref(false)
const actionSubmitting = ref(false)
const approvals = ref<Approval[]>([])
const activeTab = ref('all')

const drawerVisible = ref(false)
const currentDetail = ref<Approval | null>(null)

const actionDialogVisible = ref(false)
const actionType = ref<'approve' | 'reject'>('approve')
const currentAction = ref<Approval | null>(null)
const actionComment = ref('')

const searchKeyword = ref('')
const filterRisk = ref('')
const filterType = ref('')
const sortField = ref('')
const sortOrder = ref('')

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

// ---------- Computed ----------
const pendingCount = computed(() => approvals.value.filter(a => a.status === 'pending').length)

// ---------- Label Helpers ----------
function typeLabel(type?: string) {
  const map: Record<string, string> = {
    script: '脚本执行',
    playbook: 'Playbook 执行',
    config: '配置变更',
    inspection: '巡检任务',
  }
  return map[type || ''] || type || '-'
}

function riskTagType(level: string): TagType {
  const map: Record<string, string> = { high: 'danger', medium: 'warning', low: 'success' }
  return (map[level || ''] || 'info') as TagType
}

const riskLabel = (level?: string): string => riskLabelFn(level || '')
const statusTagType = (status?: string): TagType => approvalStatusTag(status || '') as TagType
const statusLabel = (status?: string): string => approvalStatusLabel(status || '')

function formatTime(val?: string) {
  if (!val) return '-'
  return val.replace('T', ' ').substring(0, 19)
}

// ---------- Data Fetching ----------
async function fetchApprovals() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.page_size,
    }
    if (activeTab.value !== 'all') params.status = activeTab.value
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (filterRisk.value) params.risk_level = filterRisk.value
    if (filterType.value) params.type = filterType.value
    if (sortField.value) {
      params.sort_by = sortField.value
      params.sort_order = sortOrder.value
    }

    const res = await automationService.listApprovals(params)
    const data = res.data?.data ?? res.data
    if (Array.isArray(data?.items)) {
      approvals.value = data.items
      pagination.total = data.total ?? data.items.length
    } else if (Array.isArray(data)) {
      approvals.value = data
      pagination.total = data.length
    }
  } catch (e: any) {
    ElMessage.error(e.message || '获取审批列表失败')
  } finally {
    loading.value = false
  }
}

// ---------- Search & Filter ----------
function handleTabChange() {
  pagination.page = 1
  fetchApprovals()
}

function handleSearch() {
  pagination.page = 1
  fetchApprovals()
}

function resetFilters() {
  searchKeyword.value = ''
  filterRisk.value = ''
  filterType.value = ''
  sortField.value = ''
  sortOrder.value = ''
  handleSearch()
}

function handleSortChange({ prop, order }: any) {
  sortField.value = prop || ''
  sortOrder.value = order === 'ascending' ? 'asc' : order === 'descending' ? 'desc' : 'primary'
  fetchApprovals()
}

// ---------- Detail ----------
function viewDetail(row: any) {
  currentDetail.value = row
  drawerVisible.value = true
}

// ---------- Approve / Reject ----------
function openActionDialog(row: any, type: 'approve' | 'reject') {
  currentAction.value = row
  actionType.value = type
  actionComment.value = ''
  actionDialogVisible.value = true
}

function resetActionForm() {
  actionComment.value = ''
  currentAction.value = null
}

async function submitAction() {
  if (!currentAction.value) return

  if (actionType.value === 'reject' && !actionComment.value.trim()) {
    ElMessage.warning('请填写拒绝原因')
    return
  }

  actionSubmitting.value = true
  try {
    if (actionType.value === 'approve') {
      await automationService.approve(currentAction.value.id, {
        approved: true,
        comment: actionComment.value,
      })
      ElMessage.success('已批准')
    } else {
      await automationService.reject(currentAction.value.id, {
        comment: actionComment.value,
      })
      ElMessage.success('已拒绝')
    }
    actionDialogVisible.value = false
    fetchApprovals()
  } catch (e: any) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    actionSubmitting.value = false
  }
}

// ---------- Init ----------
onMounted(() => {
  fetchApprovals()
})
</script>

<style scoped>


.tabs-card :deep(.el-card__body) {
  padding: var(--autops-space-lg) 20px;
}

.request-name {
  color: var(--autops-primary);
  cursor: pointer;
  font-weight: 500;
}

.request-name:hover {
  text-decoration: underline;
}

.text-tertiary {
  color: var(--autops-info);
  font-size: var(--autops-font-13);
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: var(--autops-space-lg) 0 0;
}

.tab-badge {
  margin-left: 4px;
}

.tab-badge :deep(.el-badge__content) {
  top: -2px;
}

.action-dialog-content {
  padding: 0 4px;
}

.section-title {
  font-size: var(--autops-font-14);
  font-weight: 600;
  color: var(--autops-text-1);
  margin-bottom: var(--autops-space-md);
}
</style>
