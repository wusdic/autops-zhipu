<template>
  <div class="autops-page-container">
    <!-- Page Header -->
    <PageHeader title="Dry-run 详情" back desc="模拟自动化策略执行，预览执行计划与影响分析" />

    <!-- Alert -->
    <el-alert
      type="info"
      title="Dry-run 模式：仅预演执行计划，不实际修改系统"
      show-icon
      :closable="false"
      class="mb-lg"
    />

    <!-- Two-column layout: List + Detail -->
    <el-row :gutter="16">
      <!-- Left: Dry-run List -->
      <el-col :span="showDetail ? 10 : 24">
        <el-card shadow="never" class="table-card">
          <template #header>
            <div class="autops-card-header">
              <span class="card-title">预演记录</span>
            </div>
          </template>

          <!-- Filter -->
          <el-row :gutter="12" class="mb-lg">
            <el-col :span="8">
              <el-input
                v-model="searchKeyword"
                placeholder="搜索名称..."
                clearable
                size="small"
                @keyup.enter="handleSearch"
                @clear="handleSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-col>
            <el-col :span="5">
              <el-select v-model="filterStatus" placeholder="状态" clearable size="small" @change="handleSearch">
                <el-option label="运行中" value="running" />
                <el-option label="成功" value="success" />
                <el-option label="失败" value="failed" />
                <el-option label="已取消" value="cancelled" />
              </el-select>
            </el-col>
            <el-col :span="4">
              <el-button size="small" type="primary" @click="handleSearch">查询</el-button>
              <el-button size="small" @click="resetFilters">重置</el-button>
            </el-col>
          </el-row>

          <!-- Table -->
          <el-table stripe
 :data="dryRuns"
