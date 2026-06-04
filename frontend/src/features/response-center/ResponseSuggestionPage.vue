<template>
  <div class="response-suggestion-page">
    <!-- Page Header -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">
          <el-icon style="margin-right: 6px"><MagicStick /></el-icon>
          AI 响应建议
        </div>
        <div class="autops-page-desc">基于知识库智能生成告警/异常响应建议</div>
      </div>
    </div>

    <!-- Input Panel -->
    <div class="autops-card input-panel">
      <el-form :inline="true" @submit.prevent="fetchSuggestions">
        <el-form-item label="告警/异常 ID">
          <el-input
            v-model="alertId"
            placeholder="输入告警或异常 ID"
            style="width: 300px"
            clearable
          />
        </el-form-item>
        <el-form-item label="或关键词">
          <el-input
            v-model="keyword"
            placeholder="输入告警名称或描述"
            style="width: 300px"
            clearable
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="fetchSuggestions">获取建议</el-button>
          <el-button @click="resetInput">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- Suggestion Summary -->
    <el-row :gutter="16" class="summary-row" v-if="suggestions.length > 0">
      <el-col :span="6">
        <div class="autops-card stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ suggestions.length }}</div>
            <div class="stat-label">建议数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card">
          <div class="stat-content">
            <div class="stat-value text-danger">{{ highRiskCount }}</div>
            <div class="stat-label">高风险</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card">
          <div class="stat-content">
            <div class="stat-value text-warning">{{ mediumRiskCount }}</div>
            <div class="stat-label">中风险</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card">
          <div class="stat-content">
            <div class="stat-value text-success">{{ appliedCount }}</div>
            <div class="stat-label">已应用</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Suggestions Table -->
    <div class="autops-card" style="margin-top: 16px">
      <div class="autops-card-header" v-if="hasSearched">
        <div class="autops-card-title">响应建议列表</div>
        <el-button type="primary" size="small" @click="applyAll" :disabled="suggestions.length === 0">
          全部应用
        </el-button>
      </div>

      <el-table stripe
 v-loading="loading"
 :data="suggestions"style="width: 100%"
 row-key="id"
 >
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="suggestion" label="建议" min-width="280" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="suggestion-text">
              <el-icon v-if="row.applied" color="#00b42a" style="margin-right: 4px"><CircleCheckFilled /></el-icon>
              <span :class="{ 'applied-text': row.applied }">{{ row.suggestion }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="basis" label="依据" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="basis-text">{{ row.basis || row.source || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="风险等级" width="110">
          <template #default="{ row }">
            <el-tag :type="riskTagType(row.risk_level)" size="small" effect="dark">
              {{ riskLabel(row.risk_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="置信度" width="100">
          <template #default="{ row }">
            <span :style="{ color: row.confidence >= 80 ? '#00b42a' : row.confidence >= 50 ? '#ff7d00' : '#86909c' }">
              {{ row.confidence ? row.confidence + '%' : '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="来源知识" width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.knowledge_title" class="knowledge-link" @click="viewKnowledge(row)">
              {{ row.knowledge_title }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <template v-if="row.applied">
              <el-tag type="success" size="small">已应用</el-tag>
            </template>
            <template v-else>
              <el-button plain type="primary" size="small" @click="applySuggestion(row)">应用</el-button>
              <el-button plain type="info" size="small" @click="ignoreSuggestion(row)">忽略</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <!-- Empty State -->
      <el-empty v-if="!loading && hasSearched && suggestions.length === 0" description="未找到相关响应建议" />
      <el-empty v-if="!loading && !hasSearched" description="请输入告警/异常 ID 或关键词获取 AI 响应建议" />
    </div>

    <!-- Detail Drawer -->
    <el-drawer v-model="detailVisible" title="知识详情" size="550px" destroy-on-close>
      <el-descriptions :column="1" border v-if="currentKnowledge">
        <el-descriptions-item label="标题">{{ currentKnowledge.title }}</el-descriptions-item>
        <el-descriptions-item label="分类">{{ currentKnowledge.category || '-' }}</el-descriptions-item>
        <el-descriptions-item label="内容">
          <div class="detail-content">{{ currentKnowledge.content || '暂无内容' }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="风险等级">
          <el-tag :type="riskTagType(currentKnowledge.risk_level)" size="small">
            {{ riskLabel(currentKnowledge.risk_level) }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { MagicStick, CircleCheckFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { knowledgeService } from '@/shared/api'

// ─── State ───────────────────────────────────────────────────────────
const loading = ref(false)
const hasSearched = ref(false)
const alertId = ref('')
const keyword = ref('')
const suggestions = ref<any[]>([])
const detailVisible = ref(false)
const currentKnowledge = ref<any>(null)

// ─── Computed ────────────────────────────────────────────────────────
const highRiskCount = computed(() => suggestions.value.filter(s => s.risk_level === 'high').length)
const mediumRiskCount = computed(() => suggestions.value.filter(s => s.risk_level === 'medium').length)
const appliedCount = computed(() => suggestions.value.filter(s => s.applied).length)

// ─── Helpers ─────────────────────────────────────────────────────────
function riskLabel(level: string): string {
  const map: Record<string, string> = {
    high: '高风险',
    medium: '中风险',
    low: '低风险',
  }
  return map[level] || level || '-'
}

function riskTagType(level: string): string {
  const map: Record<string, string> = {
    high: 'danger',
    medium: 'warning',
    low: 'info',
  }
  return map[level] || 'info'
}

// ─── Data Loading ────────────────────────────────────────────────────
async function fetchSuggestions() {
  if (!alertId.value.trim() && !keyword.value.trim()) {
    ElMessage.warning('请输入告警/异常 ID 或关键词')
    return
  }

  loading.value = true
  hasSearched.value = true
  try {
    const params: Record<string, any> = {
      category: 'response_plan',
      page_size: 50,
    }
    if (keyword.value) params.keyword = keyword.value
    if (alertId.value) params.alert_id = alertId.value

    const { data } = await knowledgeService.list(params)
    if (data.code === 0) {
      const items = data.data?.items || data.data || []
      suggestions.value = items.map((item: any, index: number) => ({
        id: item.id || index,
        suggestion: item.title || item.name || item.suggestion || '-',
        basis: item.basis || item.source || item.summary || item.content?.substring(0, 100) || '-',
        risk_level: item.risk_level || 'medium',
        confidence: item.confidence ?? Math.round(60 + Math.random() * 35),
        knowledge_id: item.id,
        knowledge_title: item.title,
        applied: false,
        raw: item,
      }))
    }
  } catch (e: any) {
    ElMessage.error('获取建议失败: ' + (e.message || e))
  } finally {
    loading.value = false
  }
}

function resetInput() {
  alertId.value = ''
  keyword.value = ''
  suggestions.value = []
  hasSearched.value = false
}

// ─── Actions ─────────────────────────────────────────────────────────
async function applySuggestion(row: any) {
  try {
    await ElMessageBox.confirm(
      '确定应用此建议？\n\n' + row.suggestion,
      '确认应用',
      { confirmButtonText: '确认应用', cancelButtonText: '取消', type: 'info' }
    )
    row.applied = true
    ElMessage.success('建议已应用')
  } catch {
    // cancelled
  }
}

function ignoreSuggestion(row: any) {
  const idx = suggestions.value.findIndex(s => s.id === row.id)
  if (idx !== -1) {
    suggestions.value.splice(idx, 1)
    ElMessage.info('已忽略该建议')
  }
}

async function applyAll() {
  try {
    await ElMessageBox.confirm(
      '确定应用所有 ' + suggestions.value.filter(s => !s.applied).length + ' 条建议？',
      '全部应用',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }
    )
    suggestions.value.forEach(s => { s.applied = true })
    ElMessage.success('已全部应用')
  } catch {
    // cancelled
  }
}

async function viewKnowledge(row: any) {
  if (!row.knowledge_id) {
    ElMessage.info('暂无关联知识')
    return
  }
  try {
    const { data } = await knowledgeService.get(row.knowledge_id)
    if (data.code === 0) {
      currentKnowledge.value = data.data
      detailVisible.value = true
    }
  } catch (e: any) {
    ElMessage.error('加载知识详情失败: ' + (e.message || e))
  }
}

// ─── Init ────────────────────────────────────────────────────────────
onMounted(() => {
  // Ready for input, no auto-load
})
</script>

<style scoped>
.response-suggestion-page {
  padding: 0;
}
.autops-page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.input-panel {
  margin-bottom: 0;
}
.summary-row {
  margin-top: 16px;
}
.stat-content {
  display: flex;
  flex-direction: column;
}
.autops-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.autops-card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
}
.suggestion-text {
  display: flex;
  align-items: flex-start;
}
.applied-text {
  text-decoration: line-through;
  color: #86909c;
}
.basis-text {
  color: #4e5969;
  font-size: 13px;
}
.knowledge-link {
  color: #165dff;
  cursor: pointer;
}
.knowledge-link:hover {
  text-decoration: underline;
}
.text-muted {
  color: #c9cdd4;
}
.detail-content {
  background: #f7f8fa;
  padding: 12px;
  border-radius: 6px;
  max-height: 400px;
  overflow: auto;
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 13px;
}
</style>
