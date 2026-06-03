<template>
  <div class="config-page">
    <!-- 页面头部 -->
    <div class="autops-page-header">
      <span class="autops-page-title">配置管理</span>
    </div>

    <!-- ========== 配置列表 ========== -->
    <div class="autops-card">
      <div class="autops-card-header">
        <span class="autops-card-title">配置列表</span>
        <div class="autops-toolbar-right">
          <el-input
            v-model="filters.search"
            placeholder="搜索配置名称"
            clearable
            style="width:180px"
            @clear="loadConfigs"
            @keyup.enter="loadConfigs"
          />
          <el-select
            v-model="filters.config_type"
            placeholder="配置类型"
            clearable
            style="width:160px"
            @change="loadConfigs"
          >
            <el-option v-for="t in configTypes" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
          <el-button type="primary" @click="openCreateDialog">新建配置</el-button>
        </div>
      </div>
      <div class="autops-card-body">

      <el-table stripe :data="configs" v-loading="loading"row-key="id">
        <el-table-column prop="name" label="配置名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="schema_def" label="Schema定义" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <code style="font-size:12px">{{ truncate(row.schema_def, 60) }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="config_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="typeTagMap[row.config_type] || 'info'">
              {{ formatConfigType(row.config_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="80" align="center">
          <template #default="{ row }">
            <span style="font-family:monospace">v{{ row.version }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_deleted" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="!row.is_deleted"
              size="small"
              active-text="激活"
              inactive-text="停用"
              inline-prompt
              @change="(val: boolean) => toggleActive(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="170">
          <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button size="small" type="warning" @click="openHistoryDialog(row)">历史</el-button>
            <el-button size="small" type="info" @click="openBindingDialog(row)">绑定</el-button>
            <el-popconfirm title="确定删除此配置？" @confirm="deleteConfig(row.id)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="pagination.total > pagination.pageSize"
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @change="loadConfigs"
      />
      </div>
    </div>

    <!-- ========== 创建/编辑对话框 ========== -->
    <el-dialog
      v-model="showFormDialog"
      :title="isEditing ? '编辑配置' : '新建配置'"
      width="600px"
      destroy-on-close
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="90px">
        <el-form-item label="配置名称" prop="name">
          <el-input
            v-model="formData.name"
            placeholder="例如: collector.ssh.timeout"
            :disabled="isEditing"
          />
        </el-form-item>
        <el-form-item label="Schema定义" prop="schema_def">
          <el-input
            v-model="formData.schema_def"
            type="textarea"
            :rows="8"
            placeholder="支持 JSON / 纯文本"
          />
        </el-form-item>
        <el-form-item label="类型" prop="config_type">
          <el-select v-model="formData.config_type" style="width:100%">
            <el-option v-for="t in configTypes" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="2" placeholder="配置说明(可选)" />
        </el-form-item>
        <el-form-item label="版本备注" v-if="isEditing">
          <el-input v-model="formData.version_note" placeholder="本次变更说明(可选)" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button type="primary" @click="saveConfig" :loading="saving">
          {{ isEditing ? '保存新版本' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- ========== 版本历史对话框 ========== -->
    <el-dialog
      v-model="showHistoryDialog"
      :title="`版本历史 - ${historyConfigName}`"
      width="780px"
      destroy-on-close
    >
      <div style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center">
        <span style="color:#86909c;font-size:13px">点击行查看详情，选择两个版本进行对比</span>
        <el-button
          type="primary"
          size="small"
          :disabled="selectedVersions.length !== 2"
          @click="openDiffView"
        >
          对比选中版本 ({{ selectedVersions.length }}/2)
        </el-button>
      </div>

      <el-table stripe
 :data="versions"
 v-loading="versionsLoading"row-key="id"
 size="small"
 @row-click="previewVersion"
 highlight-current-row
 @selection-change="handleVersionSelection"
 ref="versionTableRef"
 >
        <el-table-column type="selection" width="45" :selectable="(row: any) => true" />
        <el-table-column prop="version" label="版本" width="80" align="center">
          <template #default="{ row }">
            <span style="font-family:monospace;font-weight:600">v{{ row.version }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="schema_def" label="值预览" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <code style="font-size:12px">{{ truncate(row.config_value, 50) }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="version_note" label="备注" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ row.version_note || '-' }}</template>
        </el-table-column>
        <el-table-column prop="operator" label="操作人" width="100">
          <template #default="{ row }">{{ row.operator || '-' }}</template>
        </el-table-column>
        <el-table-column prop="is_active" label="激活" width="70" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_active" size="small" type="success">激活</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_active"
              size="small"
              type="warning"
              @click.stop="rollbackVersion(row)"
            >
              回滚
            </el-button>
            <el-tag v-else size="small" type="info">当前</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <!-- 版本详情预览 -->
      <div v-if="previewData" style="margin-top:16px">
        <h4 style="font-size:13px;color:#4e5969;margin-bottom:8px">
          版本详情 - v{{ previewData.version }}
          <span v-if="previewData.version_note" style="color:#86909c;margin-left:8px">
            {{ previewData.version_note }}
          </span>
        </h4>
        <JsonViewer v-if="isJsonValue(previewData.config_value)" :data="tryParseJson(previewData.config_value)" />
        <pre v-else class="value-preview">{{ previewData.config_value }}</pre>
      </div>
    </el-dialog>

    <!-- ========== 配置对比对话框 ========== -->
    <el-dialog
      v-model="showDiffDialog"
      title="版本对比"
      width="960px"
      destroy-on-close
    >
      <div v-if="diffLeft && diffRight" style="margin-bottom:12px;color:#86909c;font-size:13px">
        对比: v{{ diffLeft.version }} → v{{ diffRight.version }}
      </div>
      <ConfigDiffView
        v-if="diffLeft && diffRight"
        :old-value="diffLeft.config_value"
        :new-value="diffRight.config_value"
        :old-label="`v${diffLeft.version} (${formatTime(diffLeft.created_at)})`"
        :new-label="`v${diffRight.version} (${formatTime(diffRight.created_at)})`"
      />
    </el-dialog>

    <!-- ========== 配置绑定对话框 ========== -->
    <el-dialog
      v-model="showBindingDialog"
      :title="`配置绑定 - ${bindingConfigName}`"
      width="780px"
      destroy-on-close
    >
      <el-tabs>
        <el-tab-pane label="关联资产">
          <el-table stripe :data="boundAssets" v-loading="bindingLoading" size="small"max-height="300">
            <el-table-column prop="name" label="资产名称" min-width="140" show-overflow-tooltip />
            <el-table-column prop="ip" label="IP" width="140" />
            <el-table-column prop="asset_type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.asset_type }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!bindingLoading && !boundAssets.length" description="暂无关联资产" :image-size="60" />
        </el-tab-pane>
        <el-tab-pane label="关联策略">
          <el-table stripe :data="boundPolicies" v-loading="bindingLoading" size="small"max-height="300">
            <el-table-column prop="name" label="策略名称" min-width="160" show-overflow-tooltip />
            <el-table-column prop="policy_type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag size="small">{{ row.policy_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 'active' ? 'success' : 'info'">
                  {{ row.status === 'active' ? '生效' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!bindingLoading && !boundPolicies.length" description="暂无关联策略" :image-size="60" />
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import ConfigDiffView from '@/shared/components/ConfigDiffView.vue'
import JsonViewer from '@/shared/components/JsonViewer.vue'

// ──────────────── Types ────────────────
interface ConfigItem {
  id: string
  name: string
  schema_def: string
  config_type: string
  version: number
  is_deleted: boolean
  description?: string
  updated_at: string
  created_at: string
}

interface ConfigVersion {
  id: string
  config_definition_id: string
  version: number
  schema_def: string
  version_note?: string
  operator?: string
  is_deleted: boolean
  created_at: string
}

// ──────────────── Constants ────────────────
const configTypes = [
  { label: '采集模板', value: 'collection_template' },
  { label: '策略配置', value: 'policy_config' },
  { label: '通知配置', value: 'notification' },
  { label: '系统参数', value: 'system' },
]

const typeTagMap: Record<string, string> = {
  collection_template: '',
  policy_config: 'warning',
  notification: 'success',
  system: 'info',
}

// ──────────────── List State ────────────────
const loading = ref(false)
const configs = ref<ConfigItem[]>([])
const filters = reactive({ config_type: '', search: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

// ──────────────── Form State ────────────────
const showFormDialog = ref(false)
const isEditing = ref(false)
const editingId = ref('')
const saving = ref(false)

const defaultForm = {
  name: '',
  schema_def: '',
  config_type: 'system',
  description: '',
  version_note: '',
}
const formData = reactive({ ...defaultForm })

const formRules = {
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  schema_def: [{ required: true, message: '请输入Schema定义', trigger: 'blur' }],
  config_type: [{ required: true, message: '请选择类型', trigger: 'change' }],
}

// ──────────────── Version History State ────────────────
const showHistoryDialog = ref(false)
const historyConfigId = ref('')
const historyConfigName = ref('')
const versions = ref<ConfigVersion[]>([])
const versionsLoading = ref(false)
const selectedVersions = ref<ConfigVersion[]>([])
const previewData = ref<ConfigVersion | null>(null)

// ──────────────── Diff State ────────────────
const showDiffDialog = ref(false)
const diffLeft = ref<ConfigVersion | null>(null)
const diffRight = ref<ConfigVersion | null>(null)

// ──────────────── Binding State ────────────────
const showBindingDialog = ref(false)
const bindingConfigId = ref('')
const bindingConfigName = ref('')
const boundAssets = ref<any[]>([])
const boundPolicies = ref<any[]>([])
const bindingLoading = ref(false)

// ──────────────── Helpers ────────────────
function formatTime(t: string | undefined | null): string {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

function truncate(s: string | undefined | null, n: number): string {
  if (!s) return ''
  return s.length > n ? s.substring(0, n) + '...' : s
}

function formatConfigType(type: string): string {
  const found = configTypes.find(t => t.value === type)
  return found ? found.label : type
}

function isJsonValue(val: string): boolean {
  if (!val) return false
  const trimmed = val.trim()
  return (trimmed.startsWith('{') && trimmed.endsWith('}')) ||
         (trimmed.startsWith('[') && trimmed.endsWith(']'))
}

function tryParseJson(val: string): any {
  try { return JSON.parse(val) }
  catch { return val }
}

// ──────────────── Config CRUD ────────────────
async function loadConfigs() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.config_type) params.config_type = filters.config_type
    if (filters.search) params.search = filters.search

    const { data } = await api.get(R.CONFIGS, { params })
    if (data.code === 0) {
      configs.value = data.data?.items || []
      pagination.total = data.data?.total || 0
    }
  } catch (e: any) {
    ElMessage.error('加载配置失败: ' + (e.message || e))
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  isEditing.value = false
  editingId.value = ''
  Object.assign(formData, { ...defaultForm })
  showFormDialog.value = true
}

function openEditDialog(row: ConfigItem) {
  isEditing.value = true
  editingId.value = row.id
  Object.assign(formData, {
    name: row.name,
    schema_def: row.schema_def,
    config_type: row.config_type,
    description: row.description || '',
    version_note: '',
  })
  showFormDialog.value = true
}

async function saveConfig() {
  saving.value = true
  try {
    if (isEditing.value) {
      const payload = {
        schema_def: formData.schema_def,
        config_type: formData.config_type,
        description: formData.description,
        version_note: formData.version_note,
      }
      const { data } = await api.put(R.CONFIG_DETAIL(editingId.value), payload)
      if (data.code === 0) {
        ElMessage.success('已保存新版本')
        showFormDialog.value = false
        loadConfigs()
      } else {
        ElMessage.error(data.message || '保存失败')
      }
    } else {
      const payload = {
        name: formData.name,
        schema_def: formData.schema_def,
        config_type: formData.config_type,
        description: formData.description,
      }
      const { data } = await api.post(R.CONFIGS, payload)
      if (data.code === 0) {
        ElMessage.success('配置已创建')
        showFormDialog.value = false
        loadConfigs()
      } else {
        ElMessage.error(data.message || '创建失败')
      }
    }
  } catch (e: any) {
    ElMessage.error((isEditing.value ? '保存' : '创建') + '失败: ' + (e.message || e))
  } finally {
    saving.value = false
  }
}

async function deleteConfig(id: string) {
  try {
    const { data } = await api.delete(R.CONFIG_DETAIL(id))
    if (data.code === 0) {
      ElMessage.success('已删除')
      loadConfigs()
    } else {
      ElMessage.error(data.message || '删除失败')
    }
  } catch (e: any) {
    ElMessage.error('删除失败: ' + (e.message || e))
  }
}

// ──────────────── Publish / Activate ────────────────
async function toggleActive(row: ConfigItem, val: boolean) {
  try {
    const endpoint = val
      ? R.CONFIG_PUBLISH(row.id)
      : R.CONFIG_DETAIL(row.id)
    const payload = val ? {} : { is_deleted: true }
    const { data } = val
      ? await api.post(endpoint, payload)
      : await api.patch(endpoint, payload)
    if (data.code === 0) {
      ElMessage.success(val ? '已发布激活' : '已停用')
      loadConfigs()
    } else {
      ElMessage.error(data.message || '操作失败')
    }
  } catch (e: any) {
    ElMessage.error('操作失败: ' + (e.message || e))
  }
}

// ──────────────── Version History ────────────────
async function openHistoryDialog(row: ConfigItem) {
  historyConfigId.value = row.id
  historyConfigName.value = row.name
  previewData.value = null
  selectedVersions.value = []
  showHistoryDialog.value = true
  await loadVersions(row.id)
}

async function loadVersions(configId: string) {
  versionsLoading.value = true
  try {
    const { data } = await api.get(R.CONFIG_VERSIONS(configId))
    if (data.code === 0) {
      versions.value = data.data?.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载版本历史失败: ' + (e.message || e))
  } finally {
    versionsLoading.value = false
  }
}

function previewVersion(row: ConfigVersion) {
  previewData.value = row
}

function handleVersionSelection(rows: ConfigVersion[]) {
  if (rows.length > 2) {
    // Keep only the last two selected
    selectedVersions.value = rows.slice(-2)
  } else {
    selectedVersions.value = rows
  }
}

async function rollbackVersion(version: ConfigVersion) {
  try {
    await ElMessageBox.confirm(
      `确定回滚到 v${version.version}？当前激活版本将被替换。`,
      '确认回滚',
      { type: 'warning', confirmButtonText: '回滚', cancelButtonText: '取消' }
    )
    const { data } = await api.post(R.CONFIG_PUBLISH(version.id))
    if (data.code === 0) {
      ElMessage.success(`已回滚到 v${version.version}`)
      await loadVersions(historyConfigId.value)
      loadConfigs()
    } else {
      ElMessage.error(data.message || '回滚失败')
    }
  } catch {
    // User cancelled
  }
}

// ──────────────── Config Diff ────────────────
function openDiffView() {
  if (selectedVersions.value.length !== 2) return
  const [left, right] = selectedVersions.value
  // Order by version number (older first)
  if (left.version < right.version) {
    diffLeft.value = left
    diffRight.value = right
  } else {
    diffLeft.value = right
    diffRight.value = left
  }
  showDiffDialog.value = true
}

// ──────────────── Config Binding ────────────────
async function openBindingDialog(row: ConfigItem) {
  bindingConfigId.value = row.id
  bindingConfigName.value = row.name
  boundAssets.value = []
  boundPolicies.value = []
  showBindingDialog.value = true
  await loadBindings(row.id)
}

async function loadBindings(configId: string) {
  bindingLoading.value = true
  try {
    const { data } = await api.get(R.CONFIG_DETAIL(configId))
    if (data.code === 0) {
      boundAssets.value = data.data?.assets || data.data?.bound_assets || []
      boundPolicies.value = data.data?.policies || data.data?.bound_policies || []
    }
  } catch {
    // Silent - bindings may not be available
  } finally {
    bindingLoading.value = false
  }
}

// ──────────────── Init ────────────────
onMounted(() => loadConfigs())
</script>

<style scoped>
.config-page .value-preview {
  background: #f7f8fa;
  border: 1px solid #e5e6eb;
  border-radius: 4px;
  padding: 12px;
  font-size: 13px;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
  margin: 0;
}
</style>
