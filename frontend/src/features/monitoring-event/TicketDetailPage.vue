<template>
  <div class="ticket-detail">
    <!-- 顶部导航 -->
    <div class="detail-header">
      <el-button :icon="ArrowLeft" @click="$router.back()">返回</el-button>
      <div class="detail-title-area">
        <h2 style="margin: 0 0 0 12px">{{ ticket?.title || '工单详情' }}</h2>
        <StatusBadge v-if="ticket" :status="ticket.status" show-icon style="margin-left: 12px" />
        <el-tag v-if="ticket" :type="priorityType(ticket?.priority)" style="margin-left: 8px">
          {{ ticket?.priority || '-' }}
        </el-tag>
      </div>
    </div>

    <div v-loading="loading" style="margin-top: 16px">
      <template v-if="ticket">
        <el-tabs v-model="activeTab" type="border-card">
          <!-- 基本信息 -->
          <el-tab-pane label="基本信息" name="info">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="工单ID">{{ ticket.id }}</el-descriptions-item>
              <el-descriptions-item label="工单类型">{{ ticketTypeLabel(ticket.ticket_type) }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <StatusBadge :status="ticket.status" show-icon />
              </el-descriptions-item>
              <el-descriptions-item label="优先级">
                <el-tag :type="priorityType(ticket.priority)">{{ ticket.priority }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="负责人">{{ ticket.assigned_to || '未分配' }}</el-descriptions-item>
              <el-descriptions-item label="创建人">{{ ticket.created_by || '-' }}</el-descriptions-item>
              <el-descriptions-item label="SLA截止">{{ formatTime(ticket.sla_deadline) }}</el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ formatTime(ticket.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="更新时间">{{ formatTime(ticket.updated_at) }}</el-descriptions-item>
              <el-descriptions-item label="解决时间">{{ formatTime(ticket.resolved_at) }}</el-descriptions-item>
              <el-descriptions-item label="描述" :span="2">{{ ticket.description || '-' }}</el-descriptions-item>
            </el-descriptions>

            <!-- 上下文信息 -->
            <div v-if="ticket.context" style="margin-top: 16px">
              <h4>上下文信息</h4>
              <el-input type="textarea" :rows="4" :model-value="formatJson(ticket.context)" readonly />
            </div>

            <!-- 状态操作 -->
            <div style="margin-top: 16px; display: flex; gap: 8px">
              <el-button v-if="ticket.status === 'open'" type="primary" @click="changeStatus('in_progress')">
                开始处理
              </el-button>
              <el-button v-if="ticket.status === 'in_progress'" type="warning" @click="changeStatus('pending')">
                挂起
              </el-button>
              <el-button v-if="ticket.status === 'pending'" type="primary" @click="changeStatus('in_progress')">
                恢复处理
              </el-button>
              <el-button v-if="['open', 'in_progress', 'pending'].includes(ticket.status)" type="success" @click="changeStatus('resolved')">
                标记已解决
              </el-button>
              <el-button v-if="ticket.status === 'resolved'" type="info" @click="changeStatus('closed')">
                关闭工单
              </el-button>
            </div>
          </el-tab-pane>

          <!-- 关联信息 -->
          <el-tab-pane label="关联信息" name="relations">
            <el-row :gutter="16">
              <el-col :span="12">
                <h4>关联告警</h4>
                <el-table :data="relatedAlerts" stripe size="small">
                  <el-table-column prop="title" label="告警" min-width="160" show-overflow-tooltip />
                  <el-table-column label="严重级别" width="100">
                    <template #default="{ row }">
                      <SeverityBadge :severity="row.severity" size="small" />
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="70">
                    <template #default="{ row }">
                      <el-button text type="primary" size="small" @click="$router.push(`/alerts/${row.id}`)">查看</el-button>
                    </template>
                  </el-table-column>
                </el-table>
                <el-empty v-if="!relatedAlerts.length" description="暂无关联告警" :image-size="60" />
              </el-col>
              <el-col :span="12">
                <h4>关联执行</h4>
                <el-table :data="relatedExecutions" stripe size="small">
                  <el-table-column prop="playbook_name" label="Playbook" min-width="160" show-overflow-tooltip />
                  <el-table-column label="状态" width="100">
                    <template #default="{ row }">
                      <StatusBadge :status="row.status" size="small" />
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="70">
                    <template #default="{ row }">
                      <el-button text type="primary" size="small" @click="$router.push(`/executions/${row.id}`)">查看</el-button>
                    </template>
                  </el-table-column>
                </el-table>
                <el-empty v-if="!relatedExecutions.length" description="暂无关联执行" :image-size="60" />
              </el-col>
            </el-row>
          </el-tab-pane>

          <!-- 评论 -->
          <el-tab-pane label="评论" name="comments">
            <div style="margin-bottom: 16px">
              <el-input
                v-model="newComment"
                type="textarea"
                :rows="3"
                placeholder="输入评论内容..."
              />
              <el-button type="primary" style="margin-top: 8px" @click="addComment" :loading="commentSubmitting">
                提交评论
              </el-button>
            </div>
            <el-timeline>
              <el-timeline-item
                v-for="comment in comments"
                :key="comment.id"
                :timestamp="formatTime(comment.created_at)"
                placement="top"
              >
                <el-card shadow="never">
                  <p style="margin: 0">
                    <strong>{{ comment.author || '系统' }}</strong>
                    <span style="color: #999; margin-left: 8px">{{ comment.content }}</span>
                  </p>
                </el-card>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-if="!comments.length" description="暂无评论" />
          </el-tab-pane>

          <!-- 知识沉淀 -->
          <el-tab-pane label="知识沉淀" name="knowledge">
            <el-empty v-if="ticket.status !== 'closed'" description="工单关闭后可生成知识草稿">
              <el-button type="primary" @click="generateKnowledgeDraft" :disabled="ticket.status !== 'resolved' && ticket.status !== 'closed'">
                生成知识草稿
              </el-button>
            </el-empty>
            <div v-else>
              <p>工单关闭后可将处置经验沉淀为知识库文章。</p>
              <el-button type="primary" @click="generateKnowledgeDraft">生成知识草稿</el-button>
            </div>
          </el-tab-pane>
        </el-tabs>
      </template>

      <el-empty v-if="!loading && !ticket" description="工单不存在或已被删除">
        <el-button type="primary" @click="$router.back()">返回列表</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import SeverityBadge from '@/shared/components/SeverityBadge.vue'

const route = useRoute()
const ticketId = () => route.params.id as string

const loading = ref(false)
const ticket = ref<any>(null)
const activeTab = ref('info')
const comments = ref<any[]>([])
const newComment = ref('')
const commentSubmitting = ref(false)
const relatedAlerts = ref<any[]>([])
const relatedExecutions = ref<any[]>([])

async function loadTicket() {
  const id = ticketId()
  if (!id) return
  loading.value = true
  try {
    const { data } = await api.get(R.TICKET_DETAIL(id))
    if (data.code === 0) {
      ticket.value = data.data
      loadComments()
      loadRelations()
    }
  } catch {
    ElMessage.error('加载工单详情失败')
  } finally {
    loading.value = false
  }
}

async function loadComments() {
  try {
    const { data } = await api.get(R.TICKET_COMMENTS(ticketId()))
    if (data.code === 0) {
      comments.value = Array.isArray(data.data) ? data.data : data.data?.items || []
    }
  } catch {
    comments.value = []
  }
}

async function loadRelations() {
  const t = ticket.value
  if (!t) return
  // 关联告警
  const alertIds: string[] = t.alert_ids || []
  if (alertIds.length) {
    try {
      const results = await Promise.all(
        alertIds.map(id => api.get(R.ALERT_DETAIL(id)).then(r => r.data).catch(() => null))
      )
      relatedAlerts.value = results.filter(r => r && r.code === 0).map((r: any) => r.data)
    } catch { relatedAlerts.value = [] }
  }
  // 关联执行
  const execIds: string[] = t.execution_ids || []
  if (execIds.length) {
    try {
      const results = await Promise.all(
        execIds.map(id => api.get(R.EXECUTION_DETAIL(id)).then(r => r.data).catch(() => null))
      )
      relatedExecutions.value = results.filter(r => r && r.code === 0).map((r: any) => r.data)
    } catch { relatedExecutions.value = [] }
  }
}

async function addComment() {
  if (!newComment.value.trim()) return
  commentSubmitting.value = true
  try {
    const { data } = await api.post(R.TICKET_COMMENTS(ticketId()), { content: newComment.value })
    if (data.code === 0) {
      ElMessage.success('评论已提交')
      newComment.value = ''
      loadComments()
    }
  } catch {
    ElMessage.error('提交评论失败')
  } finally {
    commentSubmitting.value = false
  }
}

async function changeStatus(status: string) {
  try {
    const { data } = await api.put(R.TICKET_DETAIL(ticketId()), { status })
    if (data.code === 0) {
      ElMessage.success('状态已更新')
      loadTicket()
    }
  } catch {
    ElMessage.error('状态更新失败')
  }
}

async function generateKnowledgeDraft() {
  ElMessage.info('正在生成知识草稿...')
  // Use knowledge create API with ticket context
  try {
    const t = ticket.value
    const { data } = await api.post(R.KNOWLEDGE, {
      title: `[工单]${t?.title || ''}处置经验`,
      content: `## 问题\n${t?.description || ''}\n\n## 处理过程\n（待补充）\n\n## 解决方案\n（待补充）`,
      category: 'troubleshooting',
      status: 'draft',
      source: 'ticket',
      tags: [t?.ticket_type || 'incident'],
    })
    if (data.code === 0) {
      ElMessage.success('知识草稿已生成')
    }
  } catch {
    ElMessage.error('生成知识草稿失败')
  }
}

function formatTime(t: string) {
  return t ? new Date(t).toLocaleString('zh-CN') : '-'
}

function formatJson(obj: any) {
  try { return JSON.stringify(obj, null, 2) } catch { return String(obj) }
}

function priorityType(p: string) {
  const map: Record<string, string> = { critical: 'danger', high: 'warning', medium: '', low: 'info', low: 'success' }
  return map[p] || ''
}

function ticketTypeLabel(t: string) {
  const map: Record<string, string> = { incident: '事件', problem: '问题', change: '变更', task: '任务' }
  return map[t] || t
}

onMounted(() => loadTicket())
watch(() => route.params.id, () => { if (route.params.id) loadTicket() })
</script>

<style scoped>
.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
}
.detail-title-area {
  display: flex;
  align-items: center;
  flex: 1;
}
</style>
