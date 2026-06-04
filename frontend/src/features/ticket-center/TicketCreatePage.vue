<template>
  <div class="ticket-create-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">创建工单</span>
          <el-button :icon="Back" @click="handleBack">返回列表</el-button>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
        label-position="right"
        class="ticket-form"
        status-icon
      >
        <!-- 基本信息 -->
        <el-divider content-position="left">基本信息</el-divider>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="工单标题" prop="title">
              <el-input
                v-model="formData.title"
                placeholder="请输入工单标题，简要描述问题"
                maxlength="120"
                show-word-limit
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工单类型" prop="type">
              <el-select
                v-model="formData.type"
                placeholder="请选择工单类型"
                style="width: 100%"
                clearable
              >
                <el-option
                  v-for="item in ticketTypes"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                >
                  <div class="type-option">
                    <el-icon><component :is="item.icon" /></el-icon>
                    <span>{{ item.label }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="优先级" prop="priority">
              <el-select
                v-model="formData.priority"
                placeholder="请选择优先级"
                style="width: 100%"
              >
                <el-option
                  v-for="item in priorityLevels"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                >
                  <div class="priority-option">
                    <el-tag :type="item.tagType" size="small" effect="dark">
                      {{ item.label }}
                    </el-tag>
                    <span class="priority-desc">{{ item.desc }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="负责人" prop="assignee_id">
              <el-select
                v-model="formData.assignee_id"
                placeholder="选择负责人（可选）"
                style="width: 100%"
                filterable
                clearable
                remote
                :remote-method="searchAssignees"
                :loading="assigneeLoading"
              >
                <el-option
                  v-for="user in assigneeOptions"
                  :key="user.id"
                  :label="user.display_name || user.username"
                  :value="user.id"
                >
                  <div class="user-option">
                    <el-avatar :size="24" style="margin-right: 8px">
                      {{ (user.display_name || user.username)?.charAt(0) }}
                    </el-avatar>
                    <span>{{ user.display_name || user.username }}</span>
                    <span v-if="user.role" class="user-role">{{ user.role }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 描述 -->
        <el-divider content-position="left">详细描述</el-divider>

        <el-form-item label="问题描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="6"
            placeholder="请详细描述问题现象、影响范围及期望的处理方式…"
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="附件">
          <el-upload
            v-model:file-list="formData.attachments"
            action="#"
            :auto-upload="false"
            :limit="5"
            :on-exceed="() => ElMessage.warning('最多上传 5 个附件')"
            multiple
          >
            <el-button :icon="Paperclip">添加附件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持图片、文档、日志文件，单文件不超过 20MB，最多 5 个</div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 关联信息 -->
        <el-divider content-position="left">关联信息（可选）</el-divider>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="关联告警" prop="related_alert_id">
              <el-select
                v-model="formData.related_alert_id"
                placeholder="搜索并关联告警"
                style="width: 100%"
                filterable
                clearable
                remote
                :remote-method="searchAlerts"
                :loading="alertLoading"
                value-key="id"
              >
                <el-option
                  v-for="alert in alertOptions"
                  :key="alert.id"
                  :label="'[' + alert.severity + '] ' + alert.name || alert.title"
                  :value="alert.id"
                >
                  <div class="alert-option">
                    <el-tag :type="alertSeverityMap[alert.severity]" size="small">
                      {{ alert.severity }}
                    </el-tag>
                    <span>{{ alert.name || alert.title }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关联资产" prop="related_asset_id">
              <el-select
                v-model="formData.related_asset_id"
                placeholder="搜索并关联资产"
                style="width: 100%"
                filterable
                clearable
                remote
                :remote-method="searchAssets"
                :loading="assetLoading"
                value-key="id"
              >
                <el-option
                  v-for="asset in assetOptions"
                  :key="asset.id"
                  :label="asset.ip + ' - ' + asset.hostname || asset.name"
                  :value="asset.id"
                >
                  <div class="asset-option">
                    <span class="asset-ip">{{ asset.ip }}</span>
                    <span class="asset-name">{{ asset.hostname || asset.name }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 附加信息 -->
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="期望完成时间">
              <el-date-picker
                v-model="formData.expected_resolve_at"
                type="datetime"
                placeholder="选择期望完成时间"
                style="width: 100%"
                :disabled-date="(d: Date) => d < new Date()"
                format="YYYY-MM-DD HH:mm"
                value-format="YYYY-MM-DDTHH:mm:ss"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="通知方式">
              <el-checkbox-group v-model="formData.notify_channels">
                <el-checkbox label="email">邮件</el-checkbox>
                <el-checkbox label="sms">短信</el-checkbox>
                <el-checkbox label="webhook">Webhook</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 提交区域 -->
        <el-divider />
        <el-form-item class="form-actions">
          <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit">
            <el-icon><CircleCheck /></el-icon>
            提交工单
          </el-button>
          <el-button size="large" @click="handleSaveDraft">
            <el-icon><FolderOpened /></el-icon>
            保存草稿
          </el-button>
          <el-button size="large" @click="handleReset">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  Back,
  CircleCheck,
  FolderOpened,
  RefreshLeft,
  Paperclip,
  Warning,
  Monitor,
  Connection,
  Lock,
  Cpu,
  DataAnalysis,
} from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()

// ─── 类型定义 ────────────────────────────────────────
interface AlertItem {
  id: number | string
  name?: string
  title?: string
  severity: string
}

interface AssetItem {
  id: number | string
  ip: string
  hostname?: string
  name?: string
}

interface UserItem {
  id: number | string
  username: string
  display_name?: string
  role?: string
}

interface TicketFormData {
  title: string
  description: string
  type: string
  priority: string
  assignee_id: number | string | undefined
  related_alert_id: number | string | undefined
  related_asset_id: number | string | undefined
  expected_resolve_at: string
  notify_channels: string[]
  attachments: unknown[]
}

// ─── 工单类型配置 ────────────────────────────────────
const ticketTypes = [
  { value: 'incident', label: '事件', icon: shallowRef(Warning) },
  { value: 'problem', label: '问题', icon: shallowRef(DataAnalysis) },
  { value: 'change', label: '变更', icon: shallowRef(Connection) },
  { value: 'request', label: '服务请求', icon: shallowRef(Monitor) },
  { value: 'security', label: '安全事件', icon: shallowRef(Lock) },
  { value: 'maintenance', label: '维护', icon: shallowRef(Cpu) },
]

const priorityLevels = [
  { value: 'critical', label: '紧急', tagType: 'danger', desc: '系统不可用或核心业务中断' },
  { value: 'high', label: '高', tagType: 'warning', desc: '功能严重受损，影响较大' },
  { value: 'medium', label: '中', tagType: '', desc: '功能部分受影响' },
  { value: 'low', label: '低', tagType: 'info', desc: '轻微问题或建议' },
]

const alertSeverityMap: Record<string, string> = {
  critical: 'danger',
  high: 'warning',
  medium: '',
  low: 'info',
  info: 'info',
}

// ─── 表单状态 ────────────────────────────────────────
const formRef = ref<FormInstance>()
const submitting = ref(false)

const formData = reactive<TicketFormData>({
  title: '',
  description: '',
  type: '',
  priority: '',
  assignee_id: undefined,
  related_alert_id: undefined,
  related_asset_id: undefined,
  expected_resolve_at: '',
  notify_channels: ['email'],
  attachments: [],
})

const formRules = reactive<FormRules<TicketFormData>>({
  title: [
    { required: true, message: '请输入工单标题', trigger: 'blur' },
    { min: 4, max: 120, message: '标题长度 4~120 个字符', trigger: 'blur' },
  ],
  type: [{ required: true, message: '请选择工单类型', trigger: 'change' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }],
  description: [
    { required: true, message: '请输入问题描述', trigger: 'blur' },
    { min: 10, message: '描述至少 10 个字符', trigger: 'blur' },
  ],
})

// ─── 下拉选项数据 ────────────────────────────────────
const assigneeLoading = ref(false)
const assigneeOptions = ref<UserItem[]>([])

const alertLoading = ref(false)
const alertOptions = ref<AlertItem[]>([])

const assetLoading = ref(false)
const assetOptions = ref<AssetItem[]>([])

// ─── 搜索方法 ────────────────────────────────────────
async function searchAssignees(query: string) {
  if (!query) return
  assigneeLoading.value = true
  try {
    const res = await client.get(API.USERS ?? '/api/users', { params: { keyword: query, page_size: 20 } })
    const data = res.data?.data ?? res.data
    assigneeOptions.value = Array.isArray(data) ? data : data?.items ?? []
  } catch {
    assigneeOptions.value = []
  } finally {
    assigneeLoading.value = false
  }
}

async function searchAlerts(query: string) {
  if (!query) return
  alertLoading.value = true
  try {
    const res = await client.get(API.ALERTS, { params: { keyword: query, page_size: 20 } })
    const data = res.data?.data ?? res.data
    alertOptions.value = Array.isArray(data) ? data : data?.items ?? data?.results ?? []
  } catch {
    alertOptions.value = []
  } finally {
    alertLoading.value = false
  }
}

async function searchAssets(query: string) {
  if (!query) return
  assetLoading.value = true
  try {
    const res = await client.get(API.ASSETS, { params: { keyword: query, page_size: 20 } })
    const data = res.data?.data ?? res.data
    assetOptions.value = Array.isArray(data) ? data : data?.items ?? data?.results ?? []
  } catch {
    assetOptions.value = []
  } finally {
    assetLoading.value = false
  }
}

// ─── 提交 ────────────────────────────────────────────
async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) {
    ElMessage.warning('请完整填写必填信息')
    return
  }

  submitting.value = true
  try {
    const payload: Record<string, unknown> = {
      title: formData.title,
      description: formData.description,
      type: formData.type,
      priority: formData.priority,
      assignee_id: formData.assignee_id || null,
      related_alert_id: formData.related_alert_id || null,
      related_asset_id: formData.related_asset_id || null,
      expected_resolve_at: formData.expected_resolve_at || null,
      notify_channels: formData.notify_channels,
    }

    const res = await client.post(API.TICKETS, payload)
    const ticketId = res.data?.data?.id ?? res.data?.id

    ElMessage.success('工单创建成功')
    if (ticketId) {
      router.push('/ticket-center/tickets/' + ticketId)
    } else {
      router.push('/ticket-center/tickets')
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '创建工单失败'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}

// ─── 保存草稿 ────────────────────────────────────────
async function handleSaveDraft() {
  try {
    await client.post(API.TICKETS, {
      ...formData,
      status: 'draft',
    })
    ElMessage.success('草稿已保存')
  } catch {
    ElMessage.error('保存草稿失败')
  }
}

// ─── 重置 ────────────────────────────────────────────
async function handleReset() {
  try {
    await ElMessageBox.confirm('确定重置表单内容？所有已填信息将丢失。', '重置确认', {
      type: 'warning',
    })
    formRef.value?.resetFields()
    formData.notify_channels = ['email']
    formData.attachments = []
  } catch {
    // cancelled
  }
}

// ─── 返回 ────────────────────────────────────────────
function handleBack() {
  router.push('/ticket-center/tickets')
}

// ─── 初始化 ──────────────────────────────────────────
onMounted(() => {
  // Pre-load default assignees
  searchAssignees('')
})
</script>

<style scoped>
.ticket-create-page {
  padding: 20px;
}
.card-header .title {
  font-size: 18px;
  font-weight: 600;
}

.ticket-form {
  max-width: 960px;
}

.ticket-form :deep(.el-divider__text) {
  font-weight: 600;
  color: #1d2129;
}

.type-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.priority-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.priority-desc {
  color: #86909c;
  font-size: 12px;
}

.user-option {
  display: flex;
  align-items: center;
}

.user-role {
  margin-left: auto;
  color: #86909c;
  font-size: 12px;
}

.alert-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.asset-option {
  display: flex;
  align-items: center;
  gap: 12px;
}

.asset-ip {
  font-family: monospace;
  color: #4e5969;
}

.asset-name {
  color: #86909c;
}

.form-actions {
  margin-top: 8px;
}

.form-actions :deep(.el-form-item__content) {
  justify-content: flex-start;
  gap: 12px;
}
</style>
