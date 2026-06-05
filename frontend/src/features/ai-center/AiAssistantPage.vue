<template>
  <div class="autops-page-container">
    <div class="autops-page-header">
      <div class="autops-page-title">AI 助手</div>
      <div class="autops-page-desc">通过自然语言对话查询平台信息、分析问题、调度功能执行操作</div>
    </div>

    <div class="chat-container">
      <!-- 左侧：对话历史 -->
      <div class="chat-sidebar">
        <div class="sidebar-header">
          <el-button type="primary" size="small" style="width: 100%" @click="newConversation">
            <el-icon><Plus /></el-icon> 新建对话
          </el-button>
        </div>
        <div class="conversation-list">
          <div
            v-for="conv in conversations"
            :key="conv.id"
            class="conversation-item"
            :class="{ active: currentConvId === conv.id }"
            @click="switchConversation(conv.id)"
          >
            <el-icon size="14"><ChatLineSquare /></el-icon>
            <span class="conv-title">{{ conv.title }}</span>
          </div>
          <div v-if="conversations.length === 0" class="autops-empty" style="padding: 24px">
            <span class="autops-empty-text">暂无对话记录</span>
          </div>
        </div>
      </div>

      <!-- 右侧：对话区 -->
      <div class="chat-main">
        <!-- 消息列表 -->
        <div ref="messageListRef" class="message-list">
          <div v-if="messages.length === 0" class="welcome-area">
            <el-icon size="48" color="#165dff"><ChatLineSquare /></el-icon>
            <h3>AUTOPS AI 助手</h3>
            <p>我可以帮你查询平台信息、分析告警、调度操作。试试问我：</p>
            <div class="quick-actions">
              <el-button v-for="q in quickQuestions" :key="q" size="small" round @click="sendQuickQuestion(q)">{{ q }}</el-button>
            </div>
          </div>
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            class="message-item"
            :class="msg.role"
          >
            <div class="message-avatar">
              <el-avatar v-if="msg.role === 'user'" :size="32" style="background: #165dff">{{ (username || 'U').charAt(0) }}</el-avatar>
              <el-avatar v-else :size="32" style="background: #00b42a">AI</el-avatar>
            </div>
            <div class="message-body">
              <div class="message-content" v-html="renderMarkdown(msg.content)"></div>
              <div v-if="msg.actions && msg.actions.length" class="message-actions">
                <el-button
                  v-for="act in msg.actions"
                  :key="act.label"
                  :type="act.danger ? 'danger' : 'primary'"
                  size="small"
                  @click="executeAction(act)"
                >{{ act.label }}</el-button>
              </div>
            </div>
          </div>
          <div v-if="loading" class="message-item assistant">
            <div class="message-avatar">
              <el-avatar :size="32" style="background: #00b42a">AI</el-avatar>
            </div>
            <div class="message-body">
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区 -->
        <div class="chat-input-area">
          <el-input
            ref="inputRef"
            v-model="inputText"
            type="textarea"
            :rows="2"
            placeholder="输入问题或指令，Enter 发送，Shift+Enter 换行"
            resize="none"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <el-button
            type="primary"
            :icon="Promotion"
            :loading="loading"
            :disabled="!inputText.trim()"
            @click="sendMessage"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ChatLineSquare, Promotion } from '@element-plus/icons-vue'
import api from '@/shared/api/client'

interface MessageAction {
  label: string
  type: string
  params: Record<string, any>
  danger?: boolean
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  actions?: MessageAction[]
}

interface Conversation {
  id: string
  title: string
  messages: Message[]
}

const username = ref('')
const inputText = ref('')
const loading = ref(false)
const messages = ref<Message[]>([])
const currentConvId = ref('')
const conversations = ref<Conversation[]>([])
const messageListRef = ref<HTMLElement>()
const inputRef = ref()

const quickQuestions = [
  '当前有多少活跃告警？',
  '帮我查看资源总体状态',
  '最近24小时有什么异常？',
  '平台各模块健康情况如何？',
]

onMounted(() => {
  username.value = localStorage.getItem('username') || 'admin'
})

function newConversation() {
  const conv: Conversation = {
    id: Date.now().toString(),
    title: '新对话 ' + (conversations.value.length + 1),
    messages: [],
  }
  conversations.value.unshift(conv)
  currentConvId.value = conv.id
  messages.value = conv.messages
}

