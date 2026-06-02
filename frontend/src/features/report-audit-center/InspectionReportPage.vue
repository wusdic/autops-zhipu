<template>
  <div class="p-6">
    <h2 class="page-title">巡检报告</h2>
    <el-row :gutter="16" class="mb-lg">
      <el-col :xs="12" :sm="6" v-for="card in statCards" :key="card.label">
        <div class="autops-metric-card">
          <div class="metric-label">{{ card.label }}</div>
          <div class="metric-value" :style="{ color: card.color }">{{ card.value }}</div>
        </div>
      </el-col>
    </el-row>
    <div class="autops-card">
      <div class="autops-card-header">
        <div class="autops-card-title">报告列表</div>
        <el-button type="primary" size="small"><el-icon><Download /></el-icon> 导出</el-button>
      </div>
      <div class="autops-card-body" style="padding:0">
        <el-table :data="reports" stripe v-loading="loading" empty-text="暂无巡检报告">
          <el-table-column prop="task_name" label="巡检任务" min-width="180" show-overflow-tooltip />
          <el-table-column prop="executed_at" label="执行时间" width="160" />
          <el-table-column prop="asset_count" label="检查资产" width="90" />
          <el-table-column prop="pass_count" label="通过" width="70">
            <template #default="{ row }"><span style="color:#00b42a">{{ row.pass_count }}</span></template>
          </el-table-column>
          <el-table-column prop="fail_count" label="异常" width="70">
            <template #default="{ row }"><span style="color:#f53f3f">{{ row.fail_count }}</span></template>
          </el-table-column>
          <el-table-column prop="score" label="健康分" width="80">
            <template #default="{ row }">
              <span :style="{ color: row.score >= 90 ? '#00b42a' : row.score >= 70 ? '#ff7d00' : '#f53f3f' }">{{ row.score || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" fixed="right">
            <template #default><el-button text type="primary" size="small">查看</el-button></template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from "vue"
import api from "@/shared/api/client"
import { API } from "@/shared/api/routes"
import { Download } from "@element-plus/icons-vue"

const loading = ref(false)
const reports = ref<any[]>([])
const statCards = reactive([
  { label: "今日巡检", value: 0, color: "#165dff" },
  { label: "通过率", value: "-", color: "#00b42a" },
  { label: "异常项", value: 0, color: "#f53f3f" },
  { label: "平均健康分", value: "-", color: "#ff7d00" },
])

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.get(API.INSPECTION_TASKS, { params: { page_size: 50 } })
    if (res.data?.code === 0) reports.value = (res.data.data?.items || []).map((t: any) => ({
      task_name: t.name, executed_at: t.last_run_at || "-", asset_count: t.asset_count || 0,
      pass_count: 0, fail_count: 0, score: null,
    }))
  } catch (e) {} finally { loading.value = false }
})
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
</style>
