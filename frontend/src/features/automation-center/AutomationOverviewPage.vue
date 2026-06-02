<template>
  <div class="p-6">
    <h2 class="page-title">自动化总览</h2>
    <el-row :gutter="16" class="mb-lg">
      <el-col :xs="12" :sm="6" v-for="card in statCards" :key="card.label">
        <div class="autops-metric-card">
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
          <div class="autops-card-header"><div class="autops-card-title">执行趋势</div></div>
          <div class="autops-card-body"><div ref="trendRef" style="height:240px"></div></div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">风险分级统计</div></div>
          <div class="autops-card-body"><div ref="riskRef" style="height:240px"></div></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, onUnmounted } from "vue"
import * as echarts from "echarts"
import { VideoPlay, CircleCheck, Warning, Clock } from "@element-plus/icons-vue"

const statCards = reactive([
  { label: "自动处置次数", value: 0, icon: VideoPlay, bg: "#e8f3ff", color: "#165dff" },
  { label: "成功率", value: "0%", icon: CircleCheck, bg: "#e8ffea", color: "#00b42a" },
  { label: "待审批", value: 0, icon: Clock, bg: "#fff7e8", color: "#ff7d00" },
  { label: "高风险阻断", value: 0, icon: Warning, bg: "#ffece8", color: "#f53f3f" },
])
const trendRef = ref<HTMLElement>(); const riskRef = ref<HTMLElement>()
let charts: echarts.ECharts[] = []

onMounted(async () => {
  await nextTick()
  if (trendRef.value) {
    const c = echarts.init(trendRef.value)
    c.setOption({
      tooltip: { trigger: "axis" }, grid: { left: 40, right: 20, top: 16, bottom: 30 },
      xAxis: { type: "category", data: ["周一","周二","周三","周四","周五","周六","周日"] },
      yAxis: { type: "value" },
      series: [{ type: "line", smooth: true, data: [12,18,15,22,20,8,5], areaStyle: { color: "rgba(22,93,255,0.1)" }, lineStyle: { color: "#165dff" }, itemStyle: { color: "#165dff" } }],
    })
    charts.push(c)
  }
  if (riskRef.value) {
    const c = echarts.init(riskRef.value)
    c.setOption({
      tooltip: { trigger: "item" },
      series: [{ type: "pie", radius: ["40%","70%"], data: [
        { name: "低风险自动处理", value: 15, itemStyle: { color: "#00b42a" } },
        { name: "中风险确认", value: 8, itemStyle: { color: "#ff7d00" } },
        { name: "高风险审批", value: 3, itemStyle: { color: "#f53f3f" } },
      ] }],
    })
    charts.push(c)
  }
})
onUnmounted(() => { charts.forEach(c => c.dispose()) })
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
</style>
