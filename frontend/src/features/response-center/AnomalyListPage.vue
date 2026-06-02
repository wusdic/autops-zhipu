<template>
  <div class="p-6">
    <div class="page-header">
      <h2 class="page-title">异常列表</h2>
      <div>
        <el-select v-model="filterSeverity" placeholder="严重级别" clearable style="width:120px;margin-right:12px">
          <el-option label="严重" value="critical" /><el-option label="高" value="high" /><el-option label="中" value="medium" /><el-option label="低" value="low" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="状态" clearable style="width:120px;margin-right:12px">
          <el-option label="新建" value="new" /><el-option label="确认" value="confirmed" /><el-option label="处理中" value="processing" /><el-option label="已关闭" value="closed" />
        </el-select>
      </div>
    </div>
    <el-table :data="anomalies" stripe v-loading="loading" empty-text="暂无异常">
      <el-table-column prop="severity" label="级别" width="80">
        <template #default="{ row }">
          <span class="autops-status-tag" :class="severityClass(row.severity)">{{ severityLabel(row.severity) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="异常描述" min-width="200" show-overflow-tooltip />
      <el-table-column prop="source" label="来源" width="100">
        <template #default="{ row }"><el-tag size="small">{{ row.source }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="asset_name" label="关联资产" width="140" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="anomalyStatusType(row.status)" size="small">{{ anomalyStatusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="has_ai_analysis" label="AI分析" width="80">
        <template #default="{ row }">
          <el-tag v-if="row.has_ai_analysis" type="success" size="small">有</el-tag>
          <el-tag v-else type="info" size="small">无</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="发现时间" width="160">
        <template #default="{ row }"><span class="text-tertiary">{{ row.created_at }}</span></template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" size="small" @click="$router.push(`/response/anomalies/${row.id}`)">详情</el-button>
          <el-button v-if="row.status === 'new'" text type="success" size="small">确认</el-button>
          <el-button text type="warning" size="small">AI分析</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import api from "@/shared/api/client"
import { API } from "@/shared/api/routes"

const loading = ref(false)
const anomalies = ref<any[]>([])
const filterSeverity = ref("")
const filterStatus = ref("")

function severityClass(s: string) { return ({ critical: "status-failed", high: "status-warning", medium: "status-info", low: "status-info" } as any)[s] || "status-info" }
function severityLabel(s: string) { return ({ critical: "严重", high: "高", medium: "中", low: "低" } as any)[s] || s }
function anomalyStatusType(s: string) { return ({ new: "danger", confirmed: "warning", processing: "", closed: "success" } as any)[s] || "info" }
function anomalyStatusLabel(s: string) { return ({ new: "新建", confirmed: "已确认", processing: "处理中", closed: "已关闭" } as any)[s] || s }

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.get(API.EVENTS, { params: { page_size: 50 } })
    if (res.data?.code === 0) {
      anomalies.value = (res.data.data?.items || []).map((e: any) => ({
        id: e.id, title: e.detail || e.event_type || "异常事件", source: e.event_type || "unknown",
        asset_name: e.asset_id || "-", severity: "medium", status: "new",
        has_ai_analysis: false, created_at: e.created_at || "-"
      }))
    }
  } catch (e) { console.error(e) } finally { loading.value = false }
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
.text-tertiary { color: #86909c; font-size: 12px; }
.autops-status-tag { padding: 2px 8px; border-radius: 4px; font-size: 12px; }
.status-failed { background: #ffece8; color: #f53f3f; } .status-warning { background: #fff7e8; color: #ff7d00; }
.status-info { background: #f2f3f5; color: #86909c; }
</style>
