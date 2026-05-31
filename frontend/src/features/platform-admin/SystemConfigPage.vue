<template>
  <div class="page-container">
    <!-- ── System Info Panel ─────────────────────────────── -->
    <div class="system-info-panel" v-loading="infoLoading">
      <div class="info-item" v-for="item in systemInfo" :key="item.label">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value" :class="item.class || ''">
          <el-icon v-if="item.icon" :size="14"><component :is="item.icon" /></el-icon>
          {{ item.value }}
        </span>
      </div>
    </div>

    <!-- ── Page Header ───────────────────────────────────── -->
    <div class="page-header">
      <h2>系统配置</h2>
      <div class="header-actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索配置 Key …"
          clearable
          style="width: 240px"
          :prefix-icon="Search"
          @clear="onSearchClear"
        />
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          新增配置
        </el-button>
        <el-button @click="loadConfigs" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- ── Group Tabs ────────────────────────────────────── -->
    <el-tabs v-model="activeGroup" class="config-tabs" @tab-change="onGroupChange">
      <el-tab-pane v-for="g in configGroups" :key="g.value" :label="g.label" :name="g.value">
        <template #label>
          <span class="tab-label">
            <el-icon :size="14"><component :is="g.icon" /></el-icon>
            {{ g.label }}
            <el-badge
              v-if="groupCounts[g.value]"
              :value="groupCounts[g.value]"
              class="tab-badge"
              type="info"
            />
          </span>
        </template>
      </el-tab-pane>
    </el-tabs>

    <!-- ── Config Table ──────────────────────────────────── -->
    <el-table
      :data="filteredConfigs"
      v-loading="loading"
      stripe
      border
      style="width: 100%"
      empty-text="暂无配置项"
      row-key="id"
    >
      <el-table-column prop="key" label="参数 Key" width="280" sortable>
        <template #default="{ row }">
          <code class="config-key">{{ row.key }}</code>
        </template>
      </el-table-column>

      <el-table-column label="Value" min-width="320">
        <template #default="{ row }">
          <!-- Inline editing mode -->
          <div v-if="editingId === row.id" class="inline-edit">
            <el-input
              v-model="editValue"
              size="small"
              style="flex: 1"
              :type="row.is_secret ? 'password' : 'text'"
              @keyup.enter="saveInlineEdit(row)"
            />
            <el-button size="small" type="primary" @click="saveInlineEdit(row)" :loading="saving">保存</el-button>
            <el-button size="small" @click="cancelInlineEdit">取消</el-button>
          </div>
          <!-- Display mode -->
          <div v-else class="value-cell">
            <span class="value-text" v-if="row.is_secret && !revealedSet.has(row.id)">••••••••</span>
            <span class="value-text" v-else>{{ row.value }}</span>
            <el-button
              v-if="row.is_secret"
              size="small"
              link
              @click="toggleReveal(row.id)"
            >
              <el-icon><component :is="revealedSet.has(row.id) ? Hide : View" /></el-icon>
            </el-button>
            <el-button size="small" link type="primary" @click="startInlineEdit(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />

      <el-table-column prop="group" label="分组" width="120" sortable>
        <template #default="{ row }">
          <el-tag size="small" :type="groupTagType(row.group)">{{ groupLabel(row.group) }}</el-tag>
        </template>
      </el-table-column>

      <el-table-column label="机密" width="70" align="center">
        <template #default="{ row }">
          <el-icon v-if="row.is_secret" color="#E6A23C"><Lock /></el-icon>
        </template>
      </el-table-column>

      <el-table-column prop="updated_at" label="更新时间" width="180" sortable>
        <template #default="{ row }">
          {{ formatTime(row.updated_at) }}
        </template>
      </el-table-column>

      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" link type="primary" @click="openEditDialog(row)">编辑</el-button>
          <el-button size="small" link type="danger" @click="confirmDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- ── Create / Edit Dialog ──────────────────────────── -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑配置' : '新增配置'"
      width="600px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="90px"
        label-position="right"
      >
        <el-form-item label="Key" prop="key">
          <el-input
            v-model="formData.key"
            placeholder="如 system.max_connections"
            :disabled="isEditing"
          />
        </el-form-item>

        <el-form-item label="Value" prop="value">
          <el-input
            v-model="formData.value"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 12 }"
            placeholder="输入值，支持 JSON / YAML 格式"
          />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input v-model="formData.description" placeholder="配置项用途说明" />
        </el-form-item>

        <el-form-item label="分组" prop="group">
          <el-select v-model="formData.group" placeholder="选择配置分组" style="width: 100%">
            <el-option
              v-for="g in configGroups"
              :key="g.value"
              :label="g.label"
              :value="g.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="敏感配置">
          <el-checkbox v-model="formData.is_secret">标记为机密（显示为 ***）</el-checkbox>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          {{ isEditing ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- ── Delete Confirmation Dialog ────────────────────── -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="确认删除"
      width="420px"
      @closed="deleteTarget = null"
    >
      <div class="delete-confirm-body">
        <el-icon :size="20" color="#F56C6C"><WarningFilled /></el-icon>
        <span>确定要删除配置项 <code>{{ deleteTarget?.key }}</code> 吗？此操作不可恢复。</span>
      </div>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="doDelete" :loading="deleting">确认删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  Edit, Plus, Refresh, Search, Lock, View, Hide, WarningFilled,
  Setting, Lock as Shield, MagicStick, DataLine, Bell,
} from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

// ── Types ──────────────────────────────────────────────
interface ConfigItem {
  id: string
  key: string
  value: string
  description: string
  group: string
  is_secret: boolean
  updated_at: string
}

// ── Config Group Definitions ───────────────────────────
const configGroups = [
  { value: 'general', label: '通用', icon: Setting },
  { value: 'security', label: '安全', icon: Shield },
  { value: 'llm', label: 'LLM', icon: MagicStick },
  { value: 'collector', label: '采集器', icon: DataLine },
  { value: 'notification', label: '通知', icon: Bell },
]

const groupMap = Object.fromEntries(configGroups.map(g => [g.value, g.label]))

function groupLabel(g: string) {
  return groupMap[g] || g
}

const groupTagTypes: Record<string, string> = {
  general: '',
  security: 'danger',
  llm: 'warning',
  collector: 'success',
  notification: 'info',
}

function groupTagType(g: string) {
  return groupTagTypes[g] || ''
}

// ── State ──────────────────────────────────────────────
const loading = ref(false)
const saving = ref(false)
const configs = ref<ConfigItem[]>([])
const activeGroup = ref('general')
const searchQuery = ref('')
const revealedSet = ref<Set<string>>(new Set())

// Inline edit
const editingId = ref('')
const editValue = ref('')

// Dialog
const dialogVisible = ref(false)
const isEditing = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const formData = reactive({
  id: '',
  key: '',
  value: '',
  description: '',
  group: 'general',
  is_secret: false,
})
const formRules: FormRules = {
  key: [{ required: true, message: '请输入配置 Key', trigger: 'blur' }],
  value: [{ required: true, message: '请输入配置值', trigger: 'blur' }],
  group: [{ required: true, message: '请选择分组', trigger: 'change' }],
}

// Delete
const deleteDialogVisible = ref(false)
const deleting = ref(false)
const deleteTarget = ref<ConfigItem | null>(null)

// System Info
const infoLoading = ref(false)
const systemInfo = ref<{ label: string; value: string; icon?: any; class?: string }[]>([])

// ── Computed ───────────────────────────────────────────
const filteredConfigs = computed(() => {
  let list = configs.value
  if (activeGroup.value !== 'all') {
    list = list.filter(c => c.group === activeGroup.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(c => c.key.toLowerCase().includes(q))
  }
  return list
})

const groupCounts = computed(() => {
  const counts: Record<string, number> = {}
  for (const g of configGroups) {
    counts[g.value] = configs.value.filter(c => c.group === g.value).length
  }
  counts['all'] = configs.value.length
  return counts
})

// ── System Info ────────────────────────────────────────
async function loadSystemInfo() {
  infoLoading.value = true
  try {
    const { data } = await api.get(R.PLATFORM_STATUS)
    if (data.code === 0) {
      const d = data.data
      systemInfo.value = [
        { label: '平台版本', value: d.version || '-', icon: Setting },
        { label: '运行时间', value: d.uptime || '-', icon: Refresh },
        {
          label: '数据库',
          value: d.database?.status || '未知',
          icon: DataLine,
          class: d.database?.status === 'healthy' ? 'status-ok' : 'status-warn',
        },
        { label: '配置总数', value: String(configs.value.length), icon: DataLine },
      ]
    }
  } catch {
    // Graceful fallback — show config count at least
    systemInfo.value = [
      { label: '配置总数', value: String(configs.value.length), icon: DataLine },
    ]
  } finally {
    infoLoading.value = false
  }
}

// ── Load Configs ───────────────────────────────────────
async function loadConfigs() {
  loading.value = true
  try {
    const { data } = await api.get(R.CONFIGS)
    if (data.code === 0) {
      configs.value = (data.data.items || data.data || []).map((c: any) => ({
        id: c.id ?? c.key,
        key: c.key,
        value: c.value ?? '',
        description: c.description ?? '',
        group: c.group ?? 'general',
        is_secret: !!c.is_secret,
        updated_at: c.updated_at ?? '',
      }))
    }
    loadSystemInfo()
  } catch (e: any) {
    ElMessage.error('加载系统配置失败')
  } finally {
    loading.value = false
  }
}

// ── Inline Edit ────────────────────────────────────────
function startInlineEdit(row: ConfigItem) {
  editingId.value = row.id
  editValue.value = row.is_secret && !revealedSet.value.has(row.id) ? '' : row.value
}

function cancelInlineEdit() {
  editingId.value = ''
  editValue.value = ''
}

async function saveInlineEdit(row: ConfigItem) {
  saving.value = true
  try {
    await api.put(R.CONFIG_DETAIL(row.id), { value: editValue.value })
    row.value = editValue.value
    editingId.value = ''
    ElMessage.success('配置已更新')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '更新失败')
  } finally {
    saving.value = false
  }
}

// ── Secret Reveal ──────────────────────────────────────
function toggleReveal(id: string) {
  if (revealedSet.value.has(id)) {
    revealedSet.value.delete(id)
  } else {
    revealedSet.value.add(id)
  }
  // trigger reactivity
  revealedSet.value = new Set(revealedSet.value)
}

// ── Group Change ───────────────────────────────────────
function onGroupChange() {
  // no-op; filteredConfigs reacts automatically
}

function onSearchClear() {
  searchQuery.value = ''
}

// ── Create / Edit Dialog ───────────────────────────────
function openCreateDialog() {
  isEditing.value = false
  formData.id = ''
  formData.key = ''
  formData.value = ''
  formData.description = ''
  formData.group = activeGroup.value === 'all' ? 'general' : activeGroup.value
  formData.is_secret = false
  dialogVisible.value = true
}

function openEditDialog(row: ConfigItem) {
  isEditing.value = true
  formData.id = row.id
  formData.key = row.key
  formData.value = row.value
  formData.description = row.description
  formData.group = row.group
  formData.is_secret = row.is_secret
  dialogVisible.value = true
}

function resetForm() {
  formData.id = ''
  formData.key = ''
  formData.value = ''
  formData.description = ''
  formData.group = 'general'
  formData.is_secret = false
  formRef.value?.resetFields()
}

async function submitForm() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload = {
      key: formData.key,
      value: formData.value,
      description: formData.description,
      group: formData.group,
      is_secret: formData.is_secret,
    }

    if (isEditing.value) {
      await api.put(R.CONFIG_DETAIL(formData.id), payload)
      ElMessage.success('配置已更新')
    } else {
      await api.post(R.CONFIGS, payload)
      ElMessage.success('配置已创建')
    }
    dialogVisible.value = false
    loadConfigs()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || (isEditing.value ? '更新失败' : '创建失败'))
  } finally {
    submitting.value = false
  }
}

