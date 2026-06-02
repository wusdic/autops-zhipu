<template>
  <div class="p-6">
    <h2 class="page-title">异常总览</h2>
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
          <div class="autops-card-header"><div class="autops-card-title">异常来源分布</div></div>
          <div class="autops-card-body"><div ref="sourceRef" style="height:260px"></div></div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">处置状态分布</div></div>
          <div class="autops-card-body"><div ref="statusRef" style="height:260px"></div></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, onUnmounted } from "vue"
import * as echarts from "echarts"
import { Warning, CircleCheck, Clock, DataAnalysis } from "@element-plus/icons-vue"

const statCards = reactive([
  { label: "异常总数", value: 0, icon: Warning, bg: "#ffece8", color: "#f53f3f" },
  { label: "自动处理", value: 0, icon: CircleCheck, bg: "#e8ffea", color: "#00b42a" },
  { label: "待人工处理", value: 0, icon: Clock, bg: "#fff7e8", color: "#ff7d00" },
  { label: "自动处理比例", value: "0%", icon: DataAnalysis, bg: "#e8f3ff", color: "#165dff" },
])
const sourceRef = ref<HTMLElement>()
const statusRef = ref<HTMLElement>()
let charts: echarts.ECharts[] = []

onMounted(async () => {
  await nextTick()
  if (sourceRef.value) {
    const c = echarts.init(sourceRef.value)
    c.setOption({ tooltip: { trigger: "item" }, series: [{ type: "pie", radius: ["40%","70%"], data: [
      { name: "巡检异常", value: 3 }, { name: "监控告警", value: 5 }, { name: "日志异常", value: 2 }, { name: "配置漂移", value: 1 }
    ] }] })
    charts.push(c)
  }
  if (statusRef.value) {
    const c = echarts.init(statusRef.value)
    c.setOption({ tooltip: { trigger: "item" }, series: [{ type: "pie", radius: ["40%","70%"], data: [
      { name: "已自动处理", value: 4, itemStyle: { color: "#00b42a" } },
      { name: "待处理", value: 3, itemStyle: { color: "#ff7d00" } },
      { name: "处理中", value: 2, itemStyle: { color: "#165dff" } },
      { name: "已升级", value: 1, itemStyle: { color: "#f53f3f" } },
    ] }] })
    charts.push(c)
  }
})
onUnmounted(() => { charts.forEach(c => c.dispose()) })
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
</style>
