<template>
  <div class="autops-page-container">
    <!-- ─── Page Header ─── -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">工单详情</div>
        <div class="autops-page-desc">查看工单信息、关联告警、处理历史与 SLA 跟踪</div>
      </div>
    </div>

    <!-- 顶部导航 -->
    <div class="autops-card">
      <div class="autops-card-body">
        <div class="detail-header">
      <el-button :icon="ArrowLeft" @click="$router.back()">返回</el-button>
      <div class="detail-title-area">
        <h2 style="margin: 0 0 0 12px">{{ ticket?.title || '工单详情' }}</h2>
        <StatusBadge v-if="ticket" :status="ticket.status" show-icon style="margin-left: 12px" />
        <el-tag v-if="ticket" :type="(priorityType(ticket?.priority)) as TagType" style="margin-left: 8px">
          {{ ticket?.priority || '-' }}
        </el-tag>
        <!-- SLA 倒计时 -->
        <span v-if="ticket?.sla_deadline" style="margin-left: 8px">
          <el-tag v-if="slaOverdue" type="danger" effect="dark">
            <el-icon><WarningFilled /></el-icon>
            已超时 {{ slaRemainingText }}
          </el-tag>
          <el-tag v-else type="warning">
            SLA剩余: {{ slaRemainingText }}
          </el-tag>
        </span>
      </div>
        </div>
      </div>
    </div>

    <div v-loading="loading" class="mt-lg">
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
                <el-tag :type="(priorityType(ticket.priority)) as TagType">{{ ticket.priority }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="负责人">
                <span>{{ ticket.assigned_to || '未分配' }}</span>
                <el-button plain type="primary" size="small" style="margin-left: 8px" @click="openAssignDialog">
                  指派
                </el-button>
              </el-descriptions-item>
              <el-descriptions-item label="创建人">{{ ticket.created_by || '-' }}</el-descriptions-item>
              <el-descriptions-item label="SLA截止">{{ formatTime(ticket.sla_deadline) }}</el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ formatTime(ticket.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="更新时间">{{ formatTime(ticket.updated_at) }}</el-descriptions-item>
              <el-descriptions-item label="解决时间">{{ formatTime(ticket.resolved_at) }}</el-descriptions-item>
              <el-descriptions-item label="描述" :span="2">{{ ticket.description || '-' }}</el-descriptions-item>
            </el-descriptions>

            <!-- 上下文信息 -->
            <div v-if="ticket.context" class="mt-lg">
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
              <!-- 工作流导航 -->
              <el-button type="success" @click="navToReportFromTicket(ticketId())">
                生成报告
              </el-button>
              <el-button type="warning" @click="navToKnowledgeFromTicket(ticketId())">
                转为知识
              </el-button>
              <!-- 转知识草稿按钮 -->
              <el-button
                v-if="ticket.status === 'resolved' || ticket.status === 'closed'"
                type="warning"
                :icon="Document"
                :loading="knowledgeConverting"
                @click="convertToKnowledge"
              >
                转知识草稿
              </el-button>
            </div>
          </el-tab-pane>

          <!-- 关联信息 -->
          <el-tab-pane label="关联信息" name="relations">
            <el-row :gutter="16">
              <el-col :span="12">
                <h4>关联告警</h4>
                <el-table stripe :data="relatedAlerts"size="small">
                  <el-table-column prop="title" label="告警" min-width="160" show-overflow-tooltip />
                  <el-table-column label="严重级别" width="100">
                    <template #default="{ row }">
                      <SeverityBadge :severity="row.severity" size="small" />
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="100">
                    <template #default="{ row }">
                      <el-button plain type="primary" size="small" @click="$router.push('/alerts/' + row.id)">查看</el-button>
                    </template>
                  </el-table-column>
                </el-table>
                <el-empty v-if="!relatedAlerts.length" description="暂无关联告警" :image-size="60" />
              </el-col>
              <el-col :span="12">
                <h4>关联执行</h4>
                <el-table stripe :data="relatedExecutions"size="small">
                  <el-table-column prop="playbook_name" label="Playbook" min-width="160" show-overflow-tooltip />
                  <el-table-column label="状态" width="100">
                    <template #default="{ row }">
                      <StatusBadge :status="row.status" size="small" />
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="100">
                    <template #default="{ row }">
                      <el-button plain type="primary" size="small" @click="$router.push('/executions/' + row.id)">查看</el-button>
                    </template>
                  </el-table-column>
                </el-table>
                <el-empty v-if="!relatedExecutions.length" description="暂无关联执行" :image-size="60" />
              </el-col>
            </el-row>
          </el-tab-pane>

          <!-- 评论 -->
          <el-tab-pane label="评论" name="comments">
            <div class="mb-lg">
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
                <div class="autops-card">
                  <div class="autops-card-body">
                    <p style="margin: 0">
                      <strong>{{ comment.author || '系统' }}</strong>
                      <span style="color: #999; margin-left: 8px">{{ comment.content }}</span>
                    </p>
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-if="!comments.length" description="暂无评论" />
          </el-tab-pane>

          <!-- 附件 -->
          <el-tab-pane label="附件" name="attachments">
            <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center">
              <h4 style="margin: 0">附件列表</h4>
              <el-upload
                :action="uploadUrl"
                :headers="uploadHeaders"
                :on-success="onUploadSuccess"
                :on-error="onUploadError"
                :show-file-list="false"
                multiple
              >
                <el-button type="primary" :icon="Upload">上传附件</el-button>
              </el-upload>
            </div>
            <el-table stripe :data="attachments"v-loading="attachmentsLoading">
              <el-table-column prop="filename" label="文件名" min-width="200" show-overflow-tooltip />
              <el-table-column label="大小" width="120">
                <template #default="{ row }">{{ formatFileSize(row.size) }}</template>
              </el-table-column>
              <el-table-column prop="uploaded_by" label="上传人" width="120" />
              <el-table-column label="上传时间" width="180">
                <template #default="{ row }">{{ formatTime(row.uploaded_at) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="180" fixed="right">
                <template #default="{ row }">
                  <el-button plain type="primary" size="small" @click="downloadAttachment(row)">下载</el-button>
                  <el-popconfirm title="确认删除此附件？" @confirm="deleteAttachment(row.id)">
                    <template #reference>
                      <el-button plain type="danger" size="small">删除</el-button>
                    </template>
                  </el-popconfirm>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!attachmentsLoading && !attachments.length" description="暂无附件" />
          </el-tab-pane>

          <!-- 知识沉淀 -->
          <el-tab-pane label="知识沉淀" name="knowledge">
            <el-empty v-if="ticket.status !== 'closed' && ticket.status !== 'resolved'" description="工单解决/关闭后可生成知识草稿">
              <el-button type="primary" @click="openKnowledgeDialog" disabled>
                生成知识草稿
              </el-button>
            </el-empty>
            <div v-else>
              <p>工单解决/关闭后可将处置经验沉淀为知识库文章。</p>
              <el-button type="primary" @click="openKnowledgeDialog">生成知识草稿</el-button>
            </div>
          </el-tab-pane>
        </el-tabs>
      </template>

      <el-empty v-if="!loading && !ticket" description="工单不存在或已被删除">
        <el-button type="primary" @click="$router.back()">返回列表</el-button>
      </el-empty>
    </div>

    <!-- 转知识草稿对话框 -->
    <el-dialog v-model="knowledgeDialogVisible" title="转知识草稿" width="600px" destroy-on-close>
      <el-form :model="knowledgeForm" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="knowledgeForm.title" placeholder="知识文章标题" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="knowledgeForm.type" style="width: 100%">
            <el-option label="事件" value="incident" />
            <el-option label="故障排查" value="troubleshooting" />
            <el-option label="变更" value="change" />
            <el-option label="最佳实践" value="best_practice" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="knowledgeForm.content" type="textarea" :rows="12" placeholder="知识文章内容（支持Markdown）" />
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="knowledgeForm.tags" multiple allow-create filterable style="width: 100%" placeholder="添加标签">
            <el-option label="incident" value="incident" />
            <el-option label="ops" value="ops" />
            <el-option label="automation" value="automation" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="knowledgeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveKnowledgeDraft" :loading="knowledgeSubmitting">保存为草稿</el-button>
      </template>
    </el-dialog>

    <!-- 指派对话框 -->
    <el-dialog v-model="assignDialogVisible" title="指派工单" width="480px" destroy-on-close>
      <el-form label-width="80px">
        <el-form-item label="当前指派">
          <span>{{ ticket?.assigned_to || '未分配' }}</span>
        </el-form-item>
        <el-form-item label="选择用户">
          <el-select
            v-model="selectedAssignee"
            filterable
            remote
            reserve-keyword
            placeholder="搜索用户"
            :remote-method="searchUsers"
            :loading="usersLoading"
            style="width: 100%"
          >
            <el-option
              v-for="user in userOptions"
              :key="user.id"
              :label="user.display_name || user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="assignTicket" :loading="assignSubmitting" :disabled="!selectedAssignee">
          确认指派
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import type { TagType } from '@/shared/types'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, WarningFilled, Document, Upload } from '@element-plus/icons-vue'
import { APP_CONFIG } from '@/shared/config'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import { priorityTag } from '@/shared/utils/labels'
import SeverityBadge from '@/shared/components/SeverityBadge.vue'
import { useWorkflowNav } from '@/shared/composables/useWorkflowNav'

const route = useRoute()
const ticketId = () => route.params.id as string

const { navToReportFromTicket, navToKnowledgeFromTicket } = useWorkflowNav()

const loading = ref(false)
const ticket = ref<any>(null)
const activeTab = ref('info')
const comments = ref<any[]>([])
const newComment = ref('')
const commentSubmitting = ref(false)
const relatedAlerts = ref<any[]>([])
const relatedExecutions = ref<any[]>([])

// ─── SLA 倒计时 ───
const now = ref(Date.now())
let slaTimer: ReturnType<typeof setInterval> | null = null

const slaOverdue = computed(() => {
  if (!ticket.value?.sla_deadline) return false
  return new Date(ticket.value.sla_deadline).getTime() < now.value
})

const slaRemainingText = computed(() => {
  if (!ticket.value?.sla_deadline) return ''
  const diff = new Date(ticket.value.sla_deadline).getTime() - now.value
  const absDiff = Math.abs(diff)
  const hours = Math.floor(absDiff / 3600000)
  const minutes = Math.floor((absDiff % 3600000) / 60000)
  const seconds = Math.floor((absDiff % 60000) / 1000)
  if (hours > 24) {
    const days = Math.floor(hours / 24)
    const remainHours = hours % 24
    return days + '天' + remainHours + '时' + minutes + '分'
  }
  return hours + '时' + minutes + '分' + seconds + '秒'
})

function startSlaTimer() {
  if (slaTimer) clearInterval(slaTimer)
  slaTimer = setInterval(() => { now.value = Date.now() }, 1000)
}

// ─── 转知识草稿 ───
const knowledgeConverting = ref(false)
const knowledgeDialogVisible = ref(false)
const knowledgeSubmitting = ref(false)
const knowledgeForm = ref({
  title: '',
  content: '',
  type: 'incident' as string,
  tags: [] as string[],
})

async function convertToKnowledge() {
  const t = ticket.value
  if (!t) return
  try {
    await ElMessageBox.confirm(
      '确认将此工单转为知识草稿？系统将自动生成知识文章草稿。',
      '转知识草稿',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return // 用户取消
  }
  knowledgeConverting.value = true
  try {
    const { data } = await api.post(R.TICKET_CONVERT_KNOWLEDGE(t.id))
    if (data.code === 0) {
      ElMessage.success('已成功转为知识草稿')
    } else {
      ElMessage.error(data.message || '转换失败')
    }
  } catch {
    ElMessage.error('转知识草稿失败')
  } finally {
    knowledgeConverting.value = false
  }
}

function openKnowledgeDialog() {
  const t = ticket.value
  if (!t) return
  knowledgeForm.value = {
    title: '[工单] ' + (t.title || '') + ' 处置经验',
    content: buildKnowledgeContent(t),
    type: 'incident',
    tags: [t.ticket_type || 'incident'],
  }
  knowledgeDialogVisible.value = true
}

function buildKnowledgeContent(t: any): string {
  let content = `## 问题描述\n${t.description || '（无描述）'}\n\n`
  content += `## 工单信息\n- 工单ID: ${t.id}\n- 类型: ${t.ticket_type || '-'}\n- 优先级: ${t.priority || '-'}\n`
  if (t.context) {
    content += '\n## 上下文信息\n```\n' + formatJson(t.context) + '\n```\n'
  }
  content += `\n## 处理过程\n（请补充处理步骤）\n\n## 解决方案\n（请补充解决方案）\n\n## 经验总结\n（请补充经验总结）`
  return content
}

async function saveKnowledgeDraft() {
  if (!knowledgeForm.value.title.trim()) {
    ElMessage.warning('请填写标题')
    return
  }
  knowledgeSubmitting.value = true
  try {
    const { data } = await api.post(R.KNOWLEDGE, {
      title: knowledgeForm.value.title,
      content: knowledgeForm.value.content,
      category: knowledgeForm.value.type,
      status: 'draft',
      source: 'ticket',
      source_id: ticket.value?.id,
      tags: knowledgeForm.value.tags,
    })
    if (data.code === 0) {
      ElMessage.success('知识草稿已保存')
      knowledgeDialogVisible.value = false
    } else {
      ElMessage.error(data.message || '保存失败')
    }
  } catch {
    ElMessage.error('保存知识草稿失败')
  } finally {
    knowledgeSubmitting.value = false
  }
}

// ─── 指派/重新指派 ───
const assignDialogVisible = ref(false)
const selectedAssignee = ref('')
const userOptions = ref<any[]>([])
const usersLoading = ref(false)
const assignSubmitting = ref(false)

function openAssignDialog() {
  selectedAssignee.value = ticket.value?.assigned_to_id || ''
  assignDialogVisible.value = true
  // load initial users
  searchUsers('')
}

async function searchUsers(query: string) {
  usersLoading.value = true
  try {
    const params: Record<string, string> = {}
    if (query) params.keyword = query
    const { data } = await api.get(R.GOVERNANCE.USERS, { params })
    if (data.code === 0) {
      const list = Array.isArray(data.data) ? data.data : data.data?.items || []
      userOptions.value = list
    }
  } catch {
    userOptions.value = []
  } finally {
    usersLoading.value = false
  }
}

async function assignTicket() {
  if (!selectedAssignee.value) return
  assignSubmitting.value = true
  try {
    const { data } = await api.patch(R.TICKET_DETAIL(ticketId()), {
      assigned_to: selectedAssignee.value,
    })
    if (data.code === 0) {
      ElMessage.success('指派成功')
      assignDialogVisible.value = false
      loadTicket()
    } else {
      ElMessage.error(data.message || '指派失败')
    }
  } catch {
    ElMessage.error('指派操作失败')
  } finally {
    assignSubmitting.value = false
  }
}

// ─── 附件管理 ───
const attachments = ref<any[]>([])
const attachmentsLoading = ref(false)

const uploadUrl = computed(() => R.TICKET_ATTACHMENTS(ticketId()))
const uploadHeaders = computed(() => {
  const token = localStorage.getItem(APP_CONFIG.TOKEN_KEY) || ''
  return token ? { Authorization: 'Bearer ' + token } : {}
})

async function loadAttachments() {
  attachmentsLoading.value = true
  try {
    const { data } = await api.get(R.TICKET_ATTACHMENTS(ticketId()))
    if (data.code === 0) {
      attachments.value = Array.isArray(data.data) ? data.data : data.data?.items || []
    }
  } catch {
    attachments.value = []
  } finally {
    attachmentsLoading.value = false
  }
}

function onUploadSuccess(response: any) {
  if (response.code === 0) {
    ElMessage.success('上传成功')
    loadAttachments()
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

function onUploadError() {
  ElMessage.error('上传失败')
}

async function downloadAttachment(row: any) {
  try {
    const url = R.TICKET_ATTACHMENT(ticketId(), row.id)
    const response = await api.get(url, { responseType: 'blob' })
    const blob = new Blob([response.data])
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = row.filename
    link.click()
    URL.revokeObjectURL(link.href)
  } catch {
    ElMessage.error('下载失败')
  }
}

async function deleteAttachment(attachmentId: string) {
  try {
    const { data } = await api.delete(R.TICKET_ATTACHMENT(ticketId(), attachmentId))
    if (data.code === 0) {
      ElMessage.success('已删除')
      loadAttachments()
    } else {
      ElMessage.error(data.message || '删除失败')
    }
  } catch {
    ElMessage.error('删除失败')
  }
}

function formatFileSize(bytes: number): string {
  if (!bytes || bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + units[i]
}

// ─── 原有功能 ───

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
      loadAttachments()
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

function formatTime(t: string) {
  return t ? new Date(t).toLocaleString('zh-CN') : '-'
}

function formatJson(obj: any) {
  try { return JSON.stringify(obj, null, 2) } catch { return String(obj) }
}

// 优先级统一取自 labels.ts
const priorityType = (p: string): TagType => priorityTag(p) as TagType

function ticketTypeLabel(t: string) {
  const map: Record<string, string> = { incident: '事件', problem: '问题', change: '变更', task: '任务' }
  return map[t] || t
}

onMounted(() => {
  loadTicket()
  startSlaTimer()
})
onUnmounted(() => {
  if (slaTimer) clearInterval(slaTimer)
})
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