// ── Delete ─────────────────────────────────────────────
function confirmDelete(row: ConfigItem) {
  deleteTarget.value = row
  deleteDialogVisible.value = true
}

async function doDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await api.delete(R.CONFIG_DETAIL(deleteTarget.value.id))
    ElMessage.success('配置已删除')
    deleteDialogVisible.value = false
    deleteTarget.value = null
    loadConfigs()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '删除失败')
  } finally {
    deleting.value = false
  }
}

// ── Helpers ────────────────────────────────────────────
function formatTime(t: string) {
  if (!t) return '-'
  return t.replace('T', ' ').substring(0, 19)
}

// ── Init ───────────────────────────────────────────────
onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}

/* ── System Info Panel ─────────────────────── */
.system-info-panel {
  display: flex;
  gap: 32px;
  padding: 16px 24px;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  flex-wrap: wrap;
}
.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 120px;
}
.info-label {
  font-size: 12px;
  color: #909399;
}
.info-value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 4px;
}
.status-ok { color: #67C23A; }
.status-warn { color: #E6A23C; }

/* ── Page Header ──────────────────────────── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}
.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* ── Tabs ─────────────────────────────────── */
.config-tabs {
  margin-bottom: 12px;
}
.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.tab-badge {
  margin-left: 4px;
}
.tab-badge :deep(.el-badge__content) {
  font-size: 10px;
  height: 16px;
  line-height: 16px;
  padding: 0 5px;
}

/* ── Table ────────────────────────────────── */
.config-key {
  font-size: 13px;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  color: #303133;
}

/* ── Inline Edit ──────────────────────────── */
.inline-edit {
  display: flex;
  align-items: center;
  gap: 8px;
}
.value-cell {
  display: flex;
  align-items: center;
  gap: 4px;
}
.value-text {
  flex: 1;
  word-break: break-all;
  font-size: 13px;
}

/* ── Delete Confirm ───────────────────────── */
.delete-confirm-body {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  line-height: 1.6;
}
.delete-confirm-body code {
  background: #fef0f0;
  padding: 2px 6px;
  border-radius: 3px;
  color: #F56C6C;
  font-weight: 600;
}
</style>
