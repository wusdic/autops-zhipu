<template>
  <div class="knowledge-detail">
    <!-- 顶部导航 -->
    <div class="page-top">
      <el-button @click="goBack" :icon="ArrowLeft">返回知识列表</el-button>
      <div class="knowledge-title" v-if="article">
        <span class="name">{{ article.title }}</span>
        <el-tag :type="riskTagType(article.risk_level)" size="small" style="margin-left: 8px">
          {{ article.risk_level }}
        </el-tag>
        <el-tag :type="article.status === 'published' ? 'success' : 'info'" size="small" style="margin-left: 4px">
          {{ article.status === 'published' ? '已发布' : '草稿' }}
        </el-tag>
        <el-tag type="info" size="small" style="margin-left: 4px">
          👁 {{ article.views || 0 }}
        </el-tag>
      </div>
      <div class="top-actions" v-if="article">
        <el-button type="primary" :icon="Edit" @click="goEdit">编辑</el-button>
        <el-button
          v-if="article.status === 'draft'"
          type="success"
          :icon="Promotion"
          @click="publishArticle"
          :loading="publishing"
        >
          发布
        </el-button>
        <el-dropdown trigger="click" @command="handleMoreAction">
          <el-button :icon="MoreFilled">更多</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="convert-runbook" :icon="Notebook">
                转换为 Runbook
              </el-dropdown-item>
              <el-dropdown-item command="version-history" :icon="Clock">
                版本历史
              </el-dropdown-item>
              <el-dropdown-item command="delete" :icon="Delete" style="color: #F56C6C">
                删除
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div v-loading="loading" class="detail-body">
      <!-- 空状态 -->
      <el-empty v-if="!loading && !article" description="知识文章不存在或已被删除">
        <el-button type="primary" @click="goBack">返回列表</el-button>
      </el-empty>

      <template v-if="article">
        <!-- 基本信息 -->
        <el-card shadow="hover">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="标题" :span="2">{{ article.title }}</el-descriptions-item>
            <el-descriptions-item label="类型">
              <el-tag size="small">{{ typeLabel(article.article_type) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="风险等级">
              <el-tag :type="riskTagType(article.risk_level)" size="small">{{ article.risk_level }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="article.status === 'published' ? 'success' : 'info'" size="small">
                {{ article.status === 'published' ? '已发布' : '草稿' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="版本">v{{ article.version }}</el-descriptions-item>
            <el-descriptions-item label="浏览量">{{ article.views || 0 }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatTime(article.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ formatTime(article.updated_at) }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 正文内容 -->
        <el-card v-if="article.content" shadow="hover" style="margin-top: 16px">
          <template #header><span class="card-header-title">内容</span></template>
          <div v-html="renderMarkdown(article.content)" class="markdown-body" />
        </el-card>

        <!-- 诊断步骤 -->
        <el-card v-if="article.diagnosis_steps" shadow="hover" style="margin-top: 16px">
          <template #header><span class="card-header-title">诊断步骤</span></template>
          <div v-html="renderMarkdown(article.diagnosis_steps)" class="markdown-body" />
        </el-card>

        <!-- 处置步骤 -->
        <el-card v-if="article.resolution_steps" shadow="hover" style="margin-top: 16px">
          <template #header><span class="card-header-title">处置步骤</span></template>
          <div v-html="renderMarkdown(article.resolution_steps)" class="markdown-body" />
        </el-card>

        <!-- 验证步骤 -->
        <el-card v-if="article.verification_steps" shadow="hover" style="margin-top: 16px">
          <template #header><span class="card-header-title">验证步骤</span></template>
          <div v-html="renderMarkdown(article.verification_steps)" class="markdown-body" />
        </el-card>

        <!-- Rating / Useful Feedback -->
        <el-card shadow="hover" style="margin-top: 16px">
          <template #header><span class="card-header-title">评价与反馈</span></template>
          <div class="feedback-section">
            <div class="feedback-row">
              <span class="feedback-label">该知识是否对您有帮助？</span>
              <el-rate
                v-model="userRating"
                :texts="['无用', '不太有用', '一般', '有用', '非常有用']"
                show-text
                @change="submitRating"
              />
            </div>
            <div class="feedback-stats" v-if="article.rating_count > 0">
              <span>平均评分: {{ (article.rating_avg || 0).toFixed(1) }} ⭐</span>
              <span style="margin-left: 16px">{{ article.rating_count }} 人评价</span>
              <span style="margin-left: 16px">有用 {{ article.useful_count || 0 }} 人</span>
            </div>
            <div class="feedback-quick">
              <el-button-group style="margin-top: 12px">
                <el-button
                  :type="userFeedback === 'useful' ? 'success' : 'default'"
                  size="small"
                  @click="submitFeedback('useful')"
                >
                  👍 有用
                </el-button>
                <el-button
                  :type="userFeedback === 'not_useful' ? 'danger' : 'default'"
                  size="small"
                  @click="submitFeedback('not_useful')"
                >
                  👎 无用
                </el-button>
              </el-button-group>
            </div>
          </div>
        </el-card>

        <!-- Related Articles -->
        <el-card shadow="hover" style="margin-top: 16px" v-if="relatedArticles.length > 0">
          <template #header><span class="card-header-title">相关文章</span></template>
          <el-table :data="relatedArticles" stripe size="small" @row-click="goToRelated">
            <el-table-column prop="title" label="标题" min-width="260" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="related-title">{{ row.title }}</span>
              </template>
            </el-table-column>
            <el-table-column label="类型" width="130">
              <template #default="{ row }">
                <el-tag :type="typeTagColor(row.article_type)" size="small">{{ typeLabel(row.article_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="风险" width="80">
              <template #default="{ row }">
                <el-tag :type="riskTagType(row.risk_level)" size="small">{{ row.risk_level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="浏览" width="80" align="center">
              <template #default="{ row }">{{ row.views || 0 }}</template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- Version History Dialog -->
        <el-dialog v-model="showVersionHistory" title="版本历史" width="700px">
          <el-timeline v-if="versionHistory.length">
            <el-timeline-item
              v-for="ver in versionHistory"
              :key="ver.id || ver.version"
              :timestamp="formatTime(ver.created_at)"
              placement="top"
            >
              <el-card shadow="never" class="version-card">
                <div class="version-header">
                  <el-tag size="small">v{{ ver.version }}</el-tag>
                  <span class="version-author">{{ ver.author || ver.updated_by || '系统' }}</span>
                  <el-tag v-if="ver.version === article.version" type="success" size="small">当前版本</el-tag>
                </div>
                <div class="version-summary">{{ ver.change_summary || ver.summary || '无变更说明' }}</div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无版本历史记录" :image-size="80" />
        </el-dialog>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft, Edit, Promotion, MoreFilled, Notebook, Clock, Delete,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const route = useRoute()
const router = useRouter()

const knowledgeId = route.params.id as string
const loading = ref(false)
const publishing = ref(false)
const article = ref<any>(null)

// Rating & feedback state
const userRating = ref(0)
const userFeedback = ref('')
const ratingSubmitting = ref(false)

// Related articles
const relatedArticles = ref<any[]>([])

// Version history
const showVersionHistory = ref(false)
const versionHistory = ref<any[]>([])

// Convert to runbook
const converting = ref(false)

/** 文章类型映射 */
function typeLabel(t: string) {
  const m: Record<string, string> = {
    standard_solution: '标准方案',
    incident_summary: '事件总结',
    best_practice: '最佳实践',
    runbook: 'Runbook',
    faq: 'FAQ',
  }
  return m[t] || t || '-'
}

/** 类型标签颜色 */
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

/** 风险等级 Tag 类型 */
function riskTagType(level: string) {
  if (level === 'high') return 'danger'
  if (level === 'medium') return 'warning'
  return 'info'
}

/** 简易 Markdown 渲染 */
function renderMarkdown(text: string) {
  return text
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br/>')
}

/** 格式化时间 */
function formatTime(t: string) {
  return t ? new Date(t).toLocaleString('zh-CN') : '-'
}

/** 返回上一页 */
function goBack() {
  router.push({ name: 'knowledge' })
}

/** 跳转编辑页 */
function goEdit() {
  router.push({ name: 'knowledge-edit', params: { id: knowledgeId } })
}

/** Navigate to related article */
function goToRelated(row: any) {
  router.push({ name: 'knowledge-detail', params: { id: row.id } })
}

/** 加载知识详情 */
async function loadArticle() {
  loading.value = true
  try {
    const { data } = await api.get(API.KNOWLEDGE_DETAIL(knowledgeId))
    if (data.code === 0) {
      article.value = data.data
      // Load related and versions after article loads
      loadRelatedArticles()
      incrementViewCount()
    }
  } catch (e: any) {
    ElMessage.error('加载知识详情失败: ' + (e.message || e))
  } finally {
    loading.value = false
  }
}

/** Increment view count */
async function incrementViewCount() {
  try {
    await api.post(API.KNOWLEDGE_VIEW(knowledgeId))
  } catch {
    // silently fail - view count is non-critical
  }
}

/** 发布知识文章 */
async function publishArticle() {
  try {
    await ElMessageBox.confirm('确认发布该知识文章？发布后将对所有用户可见。', '发布确认', {
      confirmButtonText: '确认发布',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return // 用户取消
  }

  publishing.value = true
  try {
    const { data } = await api.post(API.KNOWLEDGE_PUBLISH(knowledgeId))
    if (data.code === 0) {
      ElMessage.success('发布成功')
      await loadArticle()
    }
  } catch (e: any) {
    ElMessage.error('发布失败: ' + (e.message || e))
  } finally {
    publishing.value = false
  }
}

/** Load related articles */
async function loadRelatedArticles() {
  try {
    const { data } = await api.get(API.KNOWLEDGE_RELATED(knowledgeId))
    if (data.code === 0) {
      relatedArticles.value = data.data || []
    }
  } catch {
    // Fallback: search by same type
    if (article.value?.article_type) {
      try {
        const { data } = await api.get(API.KNOWLEDGE, {
          params: { article_type: article.value.article_type, page_size: 6 },
        })
        if (data.code === 0) {
          const items = data.data?.items || data.data || []
          relatedArticles.value = items.filter((i: any) => i.id !== knowledgeId).slice(0, 5)
        }
      } catch { /* ignore */ }
    }
  }
}

/** Load version history */
async function loadVersionHistory() {
  try {
    const { data } = await api.get(API.KNOWLEDGE_VERSIONS(knowledgeId))
    if (data.code === 0) {
      versionHistory.value = data.data || []
    }
  } catch {
    versionHistory.value = []
  }
}

/** Submit rating */
async function submitRating(value: number) {
  if (!value || ratingSubmitting.value) return
  ratingSubmitting.value = true
  try {
    await api.post(API.KNOWLEDGE_FEEDBACK(knowledgeId), {
      rating: value,
    })
    ElMessage.success('评分已提交')
  } catch {
    ElMessage.warning('评分提交失败')
  } finally {
    ratingSubmitting.value = false
  }
}

/** Submit useful/not_useful feedback */
async function submitFeedback(type: 'useful' | 'not_useful') {
  userFeedback.value = type
  try {
    await api.post(API.KNOWLEDGE_FEEDBACK(knowledgeId), {
      feedback_type: type,
    })
    ElMessage.success('感谢您的反馈')
  } catch {
    ElMessage.warning('反馈提交失败')
  }
}

/** Convert to Runbook */
async function convertToRunbook() {
  try {
    await ElMessageBox.confirm(
      '将该知识文章转换为 Runbook？转换后将生成自动化执行手册。',
      '转换确认',
      { confirmButtonText: '确认转换', cancelButtonText: '取消', type: 'info' },
    )
  } catch {
    return
  }

  converting.value = true
  try {
    const { data } = await api.post(API.KNOWLEDGE_CONVERT_RUNBOOK(knowledgeId))
    if (data.code === 0) {
      ElMessage.success('已成功转换为 Runbook')
      await loadArticle()
    } else {
      ElMessage.error(data.message || '转换失败')
    }
  } catch (e: any) {
    ElMessage.error('转换失败: ' + (e.message || e))
  } finally {
    converting.value = false
  }
}

/** Handle "more" dropdown actions */
function handleMoreAction(command: string) {
  switch (command) {
    case 'convert-runbook':
      convertToRunbook()
      break
    case 'version-history':
      loadVersionHistory().then(() => {
        showVersionHistory.value = true
      })
      break
    case 'delete':
      handleDelete()
      break
  }
}

/** Delete article */
async function handleDelete() {
  try {
    await ElMessageBox.confirm('确认删除该知识文章？此操作不可恢复。', '删除确认', {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'error',
    })
  } catch {
    return
  }
  try {
    const { data } = await api.delete(API.KNOWLEDGE_DETAIL(knowledgeId))
    if (data.code === 0) {
      ElMessage.success('删除成功')
      goBack()
    }
  } catch (e: any) {
    ElMessage.error('删除失败: ' + (e.message || e))
  }
}

onMounted(() => loadArticle())
</script>

<style scoped>
.page-top {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}
.knowledge-title {
  margin-left: 16px;
  display: flex;
  align-items: center;
  flex: 1;
}
.knowledge-title .name {
  font-size: 18px;
  font-weight: 600;
}
.top-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}
.card-header-title {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}
.markdown-body {
  line-height: 1.8;
}
.markdown-body h2 {
  margin: 16px 0 8px;
  color: #303133;
}
.markdown-body h3 {
  margin: 12px 0 6px;
  color: #606266;
}
.markdown-body code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
}

/* Feedback Section */
.feedback-section {
  padding: 8px 0;
}
.feedback-row {
  display: flex;
  align-items: center;
  gap: 16px;
}
.feedback-label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}
.feedback-stats {
  margin-top: 8px;
  font-size: 13px;
  color: #909399;
}
.feedback-quick {
  margin-top: 4px;
}

/* Related Articles */
.related-title {
  color: #409EFF;
  cursor: pointer;
}
.related-title:hover {
  text-decoration: underline;
}

/* Version History */
.version-card {
  margin-bottom: 0;
}
.version-card :deep(.el-card__body) {
  padding: 12px 16px;
}
.version-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.version-author {
  font-size: 13px;
  color: #606266;
}
.version-summary {
  font-size: 13px;
  color: #909399;
}
</style>
