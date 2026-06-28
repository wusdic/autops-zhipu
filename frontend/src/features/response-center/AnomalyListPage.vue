<template>
  <div class="p-6">
    <div class="autops-page-header" v-if="!embedded">
      <div class="autops-page-title">异常列表</div>
      <el-button type="primary" @click="router.push('/response/anomalies/create')">新建异常</el-button>
    </div>

    <!-- 搜索 / 过滤 -->
    <div class="autops-card mb-lg">
      <div class="autops-card-body">
        <el-form :inline="true" @submit.prevent="fetchList">
          <el-form-item label="搜索">
            <el-input v-model="searchKeyword" placeholder="异常标题 / 描述" clearable style="width: 220px" @clear="fetchList" />
          </el-form-item>
          <el-form-item label="严重级别">
            <el-select v-model="filterSeverity" placeholder="全部" clearable style="width: 130px" @change="fetchList">
              <el-option label="严重" value="critical" />
              <el-option label="高" value="high" />
              <el-option label="中" value="medium" />
              <el-option label="低" value="low" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="filterStatus" placeholder="全部" clearable style="width: 130px" @change="fetchList">
              <el-option label="新建" value="open" />
              <el-option label="已确认" value="acknowledged" />
              <el-option label="已分配" value="assigned" />
              <el-option label="已关闭" value="closed" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="fetchList">查询</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 表格 -->
    <div class="autops-card">
      <div class="autops-card-body p-0">
        <el-table stripe :data="anomalies"v-loading="loading" empty-text="暂无异常数据">
          <el-table-column prop="title" label="异常标题" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              <el-link type="primary" @click="router.push('/response/anomalies/' + row.id)">
                {{ row.title }}
              </el-link>
            </template>
          </el-table-column>
          <el-table-column prop="severity" label="严重级别" width="100">
            <template #default="{ row }">
              <el-tag :type="(severityType(row.severity)) as TagType" size="small">
                {{ severityLabel(row.severity) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="asset_name" label="关联资产" width="150" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.asset_name || row.asset_id || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="source" label="来源" width="100">
            <template #default="{ row }">
              <el-tag size="small" type="info">{{ row.source || '-' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="(statusType(row.status)) as TagType" size="small">
                {{ statusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="assignee_name" label="负责人" width="100">
            <template #default="{ row }">
              {{ row.assignee_name || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="discovered_at" label="发现时间" width="170">
            <template #default="{ row }">
              <span class="text-tertiary">{{ row.discovered_at || row.created_at || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button plain type="primary" size="small" @click="router.push('/response/anomalies/' + row.id)">
                详情
              </el-button>
              <el-button
                v-if="row.status === 'open'"
                plain type="success" size="small"
                :loading="actionMap[row.id] === 'ack'"
                @click="handleAcknowledge(row)"
              >
                确认
              </el-button>
              <el-button
                v-if="row.status !== 'closed'"
                plain type="warning" size="small"
                :loading="actionMap[row.id] === 'close'"
                @click="handleClose(row)"
              >
                关闭
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div style="padding: 12px; display: flex; justify-content: flex-end">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="fetchList"
          @size-change="fetchList"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'

defineProps<{ embedded?: boolean }>()
import { ElMessage, ElMessageBox } from 'element-plus'
import { anomalyService } from '@/shared/api'

const router = useRouter()

const loading = ref(false)
const anomalies = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const filterSeverity = ref('')
const filterStatus = ref('')
const actionMap = reactive<Record<string, string>>({})

// Severity helpers
const severityMap: Record<string, string> = { critical: '严重', high: '高', medium: '中', low: '低' }
const severityLabel = (s: string) => severityMap[s] || s
const severityType = (s: string): '' | 'success' | 'warning' | 'danger' | 'info' =>
  ({ critical: 'danger', high: 'warning', medium: 'primary', low: 'info' } as any)[s] || 'info'

// Status helpers
const statusMap: Record<string, string> = { open: '新建', acknowledged: '已确认', assigned: '已分配', closed: '已关闭' }
const statusLabel = (s: string) => statusMap[s] || s
const statusType = (s: string): '' | 'success' | 'warning' | 'danger' | 'info' =>
  ({ open: 'danger', acknowledged: 'warning', assigned: 'primary', closed: 'success' } as any)[s] || 'info'

async function fetchList() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: page.value,
      page_size: pageSize.value,
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (filterSeverity.value) params.severity = filterSeverity.value
    if (filterStatus.value) params.status = filterStatus.value

    const res = await anomalyService.list(params)
    const data = res.data?.data || res.data
    anomalies.value = data?.items || data || []
    total.value = data?.total || anomalies.value.length
  } catch (e: any) {
    ElMessage.error(e.message || '获取异常列表失败')
  } finally {
    loading.value = false
  }
}

function resetFilter() {
  searchKeyword.value = ''
  filterSeverity.value = ''
  filterStatus.value = ''
  page.value = 1
  fetchList()
}

async function handleAcknowledge(row: any) {
  try {
    await ElMessageBox.confirm('确认异常「' + row.title + '」？', '确认操作')
    actionMap[row.id] = 'ack'
    await anomalyService.acknowledge(row.id)
    ElMessage.success('已确认')
    await fetchList()
  } catch (e: any) {
    if (e !== 'cancel' && e?.action !== 'cancel' && e?.message !== 'cancel') ElMessage.error(e.message || '操作失败')
  } finally {
    actionMap[row.id] = ''
  }
}

async function handleClose(row: any) {
  try {
    const { value } = await ElMessageBox.prompt('请输入关闭原因', '关闭异常', {
      inputPattern: /.+/,
      inputErrorMessage: '请输入关闭原因',
    })
    actionMap[row.id] = 'close'
    await anomalyService.close(row.id, { reason: value })
    ElMessage.success('已关闭')
    await fetchList()
  } catch (e: any) {
    if (e !== 'cancel' && e?.action !== 'cancel' && e?.message !== 'cancel') ElMessage.error(e.message || '操作失败')
  } finally {
    actionMap[row.id] = ''
  }
}

onMounted(() => fetchList())
</script>

<style scoped>

.text-tertiary {
  color: var(--autops-info);
  font-size: var(--autops-font-12);
}
</style>
