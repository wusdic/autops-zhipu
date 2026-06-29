<template>
  <div class="autops-page-container">
    <PageHeader title="AI 助手" desc="通过自然语言对话查询平台信息、分析问题、调度功能执行操作" />

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
import { Plus, ChatLineSquare, Promotion } from '@element-plus/icons-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'
import { sanitizeHtml } from '@/shared/utils/sanitize'

interface Message {
  role: 'user' | 'assistant'
  content: string
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

const STORAGE_KEY = 'autops_ai_conversations'

function persist() {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ conversations: conversations.value, currentConvId: currentConvId.value }),
    )
  } catch { /* 配额或隐私模式下忽略 */ }
}

function restore() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return
    const s = JSON.parse(raw)
    conversations.value = Array.isArray(s.conversations) ? s.conversations : []
    currentConvId.value = s.currentConvId || ''
    const conv = conversations.value.find(c => c.id === currentConvId.value)
    messages.value = conv ? conv.messages : []
  } catch { /* 损坏数据忽略 */ }
}

onMounted(() => {
  username.value = localStorage.getItem('username') || 'admin'
  restore()
  scrollToBottom()
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
  persist()
}

function switchConversation(id: string) {
  const conv = conversations.value.find(c => c.id === id)
  if (conv) {
    currentConvId.value = conv.id
    messages.value = conv.messages
    persist()
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
    // 携带最近多轮历史（不含刚 push 的本条 user 已在 history 末尾），供后端构建上下文
    const history = messages.value
      .slice(0, -1)
      .slice(-10)
      .map((m) => ({ role: m.role, content: m.content }))

    // 本地/推理模型单次回答可达上百秒，全局 30s 超时会让前端提前中断并误显示兜底文案；
    // 此处放宽到 200s（略大于后端 LLM 180s 超时）。
    const resp = await api.post(API.AI.CHAT, {
      message: text,
      history,
    }, { timeout: 200000 })

    if (resp.data?.code === 0 && resp.data?.data) {
      const data = resp.data.data
      // 后端契约返回 data.reply；兼容 content/message 历史字段
      const reply = data.reply || data.content || data.message || '（模型未返回内容）'
      messages.value.push({
        role: 'assistant',
        content: reply,
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
    // AI 服务不可用/超时时如实告知，不再用本地硬编码文案伪装成模型回复
    const isTimeout = err?.code === 'ECONNABORTED' || /timeout/i.test(err?.message || '')
    messages.value.push({
      role: 'assistant',
      content: isTimeout
        ? '⚠️ 模型响应超时。本地/推理模型首次或复杂问题可能较慢；若为 Qwen3 等带"思考"的模型且部署在 CPU 上，建议在「平台管理-模型服务」将该模型的「思考模式」设为关闭后重试。'
        : '⚠️ AI 服务暂时不可用：' + (err?.message || '连接失败') +
          '。请检查「平台管理-模型服务」配置或本地模型是否已启动。',
    })
  } finally {
    loading.value = false
    persist()
    scrollToBottom()
  }
}

function sendQuickQuestion(q: string) {
  inputText.value = q
  sendMessage()
}

function renderMarkdown(text: string): string {
  const html = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
  return sanitizeHtml(html)
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

/* 消息主体占满剩余宽度，气泡按内容自适应（短文不再被压成两行） */
.message-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.message-item.user .message-body {
  align-items: flex-end;
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
  display: inline-block;
  width: fit-content;
  padding: 10px 16px;
  max-width: 70%;
  font-size: var(--autops-font-14);
  line-height: 1.6;
  word-break: break-word;
}

.message-content :deep(strong) {
  font-weight: 600;
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
