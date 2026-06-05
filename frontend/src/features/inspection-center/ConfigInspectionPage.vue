<template>
  <div class="autops-page-container">
    <div class="autops-page-header">
      <div class="autops-page-title">配置巡检</div>
      <div class="autops-page-desc">配置漂移、合规检查与基线对比</div>
    </div>
    <div class="autops-toolbar">
      <div class="autops-toolbar-left">
        <el-input v-model="searchQuery" placeholder="搜索名称/资产" style="width: 200px" clearable @clear="fetchItems" @keyup.enter="fetchItems">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="filterStatus" placeholder="状态" style="width: 120px" clearable @change="fetchItems">
          <el-option label="正常" value="normal" />
          <el-option label="异常" value="abnormal" />
          <el-option label="未执行" value="pending" />
        </el-select>
        <el-select v-model="filterType" placeholder="检查类型" style="width: 140px" clearable @change="fetchItems">
          <el-option label="配置漂移" value="drift" />
          <el-option label="合规检查" value="compliance" />
          <el-option label="基线对比" value="baseline" />
        </el-select>
      </div>
      <div class="autops-toolbar-right">
        <el-button type="primary" :loading="runLoading" @click="handleRunInspection">
          <el-icon><VideoPlay /></el-icon> 执行巡检
        </el-button>
      </div>
    </div>

    <div class="autops-card">
      <el-table stripe :data="filteredItems" v-loading="loading"class="autops-table" @sort-change="handleSortChange">
        <el-table-column type="selection" width="45" />
        <el-table-column prop="name" label="巡检项名称" min-width="160" sortable="custom" show-overflow-tooltip />
        <el-table-column prop="asset_name" label="目标资产" min-width="140" show-overflow-tooltip />
        <el-table-column prop="config_path" label="配置路径" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <el-text type="info" size="small" family="monospace">{{ row.config_path || '-' }}</el-text>
          </template>
        </el-table-column>
        <el-table-column prop="check_type" label="检查类型" width="120">
          <template #default="{ row }">
            <el-tag :type="checkTypeTag(row.check_type)" size="small">{{ checkTypeLabel(row.check_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_checked_at" label="最后检查" width="170" sortable="custom">
          <template #default="{ row }">
            {{ formatTime(row.last_checked_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="result_summary" label="结果摘要" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.status === 'abnormal'" class="text-danger">{{ row.result_summary || '存在差异' }}</span>
            <span v-else-if="row.status === 'normal'" class="text-success">{{ row.result_summary || '配置一致' }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button plain type="primary" @click="showDetail(row)">详情</el-button>
            <el-button plain type="warning" @click="runSingle(row)" :loading="row._running">执行</el-button>
            <el-button plain type="danger" v-if="row.status === 'abnormal'" @click="createAnomaly(row)">报异常</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="mt-lg" style="display: flex; justify-content: flex-end">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchItems"
          @current-change="fetchItems"
        />
      </div>
    </div>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="配置巡检详情" width="780px" destroy-on-close>
      <el-descriptions :column="2" border v-if="currentItem">
        <el-descriptions-item label="巡检项名称">{{ currentItem.name }}</el-descriptions-item>
        <el-descriptions-item label="目标资产">{{ currentItem.asset_name }}</el-descriptions-item>
        <el-descriptions-item label="配置路径" :span="2">
          <el-text family="monospace">{{ currentItem.config_path }}</el-text>
        </el-descriptions-item>
        <el-descriptions-item label="检查类型">{{ checkTypeLabel(currentItem.check_type) }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTag(currentItem.status)">{{ statusLabel(currentItem.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="最后检查">{{ formatTime(currentItem.last_checked_at) }}</el-descriptions-item>
        <el-descriptions-item label="基线版本">{{ currentItem.baseline_version || '-' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 配置差异展示 -->
      <div v-if="currentItem?.diff_content" class="mt-lg">
        <h4>配置差异</h4>
        <div class="diff-content">
          <pre style="background: #1e1e1e; color: #c9cdd4; padding: 12px; border-radius: 4px; font-size: 12px; max-height: 300px; overflow: auto">{{ currentItem.diff_content }}</pre>
        </div>
      </div>

      <div v-if="currentItem?.result_summary" class="mt-lg">
        <h4>结果摘要</h4>
        <el-alert :type="currentItem.status === 'normal' ? 'success' : 'error'" :closable="false" show-icon>
          {{ currentItem.result_summary }}
        </el-alert>
      </div>

      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="runSingle(currentItem)">重新检查</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Search, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'
import { useRouter } from 'vue-router'

const router = useRouter()

// ─── State ───
const loading = ref(false)
const runLoading = ref(false)
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const filterStatus = ref('')
const filterType = ref('')
const sortField = ref('last_checked_at')
const sortOrder = ref('desc')
const detailVisible = ref(false)
const currentItem = ref<any>(null)

// ─── Computed ───
const filteredItems = computed(() => {
  let list = items.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(i => (i.name || '').toLowerCase().includes(q) || (i.asset_name || '').toLowerCase().includes(q))
  }
  if (filterStatus.value) {
    list = list.filter(i => i.status === filterStatus.value)
  }
  if (filterType.value) {
    list = list.filter(i => i.check_type === filterType.value)
  }
  return list
})

// ─── API ───
async function fetchItems() {
  loading.value = true
  try {
    const params: any = {
      page: page.value,
      page_size: pageSize.value,
      type: 'config',
    }
    if (sortField.value) params.sort_by = sortField.value
    if (sortOrder.value) params.sort_order = sortOrder.value
    const res = await api.get(API.INSPECTION_TEMPLATES, { params })
    const data = res.data
    if (data?.code === 0) {
      items.value = (data.data?.items || []).map((i: any) => ({ ...i, _running: false }))
      total.value = data.data?.total || 0
    }
  } catch (e) {
    console.error('Fetch config inspection items error:', e)
    ElMessage.error('获取配置巡检列表失败')
  } finally {
    loading.value = false
  }
}

async function handleRunInspection() {
  runLoading.value = true
  try {
    await api.post(API.INSPECTION_TASKS, { type: 'config', template_ids: filteredItems.value.filter(i => i.id).map(i => i.id) })
    ElMessage.success('配置巡检任务已创建')
    setTimeout(fetchItems, 2000)
  } catch (e) {
    ElMessage.error('执行巡检失败')
  } finally {
    runLoading.value = false
  }
}

async function runSingle(item: any) {
  item._running = true
  try {
    await api.post(API.INSPECTION_TASKS, { type: 'config', template_id: item.id })
    ElMessage.success('巡检项 ' + item.name + ' 已触发')
    setTimeout(fetchItems, 2000)
  } catch (e) {
    ElMessage.error('执行失败')
  } finally {
    item._running = false
  }
}

function createAnomaly(item: any) {
  router.push({ path: '/response/anomalies', query: { from: 'inspection', item_id: item.id } })
}

function showDetail(item: any) {
  currentItem.value = item
  detailVisible.value = true
}

function handleSortChange({ prop, order }: any) {
  sortField.value = prop || 'last_checked_at'
  sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  fetchItems()
}

// ─── Helpers ───
function checkTypeLabel(t: string) {
  const map: Record<string, string> = { drift: '配置漂移', compliance: '合规检查', baseline: '基线对比' }
  return map[t] || t || '-'
}
function checkTypeTag(t: string) {
  const map: Record<string, string> = { drift: 'warning', compliance: '', baseline: 'info' }
  return map[t] || 'info'
}
function statusLabel(s: string) {
  const map: Record<string, string> = { normal: '正常', abnormal: '异常', pending: '未执行' }
  return map[s] || s || '-'
}
function statusTag(s: string) {
  const map: Record<string, string> = { normal: 'success', abnormal: 'danger', pending: 'info' }
  return map[s] || 'info'
}
function formatTime(t: string) {
  return t ? new Date(t).toLocaleString('zh-CN') : '-'
}

onMounted(fetchItems)
</script>

<style scoped>

.diff-content { border-radius: var(--autops-radius-sm); overflow: hidden; }


.text-muted { color: var(--autops-info); }
</style>
