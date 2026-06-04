<template>
  <div class="script-list-page">
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">脚本库</div>
        <div class="autops-page-desc">管理可复用的自动化脚本</div>
      </div>
    </div>

    <!-- ========== 统计卡片 ========== -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="4">
        <div class="autops-card stat-card">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">脚本总数</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="autops-card stat-card stat-shell">
          <div class="stat-value">{{ stats.shell }}</div>
          <div class="stat-label">Shell</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="autops-card stat-card stat-python">
          <div class="stat-value">{{ stats.python }}</div>
          <div class="stat-label">Python</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="autops-card stat-card stat-powershell">
          <div class="stat-value">{{ stats.powershell }}</div>
          <div class="stat-label">PowerShell</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="autops-card stat-card stat-sql">
          <div class="stat-value">{{ stats.sql }}</div>
          <div class="stat-label">SQL</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="autops-card stat-card stat-rest">
          <div class="stat-value">{{ stats.rest_api }}</div>
          <div class="stat-label">REST API</div>
        </div>
      </el-col>
    </el-row>

    <!-- ========== 脚本列表 ========== -->
    <div class="autops-card section-card">
      
        <div class="autops-card-header">
          <span class="autops-card-title">脚本库</span>
          <div class="autops-card-header-actions">
            <el-button type="primary" @click="openCreateDialog">
              <el-icon><Plus /></el-icon> 新建脚本
            </el-button>
            <el-button @click="loadScripts">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
          </div>
        </div>
      

      <!-- 分类标签页 -->
      <el-tabs v-model="filters.script_type" @tab-change="onCategoryTabChange" class="category-tabs">
        <el-tab-pane label="全部" name="" />
        <el-tab-pane label="Shell" name="shell" />
        <el-tab-pane label="Python" name="python" />
        <el-tab-pane label="PowerShell" name="powershell" />
        <el-tab-pane label="SQL" name="sql" />
        <el-tab-pane label="REST API" name="rest_api" />
      </el-tabs>

      <!-- 高级筛选 -->
      <div class="autops-toolbar">
      <el-form :inline="true" class="filter-form">
        <el-form-item label="关键字">
          <el-input
            v-model="filters.search"
            placeholder="脚本名称 / 描述搜索"
            clearable
            style="width: 220px"
            @clear="loadScripts"
            @keyup.enter="loadScripts"
          />
        </el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="filters.risk_level" placeholder="全部" clearable @change="loadScripts">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="严重" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-input
            v-model="filters.tag"
            placeholder="标签筛选"
            clearable
            style="width: 160px"
            @clear="loadScripts"
            @keyup.enter="loadScripts"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadScripts">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

      <!-- 脚本列表表格 -->
      <el-table stripe :data="scripts" v-loading="loading"row-key="id">
        <el-table-column prop="name" label="名称" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="script-name-link" @click="openDetailDrawer(row)">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="script_type" label="分类" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="categoryTagMap[row.script_type] || 'info'">
              {{ formatCategory(row.script_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险等级" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="riskTagMap[row.risk_level] || 'info'" effect="dark">
              {{ formatRiskLevel(row.risk_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ row.description || '-' }}</template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="80" align="center">
          <template #default="{ row }">
            <span class="version-text">v{{ row.version || 1 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="标签" min-width="140">
          <template #default="{ row }">
            <div class="tag-list">
              <el-tag
                v-for="tag in (row.tags || []).slice(0, 2)"
                :key="tag"
                size="small"
                type="info"
                effect="plain"
                class="tiny-tag"
              >{{ tag }}</el-tag>
              <el-tag v-if="(row.tags || []).length > 2" size="small" type="info" effect="plain" class="tiny-tag">
                +{{ row.tags.length - 2 }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openDetailDrawer(row)">详情</el-button>
            <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button size="small" type="success" @click="duplicateScript(row)">复制</el-button>
            <el-button size="small" type="warning" @click="quickExecute(row)">执行</el-button>
            <el-popconfirm title="确认删除该脚本？" @confirm="confirmDeleteScript(row)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        class="pagination"
        @change="loadScripts"
      />
    </div>

    <!-- ========== 创建/编辑脚本对话框 ========== -->
    <el-dialog
      v-model="showFormDialog"
      :title="isEditing ? '编辑脚本' : '新建脚本'"
      width="820px"
      destroy-on-close
      :close-on-click-modal="false"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="名称" prop="name">
              <el-input v-model="formData.name" placeholder="请输入脚本名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分类" prop="script_type">
              <el-select v-model="formData.script_type" style="width: 100%">
                <el-option label="Shell" value="shell" />
                <el-option label="Python" value="python" />
                <el-option label="PowerShell" value="powershell" />
                <el-option label="SQL" value="sql" />
                <el-option label="REST API" value="rest_api" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="风险等级" prop="risk_level">
              <el-select v-model="formData.risk_level" style="width: 100%">
                <el-option label="低" value="low" />
                <el-option label="中" value="medium" />
                <el-option label="高" value="high" />
                <el-option label="严重" value="critical" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="版本号">
              <el-input-number
                v-model="formData.version"
                :min="1"
                :max="999"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="2"
            placeholder="脚本用途说明"
          />
        </el-form-item>

        <el-form-item label="标签">
          <div class="tags-editor">
            <el-tag
              v-for="tag in formData.tags"
              :key="tag"
              closable
              size="default"
              class="edit-tag"
              @close="removeTag(tag)"
            >{{ tag }}</el-tag>
            <el-input
              v-if="tagInputVisible"
              ref="tagInputRef"
              v-model="tagInputValue"
              size="default"
              style="width: 120px"
              @keyup.enter="addTag"
              @blur="addTag"
            />
            <el-button v-else size="small" @click="showTagInput">+ 添加标签</el-button>
          </div>
        </el-form-item>

        <el-form-item label="脚本内容" prop="content">
          <div class="script-editor-wrapper">
            <div class="line-numbers" ref="lineNumbersRef">
              <div v-for="n in contentLineCount" :key="n" class="line-num">{{ n }}</div>
            </div>
            <el-input
              v-model="formData.content"
              type="textarea"
              :rows="16"
              placeholder="请输入脚本代码"
              class="script-textarea"
              @scroll="syncScroll"
            />
          </div>
        </el-form-item>

        <!-- 参数定义 -->
        <el-form-item label="参数定义">
          <div class="params-section">
            <el-table stripe  :data="formData.parameters" size="small" border style="width: 100%">
              <el-table-column prop="name" label="参数名" min-width="120">
                <template #default="{ row }">
                  <el-input v-model="row.name" size="small" placeholder="参数名" />
                </template>
              </el-table-column>
              <el-table-column prop="type" label="类型" width="130">
                <template #default="{ row }">
                  <el-select v-model="row.type" size="small" style="width: 100%">
                    <el-option label="字符串" value="string" />
                    <el-option label="整数" value="integer" />
                    <el-option label="布尔" value="boolean" />
                    <el-option label="浮点数" value="float" />
                    <el-option label="列表" value="list" />
                    <el-option label="对象" value="object" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column prop="default_value" label="默认值" min-width="120">
                <template #default="{ row }">
                  <el-input v-model="row.default_value" size="small" placeholder="默认值" />
                </template>
              </el-table-column>
              <el-table-column prop="required" label="必填" width="70" align="center">
                <template #default="{ row }">
                  <el-checkbox v-model="row.required" />
                </template>
              </el-table-column>
              <el-table-column prop="description" label="说明" min-width="140">
                <template #default="{ row }">
                  <el-input v-model="row.description" size="small" placeholder="参数说明" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100" align="center">
                <template #default="{ $index }">
                  <el-button type="danger" size="small" plain @click="removeParam($index)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-button size="small" type="primary" plain style="margin-top: 8px" @click="addParam">
              <el-icon><Plus /></el-icon> 添加参数
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button type="primary" @click="saveScript" :loading="saving">
          {{ isEditing ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- ========== 脚本详情抽屉 ========== -->
    <el-drawer
      v-model="showDetailDrawer"
      :title="currentScript ? currentScript.name : '脚本详情'"
      size="680px"
      destroy-on-close
    >
      <template v-if="currentScript">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ currentScript.name }}</el-descriptions-item>
          <el-descriptions-item label="分类">
            <el-tag size="small" :type="categoryTagMap[currentScript.script_type] || 'info'">
              {{ formatCategory(currentScript.script_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="风险等级">
            <el-tag size="small" :type="riskTagMap[currentScript.risk_level] || 'info'" effect="dark">
              {{ formatRiskLevel(currentScript.risk_level) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="版本">
            <span class="version-text">v{{ currentScript.version || 1 }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTime(currentScript.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatTime(currentScript.updated_at) }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ currentScript.description || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="标签" :span="2">
            <div class="tag-list">
              <el-tag
                v-for="tag in (currentScript.tags || [])"
                :key="tag"
                size="small"
                type="info"
                effect="plain"
                style="margin-right: 4px"
              >{{ tag }}</el-tag>
              <span v-if="!(currentScript.tags || []).length" class="text-muted">无标签</span>
            </div>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 脚本代码 -->
        <div class="detail-section">
          <h4 class="detail-subtitle">脚本代码</h4>
          <div class="code-container">
            <div class="code-line-numbers">
              <div v-for="n in scriptCodeLines" :key="n" class="line-num">{{ n }}</div>
            </div>
            <pre class="code-content">{{ currentScript.content || '(空)' }}</pre>
          </div>
        </div>

        <!-- 参数列表 -->
        <div class="detail-section">
          <h4 class="detail-subtitle">参数列表</h4>
          <el-table stripe
 v-if="(currentScript.parameters || []).length"
 :data="currentScript.parameters"
 size="small"
 border>
            <el-table-column prop="name" label="参数名" min-width="120" />
            <el-table-column prop="type" label="类型" width="90" />
            <el-table-column prop="default_value" label="默认值" min-width="100">
              <template #default="{ row }">{{ row.default_value ?? '-' }}</template>
            </el-table-column>
            <el-table-column prop="required" label="必填" width="70" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.required ? 'danger' : 'info'">
                  {{ row.required ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="说明" min-width="140">
              <template #default="{ row }">{{ row.description || '-' }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="无参数定义" :image-size="50" />
        </div>

        <!-- 版本历史 -->
        <div class="detail-section">
          <h4 class="detail-subtitle">版本历史</h4>
          <el-table stripe
 v-if="versionHistory.length"
 :data="versionHistory"
 v-loading="versionLoading"
 size="small"
 bordermax-height="220"
 >
            <el-table-column prop="version" label="版本" width="80" align="center">
              <template #default="{ row }">v{{ row.version }}</template>
            </el-table-column>
            <el-table-column prop="description" label="变更说明" min-width="180" show-overflow-tooltip>
              <template #default="{ row }">{{ row.description || '-' }}</template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="170">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-else-if="!versionLoading" description="暂无版本历史" :image-size="50" />
        </div>

        <!-- 关联 Playbook -->
        <div class="detail-section">
          <h4 class="detail-subtitle">关联 Playbook</h4>
          <el-table stripe
 v-if="relatedPlaybooks.length"
 :data="relatedPlaybooks"
 v-loading="playbookLoading"
 size="small"
 bordermax-height="220"
 >
            <el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.status || 'draft' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="updated_at" label="更新时间" width="170">
              <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-else-if="!playbookLoading" description="未被任何 Playbook 引用" :image-size="50" />
        </div>

        <!-- 抽屉底部操作 -->
        <div class="drawer-footer">
          <el-button @click="openEditDialog(currentScript); showDetailDrawer = false">编辑</el-button>
          <el-button type="success" @click="duplicateScript(currentScript)">复制</el-button>
          <el-button type="warning" @click="quickExecute(currentScript)">快速执行</el-button>
        </div>
      </template>
    </el-drawer>

    <!-- ========== 删除确认对话框 (带使用检查) ========== -->
    <el-dialog v-model="showDeleteDialog" title="确认删除" width="600px" destroy-on-close>
      <template v-if="deletingScript">
        <p>确定删除脚本 <strong>{{ deletingScript.name }}</strong> ？</p>
        <div v-if="deleteUsage.playbookCount > 0" class="delete-warning">
          <el-alert
            type="warning"
            :closable="false"
            show-icon
          >
            <template #title>
              该脚本正被 <strong>{{ deleteUsage.playbookCount }}</strong> 个 Playbook 引用，删除后可能影响编排流程。
            </template>
          </el-alert>
        </div>
        <div v-if="deleteUsage.recentExecutions > 0" class="delete-warning">
          <el-alert
            type="info"
            :closable="false"
            show-icon
          >
            <template #title>
              该脚本近 7 天有 <strong>{{ deleteUsage.recentExecutions }}</strong> 次执行记录。
            </template>
          </el-alert>
        </div>
      </template>
      <template #footer>
        <el-button @click="showDeleteDialog = false">取消</el-button>
        <el-button type="danger" @click="doDeleteScript" :loading="deleting">确认删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Refresh, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

// ---------- Router ----------
const router = useRouter()

// ---------- Types ----------
interface ScriptParameter {
  name: string
  type: string
  default_value: string
  required: boolean
  description: string
}

interface Script {
  id: string
  name: string
  script_type: string
  description: string
  content: string
  risk_level: string
  version: number
  tags: string[]
  parameters: ScriptParameter[]
  created_at: string
  updated_at: string
}

// ---------- Constants ----------
const categoryTagMap: Record<string, string> = {
  shell: '', python: 'success', powershell: 'warning', sql: 'danger', rest_api: 'info',
}

const riskTagMap: Record<string, string> = {
  low: 'success', medium: 'warning', high: 'danger', critical: 'dark',
}

const categoryLabels: Record<string, string> = {
  shell: 'Shell', python: 'Python', powershell: 'PowerShell', sql: 'SQL', rest_api: 'REST API',
}

const riskLabels: Record<string, string> = {
  low: '低', medium: '中', high: '高', critical: '严重',
}

// ---------- State ----------
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const scripts = ref<Script[]>([])

const filters = reactive({
  search: '',
  script_type: '',
  risk_level: '',
  tag: '',
})
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const stats = reactive({
  total: 0,
  shell: 0,
  python: 0,
  powershell: 0,
  sql: 0,
  rest_api: 0,
})

// Form dialog
const showFormDialog = ref(false)
const isEditing = ref(false)
const editingId = ref('')
const formRef = ref<FormInstance>()
const tagInputVisible = ref(false)
const tagInputValue = ref('')
const tagInputRef = ref<InstanceType<typeof import('element-plus')['ElInput']>>()
const lineNumbersRef = ref<HTMLElement>()

const defaultFormData = () => ({
  name: '',
  script_type: 'shell',
  description: '',
  content: '',
  risk_level: 'low',
  version: 1,
  tags: [] as string[],
  parameters: [] as ScriptParameter[],
})

const formData = reactive(defaultFormData())

const formRules: FormRules = {
  name: [{ required: true, message: '请输入脚本名称', trigger: 'blur' }],
  script_type: [{ required: true, message: '请选择分类', trigger: 'change' }],
  content: [{ required: true, message: '请输入脚本内容', trigger: 'blur' }],
  risk_level: [{ required: true, message: '请选择风险等级', trigger: 'change' }],
}

// Detail drawer
const showDetailDrawer = ref(false)
const currentScript = ref<Script | null>(null)
const versionHistory = ref<any[]>([])
const versionLoading = ref(false)
const relatedPlaybooks = ref<any[]>([])
const playbookLoading = ref(false)

// Delete dialog
const showDeleteDialog = ref(false)
const deletingScript = ref<Script | null>(null)
const deleteUsage = reactive({ playbookCount: 0, recentExecutions: 0 })

// ---------- Computed ----------
const contentLineCount = computed(() => {
  const lines = (formData.content || '').split('\n').length
  return Math.max(lines, 16)
})

const scriptCodeLines = computed(() => {
  if (!currentScript.value?.content) return 1
  return currentScript.value.content.split('\n').length
})

// ---------- Helpers ----------
function formatTime(t: string | undefined | null): string {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

function formatCategory(type: string): string {
  return categoryLabels[type] || type
}

function formatRiskLevel(level: string): string {
  return riskLabels[level] || level
}

function syncScroll(e: Event) {
  const ta = e.target as HTMLTextAreaElement
  if (lineNumbersRef.value) {
    lineNumbersRef.value.scrollTop = ta.scrollTop
  }
}

// ---------- Stats ----------
async function loadStats() {
  try {
    const { data } = await api.get(API.SCRIPTS, { params: { page: 1, page_size: 1 } })
    if (data.code === 0) {
      stats.total = data.data.total || 0
    }
  } catch { /* ignore */ }

  const types = ['shell', 'python', 'powershell', 'sql', 'rest_api'] as const
  await Promise.allSettled(
    types.map(async (t) => {
      try {
        const { data } = await api.get(API.SCRIPTS, { params: { page: 1, page_size: 1, script_type: t } })
        if (data.code === 0) {
          stats[t] = data.data.total || 0
        }
      } catch { /* ignore */ }
    }),
  )
}

// ---------- Scripts CRUD ----------
async function loadScripts() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.search) params.search = filters.search
    if (filters.script_type) params.script_type = filters.script_type
    if (filters.risk_level) params.risk_level = filters.risk_level
    if (filters.tag) params.tag = filters.tag

    const { data } = await api.get(API.SCRIPTS, { params })
    if (data.code === 0) {
      scripts.value = data.data.items || []
      pagination.total = data.data.total || 0
    }
  } catch (e: any) {
    ElMessage.error('加载脚本失败: ' + (e.message || e))
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.search = ''
  filters.script_type = ''
  filters.risk_level = ''
  filters.tag = ''
  pagination.page = 1
  loadScripts()
}

function onCategoryTabChange() {
  pagination.page = 1
  loadScripts()
}

// ---------- Create / Edit ----------
function openCreateDialog() {
  isEditing.value = false
  editingId.value = ''
  Object.assign(formData, defaultFormData())
  showFormDialog.value = true
}

function openEditDialog(row: Script) {
  isEditing.value = true
  editingId.value = row.id
  Object.assign(formData, {
    name: row.name,
    script_type: row.script_type,
    description: row.description || '',
    content: row.content || '',
    risk_level: row.risk_level || 'low',
    version: row.version || 1,
    tags: [...(row.tags || [])],
    parameters: (row.parameters || []).map((p: ScriptParameter) => ({ ...p })),
  })
  showFormDialog.value = true
}

async function saveScript() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const payload = {
      name: formData.name,
      script_type: formData.script_type,
      description: formData.description,
      content: formData.content,
      risk_level: formData.risk_level,
      version: formData.version,
      tags: formData.tags,
      parameters: formData.parameters.filter((p) => p.name),
    }

    if (isEditing.value) {
      const { data } = await api.put(API.SCRIPTS + '/' + editingId.value, payload)
      if (data.code === 0) {
        ElMessage.success('保存成功')
        showFormDialog.value = false
        loadScripts()
        loadStats()
      } else {
        ElMessage.error(data.message || '保存失败')
      }
    } else {
      const { data } = await api.post(API.SCRIPTS, payload)
      if (data.code === 0) {
        ElMessage.success('创建成功')
        showFormDialog.value = false
        loadScripts()
        loadStats()
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

// ---------- Tags ----------
function showTagInput() {
  tagInputVisible.value = true
  tagInputValue.value = ''
  nextTick(() => tagInputRef.value?.focus())
}

function addTag() {
  const val = tagInputValue.value.trim()
  if (val && !formData.tags.includes(val)) {
    formData.tags.push(val)
  }
  tagInputVisible.value = false
  tagInputValue.value = ''
}

function removeTag(tag: string) {
  formData.tags = formData.tags.filter((t) => t !== tag)
}

// ---------- Parameters ----------
function addParam() {
  formData.parameters.push({
    name: '',
    type: 'string',
    default_value: '',
    required: false,
    description: '',
  })
}

function removeParam(index: number) {
  formData.parameters.splice(index, 1)
}

// ---------- Detail Drawer ----------
async function openDetailDrawer(row: Script) {
  currentScript.value = row
  showDetailDrawer.value = true
  versionHistory.value = []
  relatedPlaybooks.value = []

  // Load version history
  versionLoading.value = true
  try {
    const { data } = await api.get(API.SCRIPTS + '/' + row.id + '/versions', {
      params: { page: 1, page_size: 20 },
    })
    if (data.code === 0) {
      versionHistory.value = data.data.items || data.data || []
    }
  } catch {
    // versions endpoint optional
  } finally {
    versionLoading.value = false
  }

  // Load related playbooks
  playbookLoading.value = true
  try {
    const { data } = await api.get(API.SCRIPTS + '/' + row.id + '/playbooks', {
      params: { page: 1, page_size: 20 },
    })
    if (data.code === 0) {
      relatedPlaybooks.value = data.data.items || data.data || []
    }
  } catch {
    // playbooks endpoint optional
  } finally {
    playbookLoading.value = false
  }
}

// ---------- Delete ----------
async function confirmDeleteScript(row: Script) {
  deletingScript.value = row
  deleteUsage.playbookCount = 0
  deleteUsage.recentExecutions = 0

  // Check usage
  try {
    const { data } = await api.get(API.SCRIPTS + '/' + row.id + '/usage')
    if (data.code === 0) {
      deleteUsage.playbookCount = data.data?.playbook_count || 0
      deleteUsage.recentExecutions = data.data?.recent_executions || 0
    }
  } catch {
    // usage endpoint optional, proceed anyway
  }

  if (deleteUsage.playbookCount > 0 || deleteUsage.recentExecutions > 0) {
    showDeleteDialog.value = true
  } else {
    doDeleteScript()
  }
}

async function doDeleteScript() {
  if (!deletingScript.value) return
  deleting.value = true
  try {
    const { data } = await api.delete(API.SCRIPTS + '/' + deletingScript.value.id)
    if (data.code === 0 || data.status === 204 || data.status === 200) {
      ElMessage.success('删除成功')
      showDeleteDialog.value = false
      loadScripts()
      loadStats()
    } else {
      ElMessage.error(data.message || '删除失败')
    }
  } catch (e: any) {
    ElMessage.error('删除失败: ' + (e.message || e))
  } finally {
    deleting.value = false
  }
}

// ---------- Duplicate ----------
async function duplicateScript(row: Script) {
  try {
    const payload = {
      name: row.name + ' (副本)',
      script_type: row.script_type,
      description: row.description,
      content: row.content,
      risk_level: row.risk_level,
      version: 1,
      tags: [...(row.tags || [])],
      parameters: (row.parameters || []).map((p) => ({ ...p })),
    }
    const { data } = await api.post(API.SCRIPTS, payload)
    if (data.code === 0) {
      ElMessage.success('脚本已复制')
      loadScripts()
      loadStats()
    } else {
      ElMessage.error(data.message || '复制失败')
    }
  } catch (e: any) {
    ElMessage.error('复制失败: ' + (e.message || e))
  }
}

// ---------- Quick Execute ----------
function quickExecute(row: Script) {
  router.push({
    name: 'executions',
    query: {
      script_id: row.id,
      script_name: row.name,
    },
  })
}

// ---------- Init ----------
onMounted(() => {
  loadScripts()
  loadStats()
})
</script>

<style scoped>
.script-list-page {
  padding: 0;
}

/* ---- Statistics ---- */
.stat-row {
  margin-bottom: 16px;
}
.stat-card 
.stat-card 
.stat-shell .stat-value { color: #165dff; }
.stat-python .stat-value { color: #00b42a; }
.stat-powershell .stat-value { color: #ff7d00; }
.stat-sql .stat-value { color: #f53f3f; }
.stat-rest .stat-value { color: #86909c; }

/* ---- Section ---- */
.section-card {
  margin-bottom: 20px;
}
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}
.category-tabs {
  margin-bottom: 4px;
}

/* ---- Filters ---- */
.filter-form {
  margin-bottom: 16px;
}

/* ---- Table ---- */
.script-name-link {
  color: #165dff;
  cursor: pointer;
  font-weight: 500;
}

.script-name-link:hover {
  text-decoration: underline;
}

.version-text {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  color: #4e5969;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tiny-tag {
  font-size: 11px;
}

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

/* ---- Script Editor ---- */
.script-editor-wrapper {
  position: relative;
  display: flex;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  width: 100%;
}

.script-editor-wrapper:focus-within {
  border-color: #165dff;
}

.line-numbers {
  background: #f7f8fa;
  padding: 8px 0;
  min-width: 40px;
  text-align: right;
  user-select: none;
  overflow: hidden;
  flex-shrink: 0;
}

.line-num {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 21px;
  color: #c9cdd4;
  padding-right: 8px;
}

.script-textarea :deep(textarea) {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace !important;
  font-size: 13px !important;
  line-height: 21px !important;
  padding: 8px 12px !important;
  border: none !important;
  box-shadow: none !important;
  resize: none;
}

/* ---- Tags Editor ---- */
.tags-editor {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.edit-tag {
  font-size: 13px;
}

/* ---- Params Section ---- */
.params-section {
  width: 100%;
}

/* ---- Detail Drawer ---- */
.detail-section {
  margin-top: 20px;
}

.detail-subtitle {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid #e5e6eb;
}

.code-container {
  position: relative;
  display: flex;
  background: #1e1e1e;
  border-radius: 6px;
  overflow: hidden;
  max-height: 400px;
  overflow-y: auto;
}

.code-line-numbers {
  background: #2d2d2d;
  padding: 12px 0;
  min-width: 42px;
  text-align: right;
  user-select: none;
  flex-shrink: 0;
}

.code-line-numbers .line-num {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 20px;
  color: #858585;
  padding-right: 10px;
}

.code-content {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 20px;
  color: #c9cdd4;
  margin: 0;
  padding: 12px 16px;
  white-space: pre;
  overflow-x: auto;
  flex: 1;
}

.text-muted {
  color: #86909c;
  font-size: 13px;
}

.drawer-footer {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e5e6eb;
  display: flex;
  gap: 8px;
}

/* ---- Delete Dialog ---- */
.delete-warning {
  margin-top: 12px;
}

/* ---- Element Plus Overrides ---- */
:deep(.el-descriptions__label) {
  width: 100px;
  font-weight: 500;
}

:deep(.el-dialog__body) {
  padding-top: 16px;
  padding-bottom: 8px;
}

:deep(.el-drawer__body) {
  padding: 16px 20px;
}
</style>
