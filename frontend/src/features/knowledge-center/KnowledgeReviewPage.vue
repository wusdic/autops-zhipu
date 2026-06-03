<template>
  <div class="knowledge-review-page">
    <!-- Page Header -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">
          <el-icon style="margin-right: 6px"><Reading /></el-icon>
          知识审核
        </div>
        <div class="autops-page-desc">审核待发布的知识文章</div>
      </div>
    </div>

    <!-- Status Tabs -->
    <div class="autops-card">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="待审核" name="pending_review">
          <template #label>
            <span>待审核 <el-badge v-if="pendingCount > 0" :value="pendingCount" class="tab-badge" /></span>
          </template>
        </el-tab-pane>
        <el-tab-pane label="草稿" name="draft" />
        <el-tab-pane label="已发布" name="published" />
        <el-tab-pane label="已驳回" name="rejected" />
        <el-tab-pane label="全部" name="all" />
      </el-tabs>

      <!-- Search & Filters -->
      <el-row :gutter="16" class="filter-row">
        <el-col :span="8">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索标题、分类..."
            :prefix-icon="Search"
            clearable
            @clear="loadList"
            @keyup.enter="loadList"
          />
        </el-col>
        <el-col :span="5">
          <el-select v-model="filters.category" placeholder="分类筛选" clearable @change="loadList" style="width: 100%">
            <el-option label="事件总结" value="incident_summary" />
            <el-option label="Runbook" value="runbook" />
            <el-option label="标准方案" value="standard_solution" />
            <el-option label="FAQ" value="faq" />
            <el-option label="最佳实践" value="best_practice" />
            <el-option label="复盘报告" value="postmortem" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="loadList">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-col>
      </el-row>

      <!-- Table -->
      <el-table stripe
 v-loading="loading"
 :data="tableData"style="width: 100%"
 @sort-change="onSortChange"
 >
        <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="title-text" @click="openReview(row)">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column label="分类" width="130">
          <template #default="{ row }">
            <el-tag :type="categoryTagType(row.category)" size="small">
              {{ categoryLabel(row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="submitted_by" label="提交者" width="110" show-overflow-tooltip />
        <el-table-column prop="submitted_at" label="提交时间" width="170" sortable="custom">
          <template #default="{ row }">{{ formatTime(row.submitted_at || row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending_review'">
              <el-button text type="primary" size="small" @click="openReview(row)">审核</el-button>
              <el-button text type="success" size="small" @click="handlePublish(row)">通过</el-button>
              <el-button text type="danger" size="small" @click="handleReject(row)">驳回</el-button>
            </template>
            <template v-else-if="row.status === 'draft'">
              <el-button text type="primary" size="small" @click="openReview(row)">查看</el-button>
              <el-button text type="warning" size="small" @click="handleSubmit(row)">提交审核</el-button>
            </template>
            <template v-else>
              <el-button text type="primary" size="small" @click="openReview(row)">查看</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadList"
          @current-change="loadList"
        />
      </div>
    </div>

    <!-- Review Dialog -->
    <el-dialog v-model="reviewDialogVisible" title="知识审核" width="780px" destroy-on-close>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="标题" :span="2">{{ currentItem.title }}</el-descriptions-item>
        <el-descriptions-item label="分类">{{ categoryLabel(currentItem.category) }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTagType(currentItem.status)" size="small">{{ statusLabel(currentItem.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="提交者">{{ currentItem.submitted_by }}</el-descriptions-item>
        <el-descriptions-item label="提交时间">{{ formatTime(currentItem.submitted_at || currentItem.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="内容" :span="2">
          <div class="review-content">{{ currentItem.content }}</div>
        </el-descriptions-item>
      </el-descriptions>
      <el-form label-width="80px" style="margin-top: 16px">
        <el-form-item label="审核意见">
          <el-input
            type="textarea"
            v-model="reviewComment"
            :rows="4"
            placeholder="请输入审核意见（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="handleReject(currentItem)">驳回</el-button>
        <el-button type="success" @click="handlePublish(currentItem)">通过并发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Reading, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { knowledgeService } from '@/shared/api'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

// ─── State ───────────────────────────────────────────────────────────
const loading = ref(false)
const tableData = ref<any[]>([])
const reviewDialogVisible = ref(false)
const reviewComment = ref('')
const activeTab = ref('pending_review')
const pendingCount = ref(0)

const currentItem = reactive<any>({
  id: '',
  title: '',
  content: '',
  category: '',
  status: '',
  submitted_by: '',
  submitted_at: '',
})

const filters = reactive({
  keyword: '',
  category: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const sortBy = ref('submitted_at')
const sortOrder = ref<string>('desc')

// ─── Helpers ─────────────────────────────────────────────────────────
function statusLabel(status: string): string {
  const map: Record<string, string> = {
    draft: '草稿',
    pending_review: '待审核',
    published: '已发布',
    rejected: '已驳回',
  }
  return map[status] || status || '-'
}

function statusTagType(status: string): string {
  const map: Record<string, string> = {
    draft: 'info',
    pending_review: 'warning',
    published: 'success',
    rejected: 'danger',
  }
  return map[status] || 'info'
}

function categoryLabel(cat: string): string {
  const map: Record<string, string> = {
    incident_summary: '事件总结',
    runbook: 'Runbook',
    standard_solution: '标准方案',
    faq: 'FAQ',
    best_practice: '最佳实践',
    postmortem: '复盘报告',
    response_plan: '响应方案',
  }
  return map[cat] || cat || '-'
}

function categoryTagType(cat: string): string {
  const map: Record<string, string> = {
    incident_summary: 'warning',
    runbook: 'success',
    standard_solution: '',
    faq: 'info',
    best_practice: '',
    postmortem: 'danger',
    response_plan: '',
  }
  return map[cat] || ''
}

function formatTime(t: string): string {
  return t ? new Date(t).toLocaleString('zh-CN') : '-'
}

// ─── Data Loading ────────────────────────────────────────────────────
async function loadList() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (activeTab.value !== 'all') {
      params.status = activeTab.value
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.category) params.category = filters.category
    if (sortBy.value) {
      params.sort_by = sortBy.value
      params.sort_order = sortOrder.value
    }

    const { data } = await knowledgeService.list(params)
    if (data.code === 0) {
      const result = data.data
      tableData.value = result.items || result || []
      pagination.total = result.total || tableData.value.length
    }
  } catch (e: any) {
    ElMessage.error('加载审核列表失败: ' + (e.message || e))
  } finally {
    loading.value = false
  }
}

async function loadPendingCount() {
  try {
    const { data } = await knowledgeService.list({ status: 'pending_review', page_size: 1 })
    if (data.code === 0) {
      pendingCount.value = data.data?.total || 0
    }
  } catch {
    // silent
  }
}

function handleTabChange() {
  pagination.page = 1
  loadList()
}

function onSortChange({ prop, order }: { prop: string; order: string | null }) {
  if (prop) {
    sortBy.value = prop
    sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  }
  loadList()
}

function resetFilters() {
  filters.keyword = ''
  filters.category = ''
  pagination.page = 1
  loadList()
}

// ─── Actions ─────────────────────────────────────────────────────────
function openReview(row: any) {
  Object.assign(currentItem, row)
  reviewComment.value = ''
  reviewDialogVisible.value = true
}

async function handlePublish(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定通过并发布「${row.title || currentItem.title}」？`,
      '确认发布',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'success' }
    )
    const targetId = row.id || currentItem.id
    const { data } = await knowledgeService.publish(targetId)
    if (data.code === 0) {
      ElMessage.success('发布成功')
      reviewDialogVisible.value = false
      loadList()
      loadPendingCount()
    } else {
      ElMessage.error(data.message || '发布失败')
    }
  } catch {
    // cancelled
  }
}

async function handleReject(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定驳回「${row.title || currentItem.title}」？`,
      '确认驳回',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }
    )
    const targetId = row.id || currentItem.id
    const { data } = await knowledgeService.update(targetId, {
      status: 'rejected',
      review_comment: reviewComment.value,
    })
    if (data.code === 0) {
      ElMessage.success('已驳回')
      reviewDialogVisible.value = false
      loadList()
      loadPendingCount()
    } else {
      ElMessage.error(data.message || '操作失败')
    }
  } catch {
    // cancelled
  }
}

async function handleSubmit(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定将「${row.title}」提交审核？`,
      '确认提交',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'info' }
    )
    const { data } = await knowledgeService.update(row.id, { status: 'pending_review' })
    if (data.code === 0) {
      ElMessage.success('已提交审核')
      loadList()
      loadPendingCount()
    } else {
      ElMessage.error(data.message || '提交失败')
    }
  } catch {
    // cancelled
  }
}

// ─── Init ────────────────────────────────────────────────────────────
onMounted(() => {
  loadList()
  loadPendingCount()
})
</script>

<style scoped>
.knowledge-review-page {
  padding: 0;
}
.autops-page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.autops-page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1d2129;
  display: flex;
  align-items: center;
}
.filter-row {
  margin-bottom: 16px;
}
.title-text {
  color: #165dff;
  cursor: pointer;
  font-weight: 500;
}
.title-text:hover {
  text-decoration: underline;
}
.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
.review-content {
  background: #f7f8fa;
  padding: 12px;
  border-radius: 6px;
  max-height: 300px;
  overflow: auto;
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 13px;
}
.tab-badge {
  margin-left: 4px;
}
.tab-badge :deep(.el-badge__content) {
  top: 0;
}
</style>
