<template>
  <div class="knowledge-page">
    <!-- Page Header -->
    <div class="page-top">
      <span class="page-title">
        <el-icon style="margin-right: 6px"><Reading /></el-icon>
        知识库管理
      </span>
      <div class="top-actions">
        <el-button type="primary" :icon="Plus" @click="goCreate">新建知识</el-button>
        <el-button :icon="Upload" @click="goImport">导入</el-button>
        <el-button :icon="Download" @click="handleExport" :loading="exporting">导出</el-button>
      </div>
    </div>

    <!-- Statistics Cards -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">知识总数</div>
          </div>
          <el-icon class="stat-icon" :size="40" color="#409EFF"><Document /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ stats.incident_summary }}</div>
            <div class="stat-label">事件总结</div>
          </div>
          <el-icon class="stat-icon" :size="40" color="#E6A23C"><Warning /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ stats.runbook }}</div>
            <div class="stat-label">Runbook</div>
          </div>
          <el-icon class="stat-icon" :size="40" color="#67C23A"><Notebook /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ stats.standard_solution + stats.faq }}</div>
            <div class="stat-label">标准方案 / FAQ</div>
          </div>
          <el-icon class="stat-icon" :size="40" color="#909399"><InfoFilled /></el-icon>
        </el-card>
      </el-col>
    </el-row>

    <!-- Filters & Search -->
    <el-card shadow="hover" class="filter-card">
      <el-row :gutter="16" align="middle">
        <el-col :span="8">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索知识标题、内容..."
            :prefix-icon="Search"
            clearable
            @clear="loadList"
            @keyup.enter="loadList"
          />
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.article_type" placeholder="类型筛选" clearable @change="loadList" style="width: 100%">
            <el-option label="事件总结" value="incident_summary" />
            <el-option label="Runbook" value="runbook" />
            <el-option label="标准方案" value="standard_solution" />
            <el-option label="FAQ" value="faq" />
            <el-option label="最佳实践" value="best_practice" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.risk_level" placeholder="风险等级" clearable @change="loadList" style="width: 100%">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.status" placeholder="状态" clearable @change="loadList" style="width: 100%">
            <el-option label="已发布" value="published" />
            <el-option label="草稿" value="draft" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="sortBy" placeholder="排序方式" @change="loadList" style="width: 100%">
            <el-option label="最近更新" value="updated_at" />
            <el-option label="创建时间" value="created_at" />
            <el-option label="浏览量" value="views" />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <!-- Knowledge Table -->
    <el-card shadow="hover" style="margin-top: 16px">
      <el-table
        v-loading="loading"
        :data="knowledgeList"
        stripe
        @sort-change="onSortChange"
        style="width: 100%"
      >
        <el-table-column prop="title" label="标题" min-width="260" show-overflow-tooltip>
          <template #default="{ row }">
            <router-link :to="{ name: 'knowledge-detail', params: { id: row.id } }" class="title-link">
              {{ row.title }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="130">
          <template #default="{ row }">
            <el-tag :type="typeTagColor(row.article_type)" size="small">
              {{ typeLabel(row.article_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风险等级" width="100">
          <template #default="{ row }">
            <el-tag :type="riskTagType(row.risk_level)" size="small">{{ row.risk_level || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small">
              {{ row.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="版本" width="80" align="center">
          <template #default="{ row }">v{{ row.version || 1 }}</template>
        </el-table-column>
        <el-table-column label="浏览" width="80" align="center">
          <template #default="{ row }">{{ row.views || 0 }}</template>
        </el-table-column>
        <el-table-column label="评分" width="90" align="center">
          <template #default="{ row }">
            <span v-if="row.rating_avg">{{ row.rating_avg.toFixed(1) }} ⭐</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="170" sortable="custom">
          <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="goDetail(row.id)">查看</el-button>
            <el-button text type="primary" size="small" @click="goEdit(row.id)">编辑</el-button>
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
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Reading, Plus, Upload, Download, Search, Document, Warning,
  Notebook, InfoFilled,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()

// ─── State ───────────────────────────────────────────────────────────
const loading = ref(false)
const exporting = ref(false)
const knowledgeList = ref<any[]>([])

const filters = reactive({
  keyword: '',
  article_type: '',
  risk_level: '',
  status: '',
})

const sortBy = ref('updated_at')
const sortOrder = ref<string>('descending')

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const stats = reactive({
  total: 0,
  incident_summary: 0,
  runbook: 0,
  standard_solution: 0,
  faq: 0,
  best_practice: 0,
})

// ─── Type Helpers ────────────────────────────────────────────────────
function typeLabel(t: string) {
  const m: Record<string, string> = {
    incident_summary: '事件总结',
    runbook: 'Runbook',
    standard_solution: '标准方案',
    faq: 'FAQ',
    best_practice: '最佳实践',
  }
  return m[t] || t || '-'
}

function typeTagColor(t: string) {
  const m: Record<string, string> = {
    incident_summary: 'warning',
    runbook: 'success',
    standard_solution: '',
    faq: 'info',
    best_practice: '',
  }
  return m[t] || ''
}

function riskTagType(level: string) {
  if (level === 'high') return 'danger'
  if (level === 'medium') return 'warning'
  return 'info'
}

function formatTime(t: string) {
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
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.article_type) params.article_type = filters.article_type
    if (filters.risk_level) params.risk_level = filters.risk_level
    if (filters.status) params.status = filters.status
    if (sortBy.value) {
      params.sort_by = sortBy.value
      params.sort_order = sortOrder.value === 'ascending' ? 'asc' : 'desc'
    }

    const { data } = await api.get(API.KNOWLEDGE, { params })
    if (data.code === 0) {
      const result = data.data
      knowledgeList.value = result.items || result || []
      pagination.total = result.total || knowledgeList.value.length
    }
  } catch (e: any) {
    ElMessage.error('加载知识列表失败: ' + (e.message || e))
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const { data } = await api.get(API.KNOWLEDGE_STATS)
    if (data.code === 0) {
      const d = data.data
      stats.total = d.total || 0
      stats.incident_summary = d.incident_summary || 0
      stats.runbook = d.runbook || 0
      stats.standard_solution = d.standard_solution || 0
      stats.faq = d.faq || 0
      stats.best_practice = d.best_practice || 0
    }
  } catch {
    // Fallback: compute from list
    try {
      const { data } = await api.get(API.KNOWLEDGE, { params: { page_size: 1 } })
      if (data.code === 0) {
        stats.total = data.data?.total || knowledgeList.value.length
      }
    } catch { /* ignore */ }
  }
}

function onSortChange({ prop, order }: { prop: string; order: string | null }) {
  if (prop) {
    sortBy.value = prop
    sortOrder.value = order || 'descending'
  }
  loadList()
}

// ─── Export ──────────────────────────────────────────────────────────
async function handleExport() {
  exporting.value = true
  try {
    const params: Record<string, any> = {}
    if (filters.article_type) params.article_type = filters.article_type
    if (filters.keyword) params.keyword = filters.keyword

    const { data } = await api.get(API.KNOWLEDGE_EXPORT, {
      params,
      responseType: 'blob',
    })
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `knowledge-export-${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e: any) {
    // Fallback: export current list as JSON
    try {
      const jsonStr = JSON.stringify(knowledgeList.value, null, 2)
      const blob = new Blob([jsonStr], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `knowledge-export-${new Date().toISOString().slice(0, 10)}.json`
      a.click()
      URL.revokeObjectURL(url)
      ElMessage.success('导出成功（客户端模式）')
    } catch {
      ElMessage.error('导出失败: ' + (e.message || e))
    }
  } finally {
    exporting.value = false
  }
}

// ─── Navigation ──────────────────────────────────────────────────────
function goCreate() {
  router.push({ name: 'knowledge-import' })
}

function goImport() {
  router.push({ name: 'knowledge-import' })
}

function goDetail(id: string) {
  router.push({ name: 'knowledge-detail', params: { id } })
}

function goEdit(id: string) {
  router.push({ name: 'knowledge-edit', params: { id } })
}

// ─── Init ────────────────────────────────────────────────────────────
onMounted(() => {
  loadList()
  loadStats()
})
</script>

<style scoped>
.page-top {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}
.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
}
.top-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}
.stats-row {
  margin-bottom: 16px;
}
.stat-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
}
.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 16px 20px;
}
.stat-content {
  display: flex;
  flex-direction: column;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}
.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
.stat-icon {
  opacity: 0.6;
}
.filter-card {
  margin-bottom: 0;
}
.title-link {
  color: #409EFF;
  text-decoration: none;
  font-weight: 500;
}
.title-link:hover {
  text-decoration: underline;
}
.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
.text-muted {
  color: #c0c4cc;
}
</style>
