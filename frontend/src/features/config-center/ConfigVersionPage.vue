<template>
  <div class="page-container">
    <div class="page-header">
      <h2>配置版本</h2>
    </div>

    <!-- Filter by definition -->
    <el-card class="mb-md">
      <el-row :gutter="16" align="middle">
        <el-col :span="8">
          <el-select v-model="selectedDefId" placeholder="选择配置定义" clearable @change="fetchVersions" style="width: 100%">
            <el-option v-for="d in definitions" :key="d.id" :label="d.name" :value="d.id">
              <span>{{ d.name }}</span>
              <span class="text-tertiary font-12" style="margin-left: 8px">{{ d.config_type }}</span>
            </el-option>
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" :disabled="!selectedDefId" @click="openCreateVersion">新建版本</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- Version Timeline -->
    <el-card v-loading="loading">
      <div v-if="!selectedDefId" class="empty-state">
        <el-empty description="请选择一个配置定义查看版本历史" />
      </div>
      <div v-else-if="versions.length === 0" class="empty-state">
        <el-empty description="暂无版本记录" />
      </div>
      <div v-else>
        <el-timeline>
          <el-timeline-item
            v-for="ver in versions"
            :key="ver.id"
            :timestamp="formatTime(ver.created_at)"
            :type="versionTimelineType(ver.status)"
            placement="top"
          >
            <el-card shadow="hover" class="version-card">
              <div class="version-card-header">
                <div>
                  <span class="version-number">v{{ ver.version }}</span>
                  <el-tag :type="statusTag(ver.status)" size="small" style="margin-left: 8px">
                    {{ statusText(ver.status) }}
                  </el-tag>
                </div>
                <div class="version-actions">
                  <el-button v-if="ver.status === 'draft'" text type="primary" size="small" @click="publishVersion(ver)">
                    发布
                  </el-button>
                  <el-button text type="info" size="small" @click="viewContent(ver)">查看内容</el-button>
                </div>
              </div>
              <div v-if="ver.published_by" class="version-meta">
                发布者: {{ ver.published_by?.slice(0, 8) }}... | 发布时间: {{ formatTime(ver.published_at) }}
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-card>

    <!-- View Content Dialog -->
    <el-dialog v-model="contentDialogVisible" title="配置内容" width="640px">
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const loading = ref(false)
const definitions = ref<any[]>([])
const versions = ref<any[]>([])
const selectedDefId = ref('')

async function fetchDefinitions() {
  try {
    const resp = await api.get(API.CONFIGS, { params: { page_size: 100 } })
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
    const resp = await api.get(API.CONFIG_VERSIONS(selectedDefId.value))
    if (resp.data?.code === 0) {
      versions.value = resp.data.data || []
    }
  } catch (e) {
    console.error('Failed to fetch versions:', e)
  } finally {
    loading.value = false
  }
}

const contentDialogVisible = ref(false)
const viewingContent = ref('')

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
    const resp = await api.post(API.CONFIG_PUBLISH(ver.id))
    if (resp.data?.code === 0) {
      ElMessage.success('版本已发布')
      fetchVersions()
    }
  } catch { ElMessage.error('发布失败') }
}

const createDialogVisible = ref(false)
const submitting = ref(false)
const newVersion = reactive({ content: '' })

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
    const resp = await api.post(\`\${API.CONFIGS}/definitions/\${selectedDefId.value}/versions\`, {
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

function formatTime(t: string): string {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

function statusText(s: string): string {
  const map: Record<string, string> = { draft: '草稿', published: '已发布', archived: '已归档' }
  return map[s] || s
}

function statusTag(s: string): string {
  const map: Record<string, string> = { draft: 'info', published: 'success', archived: '' }
  return map[s] || 'info'
}

function versionTimelineType(s: string): string {
  const map: Record<string, string> = { draft: 'primary', published: 'success', archived: 'info' }
  return map[s] || 'primary'
}

onMounted(fetchDefinitions)
</script>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.mb-md { margin-bottom: 16px; }
.text-tertiary { color: #86909c; }
.font-12 { font-size: 12px; }
.empty-state { padding: 40px 0; text-align: center; }
.version-card { margin-bottom: 0; }
.version-card-header { display: flex; justify-content: space-between; align-items: center; }
.version-number { font-size: 16px; font-weight: 600; }
.version-meta { font-size: 12px; color: #86909c; margin-top: 8px; }
.version-actions { display: flex; gap: 8px; }
</style>
