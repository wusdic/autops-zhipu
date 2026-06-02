<template>
  <div class="p-6">
    <h2 class="page-title">巡检总览</h2>
    <el-row :gutter="16" class="mb-lg">
      <el-col :xs="12" :sm="6" v-for="card in statCards" :key="card.label">
        <div class="autops-metric-card" @click="card.route && $router.push(card.route)">
          <div class="metric-icon" :style="{ background: card.bg, color: card.color }">
            <el-icon size="20"><component :is="card.icon" /></el-icon>
          </div>
          <div class="metric-label">{{ card.label }}</div>
          <div class="metric-value" :style="{ color: card.color }">{{ card.value }}</div>
        </div>
      </el-col>
    </el-row>
    <el-row :gutter="16">
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">巡检任务趋势</div></div>
          <div class="autops-card-body"><div ref="trendRef" style="height: 260px"></div></div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">最近巡检任务</div></div>
          <div class="autops-card-body" style="padding: 0">
            <el-table :data="recentTasks" stripe size="small" empty-text="暂无巡检任务">
              <el-table-column prop="name" label="任务名称" min-width="160" show-overflow-tooltip />
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="success_rate" label="通过率" width="80" />
              <el-table-column prop="started_at" label="开始时间" width="140">
                <template #default="{ row }"><span class="text-tertiary font-12">{{ row.started_at }}</span></template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, onUnmounted } from "vue"
import * as echarts from "echarts"
import { CircleCheck, Warning, Clock, DataAnalysis } from "@element-plus/icons-vue"

const statCards = reactive([
  { label: "巡检任务数", value: 0, icon: DataAnalysis, bg: "#e8f3ff", color: "#165dff", route: "/inspection/tasks" },
  { label: "成功率", value: "0%", icon: CircleCheck, bg: "#e8ffea", color: "#00b42a", route: "/inspection/results" },
  { label: "异常巡检项", value: 0, icon: Warning, bg: "#ffece8", color: "#f53f3f", route: "/response/anomalies" },
  { label: "覆盖资产", value: 0, icon: Clock, bg: "#fff7e8", color: "#ff7d00" },
])
const recentTasks = ref<any[]>([])
const trendRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null

function statusType(s: string) { return ({ completed: "success", failed: "danger", running: "warning", pending: "info" } as any)[s] || "info" }
function statusLabel(s: string) { return ({ completed: "已完成", failed: "失败", running: "执行中", pending: "待执行" } as any)[s] || s }

onMounted(async () => {
  await nextTick()
  if (trendRef.value) {
    trendChart = echarts.init(trendRef.value)
    trendChart.setOption({
      tooltip: { trigger: "axis" },
      grid: { left: 40, right: 20, top: 16, bottom: 30 },
      xAxis: { type: "category", data: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"], axisLabel: { color: "#86909c" } },
      yAxis: { type: "value", axisLabel: { color: "#86909c" }, splitLine: { lineStyle: { color: "#f2f3f5" } } },
      series: [
        { name: "成功", type: "bar", stack: "total", data: [5, 8, 6, 7, 9, 4, 3], itemStyle: { color: "#00b42a" } },
        { name: "失败", type: "bar", stack: "total", data: [1, 0, 2, 1, 0, 1, 0], itemStyle: { color: "#f53f3f" } },
      ],
    })
  }
})
onUnmounted(() => { trendChart?.dispose() })
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
.text-tertiary { color: #86909c; } .font-12 { font-size: 12px; }
</style>
