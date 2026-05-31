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
          {{ article.status }}
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
                {{ article.status }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="版本">v{{ article.version }}</el-descriptions-item>
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
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Edit, Promotion } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const route = useRoute()
const router = useRouter()

const knowledgeId = route.params.id as string
const loading = ref(false)
const publishing = ref(false)
const article = ref<any>(null)

/** 文章类型映射 */
function typeLabel(t: string) {
  const m: Record<string, string> = {
    standard_solution: '标准方案',
    incident_summary: '事件总结',
    best_practice: '最佳实践',
  }
  return m[t] || t || '-'
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

/** 加载知识详情 */
async function loadArticle() {
  loading.value = true
  try {
    const { data } = await api.get(API.KNOWLEDGE_DETAIL(knowledgeId))
    if (data.code === 0) {
      article.value = data.data
    }
  } catch (e: any) {
    ElMessage.error('加载知识详情失败: ' + (e.message || e))
  } finally {
    loading.value = false
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
</style>
