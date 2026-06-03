<template>
  <div class="page-container">
    <div class="autops-page-header">
      <h2>AI 诊断面板</h2>
    </div>

    <!-- 诊断输入 -->
    <el-card style="margin-bottom: 16px">
      <template #header><span>发起诊断</span></template>
      <el-form :inline="true">
        <el-form-item label="异常ID">
          <el-input v-model="anomalyId" placeholder="输入异常ID" style="width: 300px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="startDiagnosis" :loading="diagnosing" :disabled="!anomalyId">
            开始诊断
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 诊断结果 -->
    <el-card v-if="diagnosisResult" style="margin-bottom: 16px">
      <template #header><span>诊断结果</span></template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="异常ID">{{ diagnosisResult.anomaly_id ?? anomalyId }}</el-descriptions-item>
        <el-descriptions-item label="置信度">
          <el-progress :percentage="diagnosisResult.confidence ?? 0" :color="confidenceColor(diagnosisResult.confidence)" />
        </el-descriptions-item>
        <el-descriptions-item label="根因分析" :span="2">
          <div style="white-space: pre-wrap">{{ diagnosisResult.root_cause ?? diagnosisResult.analysis ?? '-' }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="建议动作" :span="2">
          <div v-if="diagnosisResult.suggestions?.length">
            <div v-for="(s, i) in diagnosisResult.suggestions" :key="i" style="margin-bottom: 8px">
              <el-tag size="small" style="margin-right: 8px">{{ s.risk_level ?? 'medium' }}</el-tag>
              {{ s.action ?? s.description ?? s }}
            </div>
          </div>
          <span v-else>{{ diagnosisResult.recommended_actions ?? '-' }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 历史分析记录 -->
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>历史诊断记录</span>
          <el-button @click="fetchHistory" :icon="Refresh" size="small">刷新</el-button>
        </div>
      </template>
      <el-table :data="historyList" v-loading="historyLoading" stripe>
        <el-table-column prop="id" label="ID" width="100" show-overflow-tooltip />
        <el-table-column label="异常" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.anomaly_id ?? row.target_id ?? row.title ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="根因摘要" min-width="250" show-overflow-tooltip>
          <template #default="{ row }">{{ row.root_cause ?? row.analysis ?? row.summary ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="置信度" width="120">
          <template #default="{ row }">
            <el-progress :percentage="row.confidence ?? 0" :stroke-width="10" :color="confidenceColor(row.confidence)" />
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="statusType(row.status)">{{ row.status ?? '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewAnalysis(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="display:flex;justify-content:flex-end;margin-top:16px">
        <el-pagination v-model:current-page="page" v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]" :total="total" layout="total, sizes, prev, pager, next"
          @size-change="fetchHistory" @current-change="fetchHistory" />
      </div>
    </el-card>

    <!-- 分析详情抽屉 -->
    <el-drawer v-model="drawerVisible" title="诊断详情" size="600px">
      <template v-if="detailData">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="ID">{{ detailData.id }}</el-descriptions-item>
          <el-descriptions-item label="异常ID">{{ detailData.anomaly_id ?? detailData.target_id ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="置信度">
            <el-progress :percentage="detailData.confidence ?? 0" :color="confidenceColor(detailData.confidence)" />
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusType(detailData.status)">{{ detailData.status ?? '-' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTime(detailData.created_at) }}</el-descriptions-item>
        </el-descriptions>
        <div style="margin-top: 20px">
          <h4>根因分析</h4>
          <div style="white-space: pre-wrap; background: #f5f7fa; padding: 16px; border-radius: 4px; margin-top: 8px">
            {{ detailData.root_cause ?? detailData.analysis ?? detailData.summary ?? '暂无分析结果' }}
          </div>
        </div>
        <div v-if="detailData.suggestions?.length" style="margin-top: 20px">
          <h4>建议动作</h4>
          <el-table :data="detailData.suggestions" size="small" style="margin-top: 8px">
            <el-table-column prop="action" label="动作" min-width="200" />
            <el-table-column prop="risk_level" label="风险" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="{high:'danger',medium:'warning',low:'info'}[row.risk_level]||'info'">{{ row.risk_level }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { aiopsService } from '@/shared/api'

const anomalyId = ref('')
const diagnosing = ref(false)
const diagnosisResult = ref<any>(null)

const historyLoading = ref(false)
const historyList = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const drawerVisible = ref(false)
const detailData = ref<any>(null)

function confidenceColor(c: number | undefined) {
  if (!c) return '#909399'
  if (c >= 80) return '#67c23a'
  if (c >= 50) return '#e6a23c'
  return '#f56c6c'
}
function statusType(s: string) {
  return { completed: 'success', running: 'warning', failed: 'danger', pending: 'info' }[s] || 'info'
}
function formatTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

async function startDiagnosis() {
  if (!anomalyId.value) return
  diagnosing.value = true
  try {
    const res = await aiopsService.diagnose({ anomaly_id: anomalyId.value })
    const d = res.data?.data ?? res.data
    diagnosisResult.value = d
    ElMessage.success('诊断完成')
    fetchHistory()
  } catch { ElMessage.error('诊断失败') }
  finally { diagnosing.value = false }
}

async function fetchHistory() {
  historyLoading.value = true
  try {
    const res = await aiopsService.listAnalyses({ page: page.value, page_size: pageSize.value })
    const d = res.data?.data ?? res.data
    historyList.value = d?.items ?? d?.results ?? d?.list ?? (Array.isArray(d) ? d : [])
    total.value = d?.total ?? historyList.value.length
  } catch { ElMessage.error('获取历史记录失败') }
  finally { historyLoading.value = false }
}

async function viewAnalysis(row: any) {
  try {
    const res = await aiopsService.getAnalysis(row.id)
    detailData.value = res.data?.data ?? res.data ?? row
    drawerVisible.value = true
  } catch { detailData.value = row; drawerVisible.value = true }
}

onMounted(fetchHistory)
</script>
