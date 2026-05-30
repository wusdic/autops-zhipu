<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>知识库</span>
          <el-input v-model="searchText" placeholder="搜索知识..." style="width:300px" @input="loadArticles" clearable />
        </div>
      </template>

      <el-table :data="articles" v-loading="loading" stripe>
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="article_type" label="类型" width="130">
          <template #default="{ row }">
            <el-tag size="small">{{ typeLabel(row.article_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险" width="80">
          <template #default="{ row }">
            <el-tag :type="row.risk_level==='high'?'danger':row.risk_level==='medium'?'warning':'info'" size="small">
              {{ row.risk_level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status==='published'?'success':'info'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="60" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewArticle(row)">查看</el-button>
            <el-button v-if="row.status==='draft'" size="small" type="success"
              @click="publishArticle(row.id)">发布</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination v-model:current-page="page" :page-size="20" :total="total"
        layout="total, prev, pager, next" @change="loadArticles" style="margin-top:16px;justify-content:flex-end" />
    </el-card>

    <el-drawer v-model="showDetail" :title="current?.title" size="600px">
      <template v-if="current">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="类型">{{ typeLabel(current.article_type) }}</el-descriptions-item>
          <el-descriptions-item label="风险等级">{{ current.risk_level }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ current.status }}</el-descriptions-item>
          <el-descriptions-item label="版本">v{{ current.version }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="current.content" v-html="renderMarkdown(current.content)" class="markdown-body" style="margin-top:20px" />
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/shared/api/client'

const loading = ref(false)
const articles = ref<any[]>([])
const showDetail = ref(false)
const current = ref<any>(null)
const searchText = ref('')
const page = ref(1)
const total = ref(0)
const API = '/api/v1/knowledge'

function typeLabel(t: string) {
  const m: Record<string, string> = { standard_solution: '标准方案', incident_summary: '事件总结', best_practice: '最佳实践', draft: '草稿' }
  return m[t] || t
}

function renderMarkdown(text: string) {
  // Simple markdown rendering - replace ## with h2, ** with bold, etc.
  return text
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br/>')
}

async function loadArticles() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: 20, status: 'published' }
    const { data } = await api.get(API, { params })
    if (data.code === 0) { articles.value = data.data.items || []; total.value = data.data.total || 0 }
  } finally { loading.value = false }
}

function viewArticle(row: any) { current.value = row; showDetail.value = true }

async function publishArticle(id: string) {
  const { data } = await api.post(`${API}/${id}/publish`)
  if (data.code === 0) { ElMessage.success('发布成功'); loadArticles() }
}

onMounted(() => loadArticles())
</script>

<style scoped>
.markdown-body { line-height: 1.8; }
.markdown-body h2 { margin: 16px 0 8px; color: #303133; }
.markdown-body h3 { margin: 12px 0 6px; color: #606266; }
.markdown-body code { background: #f5f7fa; padding: 2px 6px; border-radius: 3px; }
</style>
