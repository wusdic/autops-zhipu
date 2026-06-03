<template>
  <div class="page-container">
    <!-- Page Header -->
    <div class="page-header">
      <h2>知识总览</h2>
      <p class="page-subtitle">查看知识库整体情况，快速访问核心功能</p>
    </div>

    <!-- Stat Cards -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6" v-for="stat in statCards" :key="stat.label">
        <el-card shadow="hover" class="stat-card" v-loading="statsLoading">
          <div class="stat-card-inner">
            <div class="stat-icon-wrap" :style="{ background: stat.bgColor }">
              <el-icon :size="24" :style="{ color: stat.color }">
                <component :is="stat.icon" />
              </el-icon>
            </div>
            <div class="stat-info">
              <el-statistic :title="stat.label" :value="stat.value" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Recent Knowledge Table -->
    <el-card class="main-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">最近更新的知识</span>
          <el-button type="primary" text @click="router.push({ name: 'knowledge' })">
            查看全部 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>
      <el-table
        :data="recentItems"
        stripe
        v-loading="tableLoading"
        empty-text="暂无知识"
        style="width: 100%"
      >
        <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="router.push(`/knowledge/${row.id}`)">
              {{ row.title }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="getCategoryTagType(row.category)">
              {{ row.category || '未分类' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="getStatusTagType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_by" label="创建者" width="120">
          <template #default="{ row }">
            <span>{{ row.created_by || row.author || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            <span class="text-muted">{{ formatTime(row.updated_at) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Quick Links + Category Stats -->
    <el-row :gutter="16" class="bottom-row">
      <!-- Category Distribution -->
      <el-col :span="12">
        <el-card class="main-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">知识分类统计</span>
            </div>
          </template>
          <div class="category-list" v-loading="statsLoading">
            <div v-for="cat in categories" :key="cat.name" class="category-row">
              <span class="category-name">{{ cat.name }}</span>
              <el-progress
                :percentage="cat.percentage"
                :stroke-width="12"
                :color="cat.color"
                style="flex: 1; margin: 0 16px"
              />
              <span class="category-count">{{ cat.count }} 篇</span>
            </div>
            <el-empty v-if="categories.length === 0 && !statsLoading" description="暂无分类数据" :image-size="60" />
          </div>
        </el-card>
      </el-col>

      <!-- Quick Links -->
      <el-col :span="12">
        <el-card class="main-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">快速访问</span>
            </div>
          </template>
          <div class="quick-links">
            <div
              v-for="link in quickLinks"
              :key="link.name"
              class="quick-link-item"
              @click="router.push(link.route)"
            >
              <div class="quick-link-icon" :style="{ background: link.bgColor, color: link.color }">
                <el-icon :size="22"><component :is="link.icon" /></el-icon>
              </div>
              <div class="quick-link-info">
                <div class="quick-link-title">{{ link.title }}</div>
                <div class="quick-link-desc">{{ link.description }}</div>
              </div>
              <el-icon class="quick-link-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, Checked, EditPen, StarFilled, ArrowRight, Upload, List, Review, Notebook } from '@element-plus/icons-vue'
import { knowledgeService } from '@/shared/api'

const router = useRouter()

// --- State ---
const statsLoading = ref(false)
const tableLoading = ref(false)
const recentItems = ref<any[]>([])

const statCards = reactive([
  { label: '知识总数', value: 0, icon: Document, color: '#165dff', bgColor: '#e8f3ff' },
  { label: '已发布', value: 0, icon: Checked, color: '#00b42a', bgColor: '#e8ffea' },
  { label: '草稿', value: 0, icon: EditPen, color: '#ff7d00', bgColor: '#fff7e8' },
  { label: '平均评分', value: 0, icon: StarFilled, color: '#722ed1', bgColor: '#f5e8ff' },
])

const categories = ref<{ name: string; count: number; percentage: number; color: string }[]>([])

const quickLinks = [
  {
    name: 'knowledge-list',
    title: '知识列表',
    description: '浏览和管理所有知识条目',
    icon: List,
    color: '#165dff',
    bgColor: '#e8f3ff',
    route: { name: 'knowledge' },
  },
  {
    name: 'knowledge-import',
    title: '知识导入',
    description: '批量导入外部知识文档',
    icon: Upload,
    color: '#00b42a',
    bgColor: '#e8ffea',
    route: { name: 'knowledge-import' },
  },
  {
    name: 'knowledge-review',
    title: '知识审核',
    description: '审核待发布的知识内容',
    icon: Review,
    color: '#ff7d00',
    bgColor: '#fff7e8',
    route: { name: 'knowledge-review' },
  },
  {
    name: 'prompt-templates',
    title: 'Prompt 模板',
    description: '管理 AI 提示词模板',
    icon: Notebook,
    color: '#722ed1',
    bgColor: '#f5e8ff',
    route: { name: 'prompt-templates' },
  },
]

// --- Helpers ---
function formatTime(val: string | number | null | undefined): string {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function getStatusTagType(status: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    published: 'success',
    draft: 'warning',
    review: '',
    rejected: 'danger',
    archived: 'info',
  }
  return map[status] || 'info'
}

function getStatusLabel(status: string): string {
  const map: Record<string, string> = {
    published: '已发布',
    draft: '草稿',
    review: '审核中',
    rejected: '已拒绝',
    archived: '已归档',
  }
  return map[status] || status || '未知'
}

function getCategoryTagType(category: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    故障处理: 'danger',
    标准方案: 'success',
    经验沉淀: 'warning',
    操作指南: '',
    FAQ: 'info',
  }
  return map[category] || 'info'
}

// --- Data Fetching ---
async function fetchStats() {
  statsLoading.value = true
  try {
    const res = await knowledgeService.stats()
    const data = res.data?.data ?? res.data ?? {}
    statCards[0].value = data.total ?? 0
    statCards[1].value = data.published ?? 0
    statCards[2].value = data.draft ?? 0
    statCards[3].value = data.avg_score ?? data.average_rating ?? 0

    // Build category distribution
    if (data.categories && Array.isArray(data.categories)) {
      const total = data.categories.reduce((s: number, c: any) => s + (c.count || 0), 0) || 1
      const colors = ['#165dff', '#00b42a', '#ff7d00', '#722ed1', '#f53f3f', '#0fc6c2', '#f77234', '#3491fa']
      categories.value = data.categories.map((c: any, i: number) => ({
        name: c.name || c.category || '未分类',
        count: c.count || 0,
        percentage: Math.round(((c.count || 0) / total) * 100),
        color: colors[i % colors.length],
      }))
    }
  } catch (err: any) {
    console.error('Failed to fetch knowledge stats:', err)
    ElMessage.error('获取知识统计信息失败')
  } finally {
    statsLoading.value = false
  }
}

async function fetchRecentItems() {
  tableLoading.value = true
  try {
    const res = await knowledgeService.list({ page: 1, page_size: 10 })
    const data = res.data?.data ?? res.data ?? {}
    recentItems.value = data.items ?? data.list ?? []
  } catch (err: any) {
    console.error('Failed to fetch recent knowledge:', err)
    ElMessage.error('获取最近知识列表失败')
  } finally {
    tableLoading.value = false
  }
}

// --- Lifecycle ---
onMounted(() => {
  fetchStats()
  fetchRecentItems()
})
</script>

<style scoped>
.page-container {
  padding: 24px;
  background: #f7f8fa;
  min-height: 100%;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1d2129;
  margin: 0 0 4px 0;
}

.page-subtitle {
  font-size: 14px;
  color: #86909c;
  margin: 0;
}

.stat-row {
  margin-bottom: 16px;
}

.stat-card {
  border-radius: 8px;
}

.stat-card-inner {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
}

.main-card {
  margin-bottom: 16px;
  border-radius: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

.bottom-row {
  margin-top: 0;
}

/* Category Distribution */
.category-list {
  min-height: 200px;
}

.category-row {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.category-row:last-child {
  margin-bottom: 0;
}

.category-name {
  width: 80px;
  font-size: 14px;
  color: #4e5969;
  flex-shrink: 0;
}

.category-count {
  font-size: 13px;
  color: #86909c;
  flex-shrink: 0;
  width: 50px;
  text-align: right;
}

/* Quick Links */
.quick-links {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.quick-link-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.quick-link-item:hover {
  background-color: #f2f3f5;
}

.quick-link-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 14px;
}

.quick-link-info {
  flex: 1;
}

.quick-link-title {
  font-size: 14px;
  font-weight: 500;
  color: #1d2129;
  margin-bottom: 2px;
}

.quick-link-desc {
  font-size: 12px;
  color: #86909c;
}

.quick-link-arrow {
  color: #c9cdd4;
  font-size: 14px;
}

.text-muted {
  color: #86909c;
  font-size: 13px;
}
</style>
