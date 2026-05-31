<template>
  <div class="alert-detail">
    <!-- 顶部返回按钮 + 告警标题 -->
    <div class="detail-header">
      <el-button :icon="ArrowLeft" @click="$router.back()">返回</el-button>
      <div class="detail-title-area">
        <SeverityBadge v-if="alert" :severity="alert.severity" size="large" />
        <h2 style="margin: 0 0 0 12px">{{ alert?.title || '告警详情' }}</h2>
        <StatusBadge v-if="alert" :status="alert.status" show-icon style="margin-left: 12px" />
      </div>
    </div>

    <div v-loading="loading" style="margin-top: 16px">
      <template v-if="alert">
        <el-tabs v-model="activeTab" type="border-card">
          <!-- 告警信息 -->
          <el-tab-pane label="告警信息" name="info">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="告警ID">{{ alert.id }}</el-descriptions-item>
              <el-descriptions-item label="严重级别">
                <SeverityBadge :severity="alert.severity" />
              </el-descriptions-item>
              <el-descriptions-item label="状态">
                <StatusBadge :status="alert.status" show-icon />
              </el-descriptions-item>
              <el-descriptions-item label="来源">{{ alert.source || '-' }}</el-descriptions-item>
              <el-descriptions-item label="触发时间">{{ formatTime(alert.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="确认时间">{{ formatTime(alert.acknowledged_at) }}</el-descriptions-item>
              <el-descriptions-item label="恢复时间">{{ formatTime(alert.resolved_at) }}</el-descriptions-item>
              <el-descriptions-item label="更新时间">{{ formatTime(alert.updated_at) }}</el-descriptions-item>
              <el-descriptions-item label="告警描述" :span="2">
                {{ alert.description || alert.message || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="标签" :span="2">
                <template v-if="alert.labels && Object.keys(alert.labels).length">
                  <el-tag v-for="(v, k) in alert.labels" :key="k" size="small" style="margin: 2px 4px">
                    {{ k }}={{ v }}
                  </el-tag>
                </template>
                <span v-else>-</span>
              </el-descriptions-item>
            </el-descriptions>
            <div v-if="alert.annotations" style="margin-top: 16px">
              <h4>注解</h4>
              <el-input type="textarea" :rows="4" :model-value="formatJson(alert.annotations)" readonly />
            </div>
            <!-- 操作按钮 -->
            <div style="margin-top: 16px; display: flex; gap: 8px">
              <el-button v-if="alert.status === 'firing'" type="warning" @click="ackAlert">确认告警</el-button>
              <el-button v-if="alert.status !== 'resolved'" type="success" @click="resolveAlert">恢复告警</el-button>
            </div>
          </el-tab-pane>

          <!-- 关联资产 -->
          <el-tab-pane label="关联资产" name="assets">
            <el-table :data="relatedAssets" stripe>
              <el-table-column prop="hostname" label="主机名" min-width="140" show-overflow-tooltip />
              <el-table-column prop="ip" label="IP 地址" width="150" />
              <el-table-column prop="asset_type" label="类型" width="120" />
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <StatusBadge :status="row.status" size="small" show-icon />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80">
                <template #default="{ row }">
                  <el-button text type="primary" size="small" @click="$router.push(`/assets/${row.id}`)">详情</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!relatedAssets.length" description="暂无关联资产" />
          </el-tab-pane>

          <!-- 事件时间线 -->
          <el-tab-pane label="事件时间线" name="timeline">
            <div v-loading="timelineLoading">
              <TimelineView :items="timelineItems" />
            </div>
          </el-tab-pane>

          <!-- AI 分析结果 -->
          <el-tab-pane label="AI 分析" name="ai">
            <div v-loading="aiLoading">
              <AiAnalysisCard
                v-if="aiAnalysis"
                :root-cause="aiAnalysis.root_cause"
                :recommendations="aiAnalysis.recommendations"
                :confidence="aiAnalysis.confidence"
                :summary="aiAnalysis.summary"
              />
              <el-empty v-if="!aiLoading && !aiAnalysis" description="暂无 AI 分析结果" />
            </div>
          </el-tab-pane>

          <!-- 执行历史 -->
          <el-tab-pane label="执行历史" name="executions">
            <el-table :data="executions" stripe>
              <el-table-column prop="id" label="执行ID" width="200" show-overflow-tooltip />
              <el-table-column prop="playbook_name" label="Playbook" min-width="160" show-overflow-tooltip />
              <el-table-column label="状态" width="110">
                <template #default="{ row }">
                  <StatusBadge :status="row.status" size="small" show-icon />
                </template>
              </el-table-column>
              <el-table-column prop="started_at" label="开始时间" width="180">
                <template #default="{ row }">{{ formatTime(row.started_at) }}</template>
              </el-table-column>
              <el-table-column prop="finished_at" label="结束时间" width="180">
                <template #default="{ row }">{{ formatTime(row.finished_at) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="80">
                <template #default="{ row }">
                  <el-button text type="primary" size="small" @click="$router.push(`/executions/${row.id}`)">详情</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!executions.length" description="暂无执行历史" />
          </el-tab-pane>
        </el-tabs>
      </template>

      <el-empty v-if="!loading && !alert" description="告警不存在或已被删除">
        <el-button type="primary" @click="$router.back()">返回列表</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import SeverityBadge from '@/shared/components/SeverityBadge.vue'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import TimelineView from '@/shared/components/TimelineView.vue'
import AiAnalysisCard from '@/shared/components/AiAnalysisCard.vue'

const route = useRoute()
const alertId = () => route.params.id as string

const loading = ref(false)
const alert = ref<any>(null)
const activeTab = ref('info')

// 关联资产
const relatedAssets = ref<any[]>([])

// 时间线
const timelineLoading = ref(false)
const timelineItems = ref<any[]>([])

// AI 分析
const aiLoading = ref(false)
const aiAnalysis = ref<any>(null)

// 执行历史
const executions = ref<any[]>([])

async function loadAlert() {
  const id = alertId()
  if (!id) return
  loading.value = true
  try {
    const { data } = await api.get(R.ALERT_DETAIL(id))
    if (data.code === 0) {
      alert.value = data.data
      // 加载关联数据
      loadRelatedAssets()
      loadTimeline()
      loadAiAnalysis()
      loadExecutions()
    }
  } catch {
    ElMessage.error('加载告警详情失败')
  } finally {
    loading.value = false
  }
}

async function loadRelatedAssets() {
  const a = alert.value
  if (!a) return
  const assetIds: string[] = a.asset_ids || (a.asset_id ? [a.asset_id] : [])
  if (!assetIds.length) { relatedAssets.value = []; return }
  try {
    const results = await Promise.all(
      assetIds.map(id => api.get(R.ASSET_DETAIL(id)).then(r => r.data).catch(() => null))
    )
    relatedAssets.value = results.filter(r => r && r.code === 0).map((r: any) => r.data)
  } catch {
    relatedAssets.value = []
  }
}

async function loadTimeline() {
  timelineLoading.value = true
  try {
    const { data } = await api.get(R.EVENTS, {
      params: { alert_id: alertId(), page: 1, page_size: 50 },
    })
    if (data.code === 0) {
      timelineItems.value = data.data?.items || data.data || []
    }
  } catch {
    timelineItems.value = []
  } finally {
    timelineLoading.value = false
  }
}

async function loadAiAnalysis() {
  aiLoading.value = true
  try {
    const { data } = await api.get(R.AIOPS.ANALYSES, {
      params: { alert_id: alertId(), page: 1, page_size: 1 },
    })
    if (data.code === 0) {
      const items = data.data?.items || data.data || []
      aiAnalysis.value = items[0] || null
    }
  } catch {
    aiAnalysis.value = null
  } finally {
    aiLoading.value = false
  }
}

async function loadExecutions() {
  try {
    const { data } = await api.get(R.EXECUTIONS, {
      params: { alert_id: alertId(), page: 1, page_size: 20 },
    })
    if (data.code === 0) {
      executions.value = data.data?.items || data.data || []
    }
  } catch {
    executions.value = []
  }
}

async function ackAlert() {
  try {
    const { data } = await api.post(R.ALERT_ACKNOWLEDGE(alertId()))
    if (data.code === 0) {
      ElMessage.success('告警已确认')
      loadAlert()
    }
  } catch {
    ElMessage.error('操作失败')
  }
}

async function resolveAlert() {
  try {
    const { data } = await api.post(R.ALERT_RESOLVE(alertId()))
    if (data.code === 0) {
      ElMessage.success('告警已恢复')
      loadAlert()
    }
  } catch {
    ElMessage.error('操作失败')
  }
}

function formatTime(t: string) {
  return t ? new Date(t).toLocaleString('zh-CN') : '-'
}

function formatJson(obj: any) {
  try { return JSON.stringify(obj, null, 2) } catch { return String(obj) }
}

onMounted(() => loadAlert())
watch(() => route.params.id, () => { if (route.params.id) loadAlert() })
</script>

<style scoped>
.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
}
.detail-title-area {
  display: flex;
  align-items: center;
  flex: 1;
}
</style>
