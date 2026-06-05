<template>
  <div class="autops-page-container">
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">配置版本</div>
        <div class="autops-page-desc">管理配置定义的版本发布、回滚与对比</div>
      </div>
    </div>

    <!-- Filter by definition + search -->
    <el-card class="mb-md">
      <el-row :gutter="16" align="middle">
        <el-col :span="8">
          <el-select v-model="selectedDefId" placeholder="选择配置定义" clearable filterable @change="fetchVersions" style="width: 100%">
            <el-option v-for="d in definitions" :key="d.id" :label="d.name" :value="d.id">
              <span>{{ d.name }}</span>
              <span class="text-tertiary font-12" style="margin-left: 8px">{{ d.config_type }}</span>
            </el-option>
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-input v-model="versionSearch" placeholder="搜索版本号" clearable @keyup.enter="fetchVersions" style="width: 100%" />
        </el-col>
        <el-col :span="4">
          <el-select v-model="statusFilter" placeholder="全部状态" clearable @change="fetchVersions" style="width: 100%">
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-col>
        <el-col :span="8" style="text-align: right">
          <el-button type="primary" :disabled="!selectedDefId" @click="openCreateVersion">新建版本</el-button>
          <el-button :disabled="!selectedDefId || !canRollback" @click="openRollbackDialog">回滚</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- Version Table -->
    <el-card v-loading="loading">
      <div v-if="!selectedDefId" class="empty-state">
        <el-empty description="请选择一个配置定义查看版本历史" />
      </div>
      <div v-else-if="filteredVersions.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无版本记录" />
      </div>
      <div v-else>
        <el-table stripe :data="filteredVersions" border size="small" row-key="id" class="version-table">
          <el-table-column prop="version" label="版本号" width="100" align="center">
            <template #default="{ row }">
              <span class="version-number">v{{ row.version }}</span>
            </template>
          </el-table-column>
          <el-table-column label="配置定义" min-width="160" show-overflow-tooltip>
            <template #default>
              <span>{{ currentDefName }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="statusTag(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="published_at" label="发布时间" width="180" align="center">
            <template #default="{ row }">
              {{ row.published_at ? formatTime(row.published_at) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="published_by" label="操作人" width="120" align="center">
            <template #default="{ row }">
              {{ row.published_by || row.created_by || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180" align="center">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="240" align="center" fixed="right">
            <template #default="{ row }">
              <el-button plain type="primary" size="small" @click="viewContent(row)">详情</el-button>
              <el-button v-if="row.status === 'draft'" plain type="success" size="small" @click="publishVersion(row)">发布</el-button>
              <el-button plain type="info" size="small" @click="openDiffDialog(row)">对比</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- View Content Dialog -->
    <el-dialog v-model="contentDialogVisible" title="配置内容" width="600px">
      <el-input type="textarea" :model-value="viewingContent" :rows="18" readonly style="font-family: monospace" />
    </el-dialog>

    <!-- Create Version Dialog -->
    <el-dialog v-model="createDialogVisible" title="新建配置版本" width="600px" destroy-on-close>
      <el-form :model="newVersion" label-width="100px">
        <el-form-item label="配置内容" required>
          <el-input v-model="newVersion.content" type="textarea" :rows="12" placeholder="输入JSON/YAML配置内容" style="font-family: monospace" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitVersion">创建</el-button>
      </template>
    </el-dialog>

    <!-- Diff Dialog -->
    <el-dialog v-model="diffDialogVisible" title="版本对比" width="800px" destroy-on-close>
      <el-form :inline="true" class="mb-lg">
        <el-form-item label="对比版本">
          <el-select v-model="diffTargetVersionId" placeholder="选择对比目标版本" style="width: 300px">
            <el-option
              v-for="v in versions"
              :key="v.id"
              :label="'v' + v.version + ' (' + statusText(v.status) + ')'"
              :value="v.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="doDiff">执行对比</el-button>
        </el-form-item>
      </el-form>
      <div v-if="diffResult" class="diff-result">
        <el-row :gutter="16">
          <el-col :span="12">
            <h4>当前版本 (v{{ diffSourceVersion }})</h4>
            <pre class="diff-code">{{ diffResult.source }}</pre>
          </el-col>
          <el-col :span="12">
            <h4>目标版本 (v{{ diffTargetVersionLabel }})</h4>
            <pre class="diff-code">{{ diffResult.target }}</pre>
          </el-col>
        </el-row>
      </div>
      <div v-else-if="diffLoading" style="text-align: center; padding: 40px 0">
        <el-icon :size="24" class="is-loading"><Loading /></el-icon>
        <p>对比中...</p>
      </div>
    </el-dialog>

    <!-- Rollback Dialog -->
    <el-dialog v-model="rollbackDialogVisible" title="版本回滚" width="480px">
      <el-alert type="warning" :closable="false" show-icon class="mb-lg">
        回滚将恢复到指定版本的配置内容，当前草稿版本将被替换。
      </el-alert>
      <el-form label-width="80px">
        <el-form-item label="回滚到">
          <el-select v-model="rollbackTargetId" placeholder="选择目标版本" style="width: 100%">
            <el-option
              v-for="v in publishedVersions"
              :key="v.id"
              :label="'v' + v.version"
              :value="v.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rollbackDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="rollbackLoading" @click="doRollback">确认回滚</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

var loading = ref(false)
var definitions = ref<any[]>([])
var versions = ref<any[]>([])
var selectedDefId = ref('')
var versionSearch = ref('')
var statusFilter = ref('')

var contentDialogVisible = ref(false)
var viewingContent = ref('')
var createDialogVisible = ref(false)
var submitting = ref(false)
var diffDialogVisible = ref(false)
var diffTargetVersionId = ref('')
var diffSourceVersion = ref(0)
var diffTargetVersionLabel = ref('')
var diffResult = ref<{ source: string; target: string } | null>(null)
var diffLoading = ref(false)
var rollbackDialogVisible = ref(false)
var rollbackTargetId = ref('')
var rollbackLoading = ref(false)

var newVersion = reactive({ content: '' })

var currentDefName = computed(function() {
  if (!selectedDefId.value) return ''
  var found = definitions.value.find(function(d) { return d.id === selectedDefId.value })
  return found ? found.name : ''
})

var filteredVersions = computed(function() {
  var data = versions.value
  if (statusFilter.value) {
    data = data.filter(function(v) { return v.status === statusFilter.value })
  }
  if (versionSearch.value) {
    var kw = versionSearch.value
    data = data.filter(function(v) { return String(v.version).indexOf(kw) >= 0 })
  }
  return data
})

var publishedVersions = computed(function() {
  return versions.value.filter(function(v) { return v.status === 'published' })
})

var canRollback = computed(function() {
  return publishedVersions.value.length > 0
})

async function fetchDefinitions() {
  try {
    var resp = await api.get(API.CONFIGS, { params: { page_size: 100 } })
    if (resp.data?.code === 0) {
      definitions.value = resp.data.data?.items || []
    }
  } catch (e) {
    console.error('Failed to fetch definitions:', e)
  }
}

async function fetchVersions() {
  if (!selectedDefId.value) {
    versions.value = []
    return
  }
  loading.value = true
  try {
    var resp = await api.get(API.CONFIG_VERSIONS(selectedDefId.value))
    if (resp.data?.code === 0) {
      versions.value = resp.data.data || []
    }
  } catch (e) {
    console.error('Failed to fetch versions:', e)
  } finally {
    loading.value = false
  }
}

function viewContent(ver: any) {
  try {
    viewingContent.value = JSON.stringify(JSON.parse(ver.content), null, 2)
  } catch {
    viewingContent.value = ver.content
  }
  contentDialogVisible.value = true
}

async function publishVersion(ver: any) {
  try {
    await ElMessageBox.confirm('确认发布版本 v' + ver.version + '？发布后将成为当前生效版本。', '确认发布')
    var resp = await api.post(API.CONFIG_PUBLISH(ver.id))
    if (resp.data?.code === 0) {
      ElMessage.success('版本已发布')
      fetchVersions()
    }
  } catch { /* cancelled or error */ }
}

function openCreateVersion() {
  newVersion.content = ''
  createDialogVisible.value = true
}

async function submitVersion() {
  if (!newVersion.content.trim()) {
    ElMessage.warning('请输入配置内容')
    return
  }
  submitting.value = true
  try {
    var resp = await api.post(API.CONFIGS + '/definitions/' + selectedDefId.value + '/versions', {
      content: newVersion.content,
    })
    if (resp.data?.code === 0) {
      ElMessage.success('版本已创建')
      createDialogVisible.value = false
      fetchVersions()
    }
  } catch { ElMessage.error('创建失败') }
  finally { submitting.value = false }
}

function openDiffDialog(ver: any) {
  diffSourceVersion.value = ver.version
  diffTargetVersionId.value = ''
  diffResult.value = null
  diffDialogVisible.value = true
}

function doDiff() {
  if (!diffTargetVersionId.value) {
    ElMessage.warning('请选择对比目标版本')
    return
  }
  var sourceVer = versions.value.find(function(v) { return v.version === diffSourceVersion.value })
  var targetVer = versions.value.find(function(v) { return v.id === diffTargetVersionId.value })
  if (!sourceVer || !targetVer) return

  diffLoading.value = true
  diffTargetVersionLabel.value = targetVer.version

  setTimeout(function() {
    var sourceContent: string
    var targetContent: string
    try {
      sourceContent = JSON.stringify(JSON.parse(sourceVer.content), null, 2)
    } catch {
      sourceContent = sourceVer.content
    }
    try {
      targetContent = JSON.stringify(JSON.parse(targetVer.content), null, 2)
    } catch {
      targetContent = targetVer.content
    }
    diffResult.value = { source: sourceContent, target: targetContent }
    diffLoading.value = false
  }, 300)
}

function openRollbackDialog() {
  rollbackTargetId.value = ''
  rollbackDialogVisible.value = true
}

async function doRollback() {
  if (!rollbackTargetId.value) {
    ElMessage.warning('请选择回滚目标版本')
    return
  }
  try {
    await ElMessageBox.confirm('确认回滚？当前草稿配置将被替换为目标版本的内容。', '确认回滚')
    rollbackLoading.value = true
    var resp = await api.post(API.CONFIG_ROLLBACK(selectedDefId.value), {
      target_version_id: rollbackTargetId.value,
    })
    if (resp.data?.code === 0) {
      ElMessage.success('回滚成功')
      rollbackDialogVisible.value = false
      fetchVersions()
    }
  } catch { /* cancelled or error */ }
  finally { rollbackLoading.value = false }
}

function formatTime(t: string): string {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

function statusText(s: string): string {
  var map: Record<string, string> = { draft: '草稿', published: '已发布', archived: '已归档' }
  return map[s] || s
}

function statusTag(s: string): string {
  var map: Record<string, string> = { draft: 'info', published: 'success', archived: '' }
  return map[s] || 'info'
}

onMounted(fetchDefinitions)
</script>

<style scoped>
.mb-md { margin-bottom: var(--autops-space-lg); }
.text-tertiary { color: var(--autops-info); }
.font-12 { font-size: var(--autops-font-12); }
.empty-state { padding: 40px 0; text-align: center; }
.version-number { font-size: var(--autops-font-14); font-weight: 600; color: var(--autops-primary); }
.version-table { width: 100%; }
.diff-result h4 { margin-bottom: var(--autops-space-sm); font-size: var(--autops-font-14); color: var(--autops-text-1); }
.diff-code {
  background: var(--autops-terminal-bg);
  color: var(--autops-text-4);
  border-radius: var(--autops-radius-sm);
  padding: var(--autops-space-md);
  font-size: var(--autops-font-12);
  line-height: 1.5;
  max-height: 400px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: 'Courier New', Courier, monospace;
}
</style>
