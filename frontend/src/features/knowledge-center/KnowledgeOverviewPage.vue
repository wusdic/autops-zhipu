<template>
  <div class="autops-page-container">
    <!-- Page Header -->
    <div class="autops-page-header">
      <div class="autops-page-title">知识总览</div>
      <div class="autops-page-desc">查看知识库整体情况，快速访问核心功能</div>
    </div>

    <!-- Stat Cards -->
    <el-row :gutter="16" class="metric-row">
      <el-col :span="6" v-for="stat in statCards" :key="stat.label">
        <div class="autops-metric-card" v-loading="statsLoading">
          <div class="metric-icon" :class="stat.bgClass">
            <el-icon :size="20"><component :is="stat.icon" /></el-icon>
          </div>
          <div class="metric-label">{{ stat.label }}</div>
          <div class="metric-value">{{ stat.value }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- Recent Knowledge Table -->
    <el-card class="main-card" shadow="never">
      <template #header>
        <div class="autops-card-header">
          <span class="card-title">最近更新的知识</span>
          <el-button type="primary" plain @click="router.push({ name: 'knowledge' })">
            查看全部 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>
      <el-table stripe
 :data="recentItems"
40| v-loading="tableLoading"
 empty-text="暂无知识"
 style="width: 100%"
 >
        <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="router.push('/knowledge/' + row.id)">
              {{ row.title }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="(getCategoryTagType(row.category)) as TagType">
              {{ row.category || '未分类' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="(getStatusTagType(row.status)) as TagType">
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
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, CircleCheck, Edit, Star, ArrowRight, Upload, List, View as Review, Notebook } from '@element-plus/icons-vue'
import { knowledgeService } from '@/shared/api'

const router = useRouter()

// --- State ---
const statsLoading = ref(false)
const tableLoading = ref(false)
const recentItems = ref<any[]>([])

const statCards = reactive([
  { label: '知识总数', value: 0, icon: Document, bgClass: 'bg-brand' },
  { label: '已发布', value: 0, icon: CircleCheck, bgClass: 'bg-success' },
  { label: '草稿', value: 0, icon: Edit, bgClass: 'bg-info' },
  { label: '平均评分', value: 0, icon: Star, bgClass: 'bg-warning' },
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
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes())
}

function getStatusTagType(status: string): TagType {
  const map: Record<string, TagType> = {
    published: 'success',
    draft: 'warning',
    review: '',
    rejected: 'danger',
    archived: 'info',
  }
  return (map[status] || 'info') as TagType
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

function getCategoryTagType(category: string): TagType {
  const map: Record<string, TagType> = {
    故障处理: 'danger',
    标准方案: 'success',
    经验沉淀: 'warning',
    操作指南: '',
    FAQ: 'info',
  }
  return (map[category] || 'info') as TagType
}

// --- Data Fetching ---
async function fetchStats() {
  statsLoading.value = true
  try {
    const res = await knowledgeService.stats()
    // /api/v1/knowledge/stats returns: { total, published, draft }
    // Response is wrapped: { code: 0, data: { total, published, draft } }
    const raw = res.data ?? {}
    const data = raw.data ?? raw
    statCards[0].value = data.total ?? 0
    statCards[1].value = data.published ?? 0
    statCards[2].value = data.draft ?? 0
    statCards[3].value = data.avg_score ?? data.average_rating ?? 0

    // Build category distribution
    if (data.categories && Array.isArray(data.categories)) {
      var catTotal = data.categories.reduce(function (s: number, c: any) { return s + (c.count || 0) }, 0) || 1
      var colors = ['#165dff', '#00b42a', '#ff7d00', '#722ed1', '#f53f3f', '#0fc6c2', '#f77234', '#3491fa']
      categories.value = data.categories.map(function (c: any, i: number) {
        return {
          name: c.name || c.category || '未分类',
          count: c.count || 0,
          percentage: Math.round(((c.count || 0) / catTotal) * 100),
          color: colors[i % colors.length],
        }
      })
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
.main-card {
  margin-bottom: var(--autops-space-lg);
  border-radius: var(--autops-radius-md);
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
  margin-bottom: var(--autops-space-lg);
}

.category-row:last-child {
  margin-bottom: 0;
}

.category-name {
  width: 80px;
  font-size: var(--autops-font-14);
  color: var(--autops-text-2);
  flex-shrink: 0;
}

.category-count {
  font-size: var(--autops-font-13);
  color: var(--autops-info);
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
  border-radius: var(--autops-radius-md);
  cursor: pointer;
  transition: background-color 0.2s;
}

.quick-link-item:hover {
  background-color: var(--autops-bg-3);
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
  font-size: var(--autops-font-14);
  font-weight: 500;
  color: var(--autops-text-1);
  margin-bottom: 2px;
}

.quick-link-desc {
  font-size: var(--autops-font-12);
  color: var(--autops-info);
}

.quick-link-arrow {
  color: var(--autops-text-4);
  font-size: var(--autops-font-14);
}

.text-muted {
  color: var(--autops-info);
  font-size: var(--autops-font-13);
}
</style>
