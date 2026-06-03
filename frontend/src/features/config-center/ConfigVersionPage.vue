     1|<template>
     2|  <div class="page-container">
     3|    <div class="autops-page-header">
     4|      <div class="autops-page-title">配置版本</div>
     5|    </div>
     6|
     7|    <!-- Filter by definition -->
     8|    <el-card class="mb-md">
     9|      <el-row :gutter="16" align="middle">
    10|        <el-col :span="8">
    11|          <el-select v-model="selectedDefId" placeholder="选择配置定义" clearable @change="fetchVersions" style="width: 100%">
    12|            <el-option v-for="d in definitions" :key="d.id" :label="d.name" :value="d.id">
    13|              <span>{{ d.name }}</span>
    14|              <span class="text-tertiary font-12" style="margin-left: 8px">{{ d.config_type }}</span>
    15|            </el-option>
    16|          </el-select>
    17|        </el-col>
    18|        <el-col :span="4">
    19|          <el-button type="primary" :disabled="!selectedDefId" @click="openCreateVersion">新建版本</el-button>
    20|        </el-col>
    21|      </el-row>
    22|    </el-card>
    23|
    24|    <!-- Version Timeline -->
    25|    <el-card v-loading="loading">
    26|      <div v-if="!selectedDefId" class="empty-state">
    27|        <el-empty description="请选择一个配置定义查看版本历史" />
    28|      </div>
    29|      <div v-else-if="versions.length === 0" class="empty-state">
    30|        <el-empty description="暂无版本记录" />
    31|      </div>
    32|      <div v-else>
    33|        <el-timeline>
    34|          <el-timeline-item
    35|            v-for="ver in versions"
    36|            :key="ver.id"
    37|            :timestamp="formatTime(ver.created_at)"
    38|            :type="versionTimelineType(ver.status)"
    39|            placement="top"
    40|          >
    41|            <el-card shadow="hover" class="version-card">
    42|              <div class="version-card-header">
    43|                <div>
    44|                  <span class="version-number">v{{ ver.version }}</span>
    45|                  <el-tag :type="statusTag(ver.status)" size="small" style="margin-left: 8px">
    46|                    {{ statusText(ver.status) }}
    47|                  </el-tag>
    48|                </div>
    49|                <div class="version-actions">
    50|                  <el-button v-if="ver.status === 'draft'" text type="primary" size="small" @click="publishVersion(ver)">
    51|                    发布
    52|                  </el-button>
    53|                  <el-button text type="info" size="small" @click="viewContent(ver)">查看内容</el-button>
    54|                </div>
    55|              </div>
    56|              <div v-if="ver.published_by" class="version-meta">
    57|                发布者: {{ ver.published_by?.slice(0, 8) }}... | 发布时间: {{ formatTime(ver.published_at) }}
    58|              </div>
    59|            </el-card>
    60|          </el-timeline-item>
    61|        </el-timeline>
    62|      </div>
    63|    </el-card>
    64|
    65|    <!-- View Content Dialog -->
    66|    <el-dialog v-model="contentDialogVisible" title="配置内容" width="600px">
    67|      <el-input type="textarea" :model-value="viewingContent" :rows="18" readonly style="font-family: monospace" />
    68|    </el-dialog>
    69|
    70|    <!-- Create Version Dialog -->
    71|    <el-dialog v-model="createDialogVisible" title="新建配置版本" width="600px" destroy-on-close>
    72|      <el-form :model="newVersion" label-width="100px">
    73|        <el-form-item label="配置内容" required>
    74|          <el-input v-model="newVersion.content" type="textarea" :rows="12" placeholder="输入JSON/YAML配置内容" style="font-family: monospace" />
    75|        </el-form-item>
    76|      </el-form>
    77|      <template #footer>
    78|        <el-button @click="createDialogVisible = false">取消</el-button>
    79|        <el-button type="primary" :loading="submitting" @click="submitVersion">创建</el-button>
    80|      </template>
    81|    </el-dialog>
    82|  </div>
    83|</template>
    84|
    85|<script setup lang="ts">
    86|import { ref, reactive, onMounted } from 'vue'
    87|import { ElMessage } from 'element-plus'
    88|import api from '@/shared/api/client'
    89|import { API } from '@/shared/api/routes'
    90|
    91|const loading = ref(false)
    92|const definitions = ref<any[]>([])
    93|const versions = ref<any[]>([])
    94|const selectedDefId = ref('')
    95|
    96|async function fetchDefinitions() {
    97|  try {
    98|    const resp = await api.get(API.CONFIGS, { params: { page_size: 100 } })
    99|    if (resp.data?.code === 0) {
   100|      definitions.value = resp.data.data?.items || []
   101|    }
   102|  } catch (e) {
   103|    console.error('Failed to fetch definitions:', e)
   104|  }
   105|}
   106|
   107|async function fetchVersions() {
   108|  if (!selectedDefId.value) {
   109|    versions.value = []
   110|    return
   111|  }
   112|  loading.value = true
   113|  try {
   114|    const resp = await api.get(API.CONFIG_VERSIONS(selectedDefId.value))
   115|    if (resp.data?.code === 0) {
   116|      versions.value = resp.data.data || []
   117|    }
   118|  } catch (e) {
   119|    console.error('Failed to fetch versions:', e)
   120|  } finally {
   121|    loading.value = false
   122|  }
   123|}
   124|
   125|const contentDialogVisible = ref(false)
   126|const viewingContent = ref('')
   127|
   128|function viewContent(ver: any) {
   129|  try {
   130|    viewingContent.value = JSON.stringify(JSON.parse(ver.content), null, 2)
   131|  } catch {
   132|    viewingContent.value = ver.content
   133|  }
   134|  contentDialogVisible.value = true
   135|}
   136|
   137|async function publishVersion(ver: any) {
   138|  try {
   139|    const resp = await api.post(API.CONFIG_PUBLISH(ver.id))
   140|    if (resp.data?.code === 0) {
   141|      ElMessage.success('版本已发布')
   142|      fetchVersions()
   143|    }
   144|  } catch { ElMessage.error('发布失败') }
   145|}
   146|
   147|const createDialogVisible = ref(false)
   148|const submitting = ref(false)
   149|const newVersion = reactive({ content: '' })
   150|
   151|function openCreateVersion() {
   152|  newVersion.content = ''
   153|  createDialogVisible.value = true
   154|}
   155|
   156|async function submitVersion() {
   157|  if (!newVersion.content.trim()) {
   158|    ElMessage.warning('请输入配置内容')
   159|    return
   160|  }
   161|  submitting.value = true
   162|  try {
   163|    const resp = await api.post(API.CONFIGS + '/definitions/' + selectedDefId.value + '/versions', {
   164|      content: newVersion.content,
   165|    })
   166|    if (resp.data?.code === 0) {
   167|      ElMessage.success('版本已创建')
   168|      createDialogVisible.value = false
   169|      fetchVersions()
   170|    }
   171|  } catch { ElMessage.error('创建失败') }
   172|  finally { submitting.value = false }
   173|}
   174|
   175|function formatTime(t: string): string {
   176|  if (!t) return ''
   177|  return new Date(t).toLocaleString('zh-CN')
   178|}
   179|
   180|function statusText(s: string): string {
   181|  const map: Record<string, string> = { draft: '草稿', published: '已发布', archived: '已归档' }
   182|  return map[s] || s
   183|}
   184|
   185|function statusTag(s: string): string {
   186|  const map: Record<string, string> = { draft: 'info', published: 'success', archived: '' }
   187|  return map[s] || 'info'
   188|}
   189|
   190|function versionTimelineType(s: string): string {
   191|  const map: Record<string, string> = { draft: 'primary', published: 'success', archived: 'info' }
   192|  return map[s] || 'primary'
   193|}
   194|
   195|onMounted(fetchDefinitions)
   196|</script>
   197|
   198|<style scoped>
   199|
   200|.mb-md { margin-bottom: 16px; }
   201|.text-tertiary { color: #86909c; }
   202|.font-12 { font-size: 12px; }
   203|.empty-state { padding: 40px 0; text-align: center; }
   204|.version-card { margin-bottom: 0; }
   205|.version-card-header { display: flex; justify-content: space-between; align-items: center; }
   206|.version-number { font-size: 16px; font-weight: 600; }
   207|.version-meta { font-size: 12px; color: #86909c; margin-top: 8px; }
   208|.version-actions { display: flex; gap: 8px; }
   209|</style>
   210|