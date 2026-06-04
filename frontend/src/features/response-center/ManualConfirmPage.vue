<template>
  <div class="manual-confirm-page">
    <div class="autops-page-header">
      <div class="autops-page-title-row">
        <el-button plain @click="router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <span class="autops-page-title">人工确认台</span>
      </div>
      <div class="autops-page-desc">审核和确认自动处置、AI建议和策略触发的操作</div>
    </div>
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px">
      <el-badge :value="pendingCount" :max="99">
        <el-tag type="danger">待确认</el-tag>
      </el-badge>
      <el-button @click="loadData" :loading="loading">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <!-- 筛选 -->
    <el-card class="mt-4" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" @change="loadData">
            <el-option label="待确认" value="pending" />
            <el-option label="已确认" value="confirmed" />
            <el-option label="已拒绝" value="rejected" />
            <el-option label="已超时" value="timeout" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="filters.source" placeholder="全部" clearable @change="loadData">
            <el-option label="自动处置" value="automation" />
            <el-option label="AI建议" value="ai" />
            <el-option label="策略触发" value="policy" />
          </el-select>
        </el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="filters.risk" placeholder="全部" clearable @change="loadData">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 确认列表 -->
    <el-card class="mt-4" shadow="never">
      <el-table stripe :data="items" v-loading="loading"border>
        <el-table-column prop="title" label="确认事项" min-width="250">
          <template #default="{ row }">
            <div class="confirm-title">
              <el-tag v-if="row.status === 'pending'" type="danger" size="small" class="mr-1">待确认</el-tag>
              <span>{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="110">
          <template #default="{ row }">
            <el-tag :type="sourceType(row.source)" size="small">{{ sourceName(row.source) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险" width="80">
          <template #default="{ row }">
            <el-tag :type="riskType(row.risk_level)" size="small">{{ row.risk_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="asset_name" label="关联资产" width="140" />
        <el-table-column prop="action_summary" label="执行动作摘要" min-width="200" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column prop="timeout_at" label="超时时间" width="180" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button plain type="primary" @click="viewDetail(row)">详情</el-button>
              <el-button plain type="success" @click="handleConfirm(row)">确认执行</el-button>
              <el-button plain type="danger" @click="handleReject(row)">拒绝</el-button>
            </template>
            <template v-else>
              <el-button plain type="primary" @click="viewDetail(row)">查看</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="mt-4" v-model:current-page="pagination.page" v-model:page-size="pagination.size"
        :total="pagination.total" :page-sizes="[20, 50, 100]" layout="total, sizes, prev, pager, next"
        @size-change="loadData" @current-change="loadData" />
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="确认事项详情" width="780px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="标题" :span="2">{{ detailData.title }}</el-descriptions-item>
        <el-descriptions-item label="来源">{{ sourceName(detailData.source) }}</el-descriptions-item>
        <el-descriptions-item label="风险等级">{{ detailData.risk_level }}</el-descriptions-item>
        <el-descriptions-item label="关联资产">{{ detailData.asset_name }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detailData.created_at }}</el-descriptions-item>
        <el-descriptions-item label="执行动作" :span="2">
          <pre class="action-pre">{{ detailData.action_detail }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="AI分析" :span="2" v-if="detailData.ai_analysis">
          <div class="ai-analysis">{{ detailData.ai_analysis }}</div>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer v-if="detailData.status === 'pending'">
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="danger" @click="handleReject(detailData); detailVisible = false">拒绝</el-button>
        <el-button type="primary" @click="handleConfirm(detailData); detailVisible = false">确认执行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, ArrowLeft } from '@element-plus/icons-vue'
import client from '@/shared/api/client'

const router = useRouter()
const loading = ref(false)
const detailVisible = ref(false)
const items = ref<any[]>([])
const detailData = ref<any>({})

const filters = reactive({ status: 'pending', source: '', risk: '' })
const pagination = reactive({ page: 1, size: 20, total: 0 })

const pendingCount = computed(() => items.value.filter(i => i.status === 'pending').length)

const sourceMap: Record<string, string> = { automation: '自动处置', ai: 'AI建议', policy: '策略触发' }
function sourceName(s: string) { return sourceMap[s] || s }
function sourceType(s: string) { return { automation: 'warning', ai: 'success', policy: 'primary' }[s] || 'info' }
function riskType(r: string) { return { high: 'danger', medium: 'warning', low: 'info' }[r] || 'info' }

async function loadData() {
  loading.value = true
  try {
    const res = await client.get('/api/v1/automation/approvals', { params: { status: filters.status, page: pagination.page, page_size: pagination.size } })
    const data = res.data?.data ?? res.data
    items.value = data?.items || []
    pagination.total = data?.total || 0
  } catch { items.value = [] } finally { loading.value = false }
}

function viewDetail(row: any) { detailData.value = row; detailVisible.value = true }

async function handleConfirm(row: any) {
  try {
    await ElMessageBox.confirm('确认执行该操作？执行后不可撤销。', '确认执行', { type: 'warning' })
    await client.post('/api/v1/automation/approvals/' + row.id + '/approve')
    ElMessage.success('已确认执行')
    loadData()
  } catch { /* cancelled */ }
}

async function handleReject(row: any) {
  try {
    const { value } = await ElMessageBox.prompt('请输入拒绝原因', '拒绝确认', { type: 'warning', inputPlaceholder: '拒绝原因' })
    await client.post('/api/v1/automation/approvals/' + row.id + '/reject', { reason: value })
    ElMessage.success('已拒绝')
    loadData()
  } catch { /* cancelled */ }
}

onMounted(loadData)
</script>

<style scoped>
.manual-confirm-page { padding: 20px; }
.mt-4 { margin-top: 16px; }
.mr-1 { margin-right: 4px; }
.mr-4 { margin-right: 16px; }
.confirm-title { display: flex; align-items: center; }
.action-pre { background: #f7f8fa; padding: 8px; border-radius: 4px; font-size: 13px; white-space: pre-wrap; }
.ai-analysis { background: #ecf5ff; padding: 8px; border-radius: 4px; font-size: 13px; }
</style>