v-loading="loading"
 empty-text="暂无预演记录"
 highlight-current-row
 @current-change="handleRowSelect"
 size="small"
 >
            <el-table-column prop="name" label="名称" min-width="150" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="dryrun-name" @click="loadDetail(row)">{{ row.name || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="policy_name" label="关联策略" width="130" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="text-tertiary">{{ row.policy_name || row.policy_id || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90" align="center">
              <template #default="{ row }">
                <StatusBadge :status="row.status" />
              </template>
            </el-table-column>
            <el-table-column prop="triggered_at" label="触发时间" width="160">
              <template #default="{ row }">
                <span class="text-tertiary">{{ formatTime(row.triggered_at || row.created_at) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right" align="center">
              <template #default="{ row }">
                <el-button plain type="primary" size="small" @click="loadDetail(row)">查看</el-button>
                <el-button plain type="danger" size="small" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- Pagination -->
          <div class="pagination-wrap">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.page_size"
              :total="pagination.total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              background
              small
              @size-change="fetchDryRuns"
              @current-change="fetchDryRuns"
            />
          </div>
        </el-card>
      </el-col>

      <!-- Right: Detail View -->
      <el-col :span="14" v-if="showDetail">
        <el-card shadow="never" class="detail-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">预演详情</span>
              <el-button plain type="primary" size="small" @click="showDetail = false; detail = null">
                <el-icon><Close /></el-icon> 关闭
              </el-button>
            </div>
          </template>

          <div v-loading="detailLoading">
            <template v-if="detail">
              <!-- Basic Info -->
              <el-descriptions :column="2" border size="small" class="mb-lg">
                <el-descriptions-item label="名称">{{ detail.name || '-' }}</el-descriptions-item>
                <el-descriptions-item label="关联策略">{{ detail.policy_name || detail.policy_id || '-' }}</el-descriptions-item>
                <el-descriptions-item label="状态">
                  <StatusBadge :status="detail.status" />
                </el-descriptions-item>
                <el-descriptions-item label="触发时间">{{ formatTime(detail.triggered_at || detail.created_at) }}</el-descriptions-item>
                <el-descriptions-item label="完成时间" v-if="detail.completed_at">
                  {{ formatTime(detail.completed_at) }}
                </el-descriptions-item>
                <el-descriptions-item label="耗时" v-if="detail.duration">
                  {{ detail.duration }}s
                </el-descriptions-item>
              </el-descriptions>

              <!-- Step-by-step Execution Plan -->
              <div class="section-title">执行计划模拟</div>
              <div v-if="detail.steps && detail.steps.length" class="steps-container">
                <div
                  v-for="(step, index) in detail.steps"
                  :key="index"
                  class="step-item"
                  :class="{ 'step-success': step.status === 'success', 'step-failed': step.status === 'failed', 'step-running': step.status === 'running', 'step-pending': step.status === 'pending' }"
                >
                  <div class="step-header">
                    <div class="step-index">{{ index + 1 }}</div>
                    <div class="step-info">
                      <div class="step-name">{{ step.name || '步骤 ' + index + 1 }}</div>
                      <div class="step-desc">{{ step.description || '-' }}</div>
                    </div>
                    <el-tag
                      :type="(dryRunStatusTag(step.status)) as TagType"
                      size="small"
                      effect="light"
                      class="ml-auto"
                    >
                      {{ dryRunStatusLabel(step.status) }}
                    </el-tag>
                  </div>
                  <div v-if="step.action" class="step-detail">
                    <div class="step-detail-row">
                      <span class="step-label">动作:</span>
                      <span>{{ step.action }}</span>
                    </div>
                    <div v-if="step.target" class="step-detail-row">
                      <span class="step-label">目标:</span>
                      <span>{{ step.target }}</span>
                    </div>
                    <div v-if="step.result" class="step-detail-row">
                      <span class="step-label">模拟结果:</span>
                      <el-tag size="small" type="info">{{ step.result }}</el-tag>
                    </div>
                    <div v-if="step.message" class="step-detail-row">
                      <span class="step-label">消息:</span>
                      <span class="text-tertiary">{{ step.message }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <el-empty v-else description="暂无执行步骤数据" :image-size="60" />

              <!-- Impact Analysis -->
              <div class="section-title mt-lg">影响分析</div>
              <el-descriptions v-if="detail.impact" :column="1" border size="small">
                <el-descriptions-item label="目标资源">
                  {{ detail.impact.target || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="影响范围">
                  <el-tag size="small" type="warning">{{ detail.impact.scope || '-' }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="风险等级">
                  <StatusBadge :status="detail.impact.risk_level ?? ''" />
                </el-descriptions-item>
                <el-descriptions-item label="预计变更">
                  {{ detail.impact.changes || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="影响资产数" v-if="detail.impact.affected_count">
                  {{ detail.impact.affected_count }}
                </el-descriptions-item>
              </el-descriptions>
              <el-empty v-else description="暂无影响分析数据" :image-size="60" />

              <!-- Error Info -->
              <div v-if="detail.error" class="mt-lg">
                <div class="section-title text-danger">错误信息</div>
                <el-alert type="error" :title="detail.error" show-icon :closable="false" />
              </div>
            </template>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import type { TagType } from '@/shared/types'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Search, Close } from '@element-plus/icons-vue'
import { automationService } from '@/shared/api'
import PageHeader from '@/shared/components/PageHeader.vue'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import { riskLabel as riskLabelFn } from '@/shared/utils/labels'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()

// ---------- Types ----------
interface DryRunStep {
  name?: string
  description?: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped'
  action?: string
  target?: string
  result?: string
  message?: string
}

interface DryRunImpact {
  target?: string
  scope?: string
  risk_level?: 'high' | 'medium' | 'low'
  changes?: string
  affected_count?: number
}

interface DryRun {
  id: string
  name: string
  policy_id?: string
  policy_name?: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled'
  triggered_at?: string
  created_at?: string
  completed_at?: string
  duration?: number
  steps?: DryRunStep[]
  impact?: DryRunImpact
  error?: string
}

// ---------- State ----------
const loading = ref(false)
const detailLoading = ref(false)
const dryRuns = ref<DryRun[]>([])
const detail = ref<DryRun | null>(null)
const showDetail = ref(false)

const searchKeyword = ref('')
const filterStatus = ref('')

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

// ---------- Helpers ----------
function dryRunStatusTag(status?: string): TagType {
  const map: Record<string, TagType> = {
    pending: 'info',
    running: 'primary',
    success: 'success',
    failed: 'danger',
    cancelled: 'info',
    skipped: 'warning',
  }
  return map[status || ''] ?? 'info'
}

function dryRunStatusLabel(status?: string) {
  const map: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    success: '成功',
    failed: '失败',
    cancelled: '已取消',
    skipped: '已跳过',
  }
  return map[status || ''] || '未知'
}

function riskTagType(level: string): TagType {
  const map: Record<string, string> = { high: 'danger', medium: 'warning', low: 'success' }
  return (map[level || ''] || 'info') as TagType
}

const riskLabel = (level?: string): string => riskLabelFn(level || '')

function formatTime(val?: string) {
  if (!val) return '-'
  return val.replace('T', ' ').substring(0, 19)
}

// ---------- Data Fetching ----------
async function fetchDryRuns() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.page_size,
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (filterStatus.value) params.status = filterStatus.value

    // Use direct API call since automationService doesn't have listDryRuns
    const res = await client.get(API.AUTOMATION.DRY_RUN, { params })
    const data = res.data?.data ?? res.data
    if (Array.isArray(data?.items)) {
      dryRuns.value = data.items
      pagination.total = data.total ?? data.items.length
    } else if (Array.isArray(data)) {
      dryRuns.value = data
      pagination.total = data.length
    }
  } catch (e: any) {
    ElMessage.error(e.message || '获取预演列表失败')
  } finally {
    loading.value = false
  }
}

// ---------- Search & Filter ----------
function handleSearch() {
  pagination.page = 1
  fetchDryRuns()
}

function resetFilters() {
  searchKeyword.value = ''
  filterStatus.value = ''
  handleSearch()
}

// ---------- Detail ----------
function handleRowSelect(row: DryRun | null) {
  if (row) loadDetail(row)
}

async function loadDetail(row: any) {
  detailLoading.value = true
  showDetail.value = true
  try {
    const res = await automationService.getDryRunDetail(row.id)
    const data = res.data?.data ?? res.data
    detail.value = data && typeof data === 'object' ? data : row
  } catch (e: any) {
    // Fallback: use row data if API fails
    detail.value = row
    ElMessage.warning(e.message || '获取详情失败，显示本地数据')
  } finally {
    detailLoading.value = false
  }
}

// ---------- Actions ----------
async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(
      '确认删除预演记录「' + row.name + '」？此操作不可撤销。',
      '删除确认',
      { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' }
    )
    await client.delete(API.AUTOMATION.DRY_RUN_DETAIL(row.id))
    ElMessage.success('删除成功')
    if (detail.value?.id === row.id) {
      detail.value = null
      showDetail.value = false
    }
    fetchDryRuns()
  } catch (e: any) {
    if (e !== 'cancel' && e?.action !== 'cancel' && e?.message !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

// ---------- Init ----------
onMounted(() => {
  fetchDryRuns()
})
</script>

<style scoped>






.table-card :deep(.el-card__body) {
  padding: var(--autops-space-lg);
}

.detail-card :deep(.el-card__body) {
  padding: var(--autops-space-lg);
}

.dryrun-name {
  color: var(--autops-primary);
  cursor: pointer;
  font-weight: 500;
}

.dryrun-name:hover {
  text-decoration: underline;
}

.text-tertiary {
  color: var(--autops-info);
  font-size: var(--autops-font-13);
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: var(--autops-space-md) 0 0;
}

.section-title {
  font-size: var(--autops-font-14);
  font-weight: 600;
  color: var(--autops-text-1);
  margin-bottom: var(--autops-space-md);
}

/* Step Items */
.steps-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-item {
  border: 1px solid var(--autops-bg-4);
  border-radius: 6px;
  padding: var(--autops-space-md);
  transition: border-color 0.2s;
}

.step-item.step-success {
  border-left: 3px solid var(--autops-success);
}

.step-item.step-failed {
  border-left: 3px solid var(--autops-danger);
}

.step-item.step-running {
  border-left: 3px solid var(--autops-primary);
}
</style>
