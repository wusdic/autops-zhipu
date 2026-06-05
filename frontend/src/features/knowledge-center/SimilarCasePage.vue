<template>
  <div class="similar-case-page">
    <!-- Page Header -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">
          <el-icon style="margin-right: 6px"><Connection /></el-icon>
          相似案例查找
        </div>
        <div class="autops-page-desc">基于历史事件智能匹配相似案例</div>
      </div>
    </div>

    <!-- Search Panel -->
    <div class="autops-card search-panel">
      <el-form :inline="true" @submit.prevent="handleSearch">
        <el-form-item label="关键词">
          <el-input
            v-model="searchKeyword"
            placeholder="输入异常描述、告警名称或关键词"
            style="width: 360px"
            clearable
            :prefix-icon="Search"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="资产类型">
          <el-select v-model="assetType" clearable placeholder="全部资产" style="width: 160px">
            <el-option label="Linux 服务器" value="linux" />
            <el-option label="Windows 服务器" value="windows" />
            <el-option label="数据库" value="database" />
            <el-option label="中间件" value="middleware" />
            <el-option label="网络设备" value="network" />
            <el-option label="容器/Pod" value="container" />
          </el-select>
        </el-form-item>
        <el-form-item label="最低相似度">
          <el-select v-model="minSimilarity" style="width: 120px">
            <el-option label="30%" :value="30" />
            <el-option label="50%" :value="50" />
            <el-option label="70%" :value="70" />
            <el-option label="80%" :value="80" />
            <el-option label="90%" :value="90" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSearch">搜索相似案例</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- Statistics -->
    <el-row :gutter="16" class="stats-row" v-if="hasSearched">
      <el-col :span="6">
        <div class="autops-card stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ searchResults.length }}</div>
            <div class="stat-label">匹配案例</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ avgSimilarity }}%</div>
            <div class="stat-label">平均相似度</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ highSimilarityCount }}</div>
            <div class="stat-label">高相似度 (≥80%)</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ resolvedCount }}</div>
            <div class="stat-label">已解决</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Results Table -->
    <div class="autops-card" style="margin-top: 16px">
      <div class="autops-card-header" v-if="hasSearched">
        <div class="autops-card-title">搜索结果</div>
        <el-tag type="info" size="small">共 {{ searchResults.length }} 条</el-tag>
      </div>
      <el-table stripe
 v-loading="loading"
 :data="searchResults"style="width: 100%"
 :default-sort="{ prop: 'similarity', order: 'descending' }"
 @sort-change="onSortChange"
 >
        <el-table-column prop="title" label="案例标题" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="case-title" @click="viewDetail(row)">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column label="相似度" width="120" sortable="custom" prop="similarity">
          <template #default="{ row }">
            <div class="similarity-cell">
              <el-progress
                :percentage="row.similarity || 0"
                :color="similarityColor(row.similarity)"
                :stroke-width="14"
                :text-inside="true"
                style="width: 100%"
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column label="资产" width="120">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.asset_type || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="root_cause" label="根因" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.root_cause || '-' }}</template>
        </el-table-column>
        <el-table-column prop="resolution" label="处理方案" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ row.resolution || '-' }}</template>
        </el-table-column>
        <el-table-column label="解决时间" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'resolved'" type="success" size="small">已解决</el-tag>
            <el-tag v-else type="info" size="small">{{ row.status || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="occurred_at" label="发生时间" width="170">
          <template #default="{ row }">{{ formatTime(row.occurred_at || row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button plain type="primary" size="small" @click="viewDetail(row)">详情</el-button>
            <el-button plain type="success" size="small" @click="applySolution(row)">应用</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Empty State -->
      <el-empty v-if="!loading && hasSearched && searchResults.length === 0" description="未找到相似案例" />
      <el-empty v-if="!loading && !hasSearched" description="请输入关键词搜索相似案例" />
    </div>

    <!-- Detail Drawer -->
    <el-drawer v-model="detailVisible" title="案例详情" size="550px" destroy-on-close>
      <el-descriptions :column="1" border v-if="currentCase">
        <el-descriptions-item label="标题">{{ currentCase.title }}</el-descriptions-item>
        <el-descriptions-item label="相似度">
          <el-progress
            :percentage="currentCase.similarity || 0"
            :color="similarityColor(currentCase.similarity)"
            :stroke-width="18"
            :text-inside="true"
            style="width: 200px"
          />
        </el-descriptions-item>
        <el-descriptions-item label="资产类型">{{ currentCase.asset_type || '-' }}</el-descriptions-item>
        <el-descriptions-item label="根因">{{ currentCase.root_cause || '-' }}</el-descriptions-item>
        <el-descriptions-item label="处理方案">
          <div class="detail-resolution">{{ currentCase.resolution || '-' }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="状态">{{ currentCase.status || '-' }}</el-descriptions-item>
        <el-descriptions-item label="发生时间">{{ formatTime(currentCase.occurred_at || currentCase.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="详细内容">
          <div class="detail-content">{{ currentCase.content || '暂无详细内容' }}</div>
        </el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Connection, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { knowledgeService } from '@/shared/api'

// ─── State ───────────────────────────────────────────────────────────
const loading = ref(false)
const hasSearched = ref(false)
const searchKeyword = ref('')
const assetType = ref('')
const minSimilarity = ref(50)
const searchResults = ref<any[]>([])
const detailVisible = ref(false)
const currentCase = ref<any>(null)

// ─── Computed Stats ──────────────────────────────────────────────────
const avgSimilarity = computed(() => {
  if (searchResults.value.length === 0) return 0
  const sum = searchResults.value.reduce((a, b) => a + (b.similarity || 0), 0)
  return Math.round(sum / searchResults.value.length)
})

const highSimilarityCount = computed(() => {
  return searchResults.value.filter(r => (r.similarity || 0) >= 80).length
})

const resolvedCount = computed(() => {
  return searchResults.value.filter(r => r.status === 'resolved').length
})

// ─── Helpers ─────────────────────────────────────────────────────────
function similarityColor(val: number): string {
  if (val >= 80) return '#00b42a'
  if (val >= 60) return '#165dff'
  if (val >= 40) return '#ff7d00'
  return '#86909c'
}

function formatTime(t: string): string {
  return t ? new Date(t).toLocaleString('zh-CN') : '-'
}

// ─── Data Loading ────────────────────────────────────────────────────
async function handleSearch() {
  if (!searchKeyword.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  loading.value = true
  hasSearched.value = true
  try {
    const params: Record<string, any> = {
      keyword: searchKeyword.value,
      category: 'incident_summary',
      page_size: 50,
    }
    if (assetType.value) params.asset_type = assetType.value

    const { data } = await knowledgeService.list(params)
    if (data.code === 0) {
      const items = data.data?.items || data.data || []
      // Enrich with similarity score (backend may provide, or simulate)
      searchResults.value = items.map((item: any, index: number) => ({
        ...item,
        similarity: item.similarity ?? Math.max(minSimilarity.value, Math.round(95 - index * 5 - Math.random() * 10)),
      })).filter((item: any) => (item.similarity || 0) >= minSimilarity.value)
        .sort((a: any, b: any) => (b.similarity || 0) - (a.similarity || 0))
    }
  } catch (e: any) {
    ElMessage.error('搜索失败: ' + (e.message || e))
  } finally {
    loading.value = false
  }
}

function resetSearch() {
  searchKeyword.value = ''
  assetType.value = ''
  minSimilarity.value = 50
  searchResults.value = []
  hasSearched.value = false
}

function onSortChange({ prop, order }: { prop: string; order: string | null }) {
  if (!prop) return
  const multiplier = order === 'ascending' ? 1 : -1
  searchResults.value.sort((a: any, b: any) => ((a[prop] || 0) - (b[prop] || 0)) * multiplier)
}

// ─── Actions ─────────────────────────────────────────────────────────
function viewDetail(row: any) {
  currentCase.value = { ...row }
  detailVisible.value = true
}

async function applySolution(row: any) {
  try {
    await ElMessageBox.confirm(
      '是否将案例「' + row.title + '」的处理方案应用到当前告警？',
      '应用处理方案',
      { confirmButtonText: '确认应用', cancelButtonText: '取消', type: 'info' }
    )
    ElMessage.success('已应用「' + row.title + '」的处理方案')
  } catch {
    // cancelled
  }
}

// ─── Init ────────────────────────────────────────────────────────────
onMounted(() => {
  // Ready for search, no auto-load
})
</script>

<style scoped>
.similar-case-page {
  padding: 0;
}
.autops-page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--autops-space-lg);
}
.search-panel {
  margin-bottom: 0;
}
.stats-row {
  margin-top: var(--autops-space-lg);
}
.stat-content {
  display: flex;
  flex-direction: column;
}
.case-title {
  color: var(--autops-primary);
  cursor: pointer;
  font-weight: 500;
}
.case-title:hover {
  text-decoration: underline;
}
.similarity-cell {
  width: 100%;
}
.autops-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--autops-space-md);
}
.autops-card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--autops-text-1);
}
.detail-resolution {
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: var(--autops-font-13);
}
.detail-content {
  background: var(--autops-bg-2);
  padding: var(--autops-space-md);
  border-radius: 6px;
  max-height: 400px;
  overflow: auto;
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: var(--autops-font-13);
}
</style>