function switchConversation(id: string) {
  const conv = conversations.value.find(c => c.id === id)
  if (conv) {
    currentConvId.value = conv.id
    messages.value = conv.messages
    scrollToBottom()
  }
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  if (!currentConvId.value) newConversation()

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const resp = await api.post('/api/v1/ai/chat', {
      message: text,
      conversation_id: currentConvId.value,
    })

    if (resp.data?.code === 0 && resp.data?.data) {
      const data = resp.data.data
      messages.value.push({
        role: 'assistant',
        content: data.content || data.message || '处理完成',
        actions: data.actions || [],
      })
      // Update conversation title from first exchange
      if (messages.value.length === 2) {
        const conv = conversations.value.find(c => c.id === currentConvId.value)
        if (conv) conv.title = text.length > 20 ? text.substring(0, 20) + '...' : text
      }
    } else {
      messages.value.push({
        role: 'assistant',
        content: resp.data?.message || '抱歉，处理请求时出现了问题。',
      })
    }
  } catch (err: any) {
    // Fallback: local intelligent response
    messages.value.push({
      role: 'assistant',
      content: generateLocalResponse(text),
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function generateLocalResponse(text: string): string {
  const lower = text.toLowerCase()
  if (lower.includes('告警') || lower.includes('alert')) {
    return '正在为您查询告警信息。您可以前往 **监控告警** 模块查看实时告警列表，或告诉我具体的告警ID进行详细分析。\n\n快捷操作：点击上方 **告警列表** 查看所有活跃告警。'
  }
  if (lower.includes('资源') || lower.includes('asset')) {
    return '正在为您查询资源状态。您可以前往 **资源中心** 查看所有资源的实时状态。\n\n我也可以帮您：\n- 查询特定资源的详细信息\n- 查看资源拓扑关系\n- 检查资源健康状态'
  }
  if (lower.includes('巡检') || lower.includes('inspection')) {
    return '正在为您查询巡检情况。您可以前往 **巡检中心** 查看巡检计划执行状态和结果。\n\n需要我帮您：\n- 查看最近的巡检结果\n- 创建新的巡检任务\n- 查看巡检报告'
  }
  return '收到您的请求。我正在持续学习中，目前可以帮您：\n\n1. **查询信息**：告警、资源、巡检、执行状态\n2. **分析问题**：根因分析、影响范围评估\n3. **调度操作**：执行策略、创建工单\n\n请告诉我您需要什么帮助？'
}

function sendQuickQuestion(q: string) {
  inputText.value = q
  sendMessage()
}

async function executeAction(action: MessageAction) {
  if (action.danger) {
    try {
      await ElMessageBox.confirm(
        '此操作可能影响系统运行，确认执行？',
        '操作确认',
        { confirmButtonText: '确认执行', cancelButtonText: '取消', type: 'warning' }
      )
    } catch { return }
  }

  try {
    const resp = await api.post('/api/v1/ai/execute', {
      action_type: action.type,
      params: action.params,
    })
    if (resp.data?.code === 0) {
      ElMessage.success('操作执行成功')
      messages.value.push({
        role: 'assistant',
        content: '操作已成功执行：' + (resp.data.data?.message || '完成'),
      })
    } else {
      ElMessage.error(resp.data?.message || '操作执行失败')
    }
  } catch {
    ElMessage.error('操作执行失败，请稍后重试')
  }
  scrollToBottom()
}

function renderMarkdown(text: string): string {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}

function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.ai-assistant-page {
  height: calc(100vh - 56px - 40px);
  display: flex;
  flex-direction: column;
}

.chat-container {
  flex: 1;
  display: flex;
  background: var(--autops-bg-1);
  border-radius: var(--autops-radius-md);
  border: 1px solid var(--autops-bg-4);
  overflow: hidden;
  min-height: 0;
}

.chat-sidebar {
  width: 240px;
  border-right: 1px solid var(--autops-bg-4);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  padding: var(--autops-space-md);
  border-bottom: 1px solid var(--autops-bg-4);
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--autops-space-sm);
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--autops-radius-sm);
  cursor: pointer;
  transition: background 0.15s;
  color: var(--autops-text-2);
  font-size: var(--autops-font-13);
}

.conversation-item:hover {
  background: var(--autops-bg-3);
}

.conversation-item.active {
  background: var(--autops-primary-light-5);
  color: var(--autops-primary);
}

.conv-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--autops-space-xl) 24px;
}

.welcome-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  color: var(--autops-text-2);
}

.welcome-area h3 {
  font-size: var(--autops-font-20);
  color: var(--autops-text-1);
  margin: 8px 0 0;
}

.welcome-area p {
  font-size: var(--autops-font-14);
  color: var(--autops-text-3);
  margin: 0;
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 8px;
  max-width: 500px;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: var(--autops-space-xl);
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-item.user .message-content {
  background: var(--autops-primary);
  color: var(--autops-bg-1);
  border-radius: var(--autops-radius-lg) 12px 2px 12px;
}

.message-item.assistant .message-content {
  background: var(--autops-bg-3);
  color: var(--autops-text-1);
  border-radius: var(--autops-radius-lg) 12px 12px 2px;
}

.message-content {
  padding: 10px 16px;
  max-width: 70%;
  font-size: var(--autops-font-14);
  line-height: 1.6;
  word-break: break-word;
}

.message-content :deep(strong) {
  font-weight: 600;
}

.message-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 14px 16px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--autops-text-4);
  border-radius: 50%;
  animation: typing 1.2s infinite;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
  30% { opacity: 1; transform: scale(1); }
}

.chat-input-area {
  display: flex;
  gap: 8px;
  padding: var(--autops-space-lg) 24px;
  border-top: 1px solid var(--autops-bg-4);
  align-items: flex-end;
}

.chat-input-area .el-textarea {
  flex: 1;
}
</style>
