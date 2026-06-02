<template>
  <div class="p-6">
    <h2 class="page-title">资源总览</h2>
    <!-- 统计卡片 -->
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
    <!-- 类型分布 + 环境分布 -->
    <el-row :gutter="16">
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">资产类型分布</div></div>
          <div class="autops-card-body"><div ref="typeChartRef" style="height: 280px"></div></div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">纳管状态分布</div></div>
          <div class="autops-card-body"><div ref="statusChartRef" style="height: 280px"></div></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, onUnmounted } from "vue"
import * as echarts from "echarts"
import api from "@/shared/api/client"
import { API } from "@/shared/api/routes"
import { Box, Search, Warning, CircleCheck } from "@element-plus/icons-vue"

const statCards = reactive([
  { label: "资产总数", value: 0, icon: Box, bg: "#e8f3ff", color: "#165dff", route: "/resource-center/assets" },
  { label: "巡检覆盖率", value: "0%", icon: CircleCheck, bg: "#e8ffea", color: "#00b42a", route: "/inspection/overview" },
  { label: "异常资源数", value: 0, icon: Warning, bg: "#ffece8", color: "#f53f3f", route: "/response/anomalies" },
  { label: "待纳管", value: 0, icon: Search, bg: "#fff7e8", color: "#ff7d00", route: "/resource-center/discovery" },
])

const typeChartRef = ref<HTMLElement>()
const statusChartRef = ref<HTMLElement>()
let typeChart: echarts.ECharts | null = null
let statusChart: echarts.ECharts | null = null

onMounted(async () => {
  try {
    const res = await api.get(API.ASSETS, { params: { page_size: 100 } })
    const data = res.data?.data
    if (data?.items) {
      const items = data.items
      statCards[0].value = data.total || items.length
      statCards[3].value = items.filter((a: any) => a.reachability === "unknown").length

      // 类型分布
      const typeMap: Record<string, number> = {}
      items.forEach((a: any) => { const t = a.asset_type || "unknown"; typeMap[t] = (typeMap[t] || 0) + 1 })
      await nextTick()
      if (typeChartRef.value) {
        typeChart = echarts.init(typeChartRef.value)
        typeChart.setOption({
          tooltip: { trigger: "item" },
          series: [{ type: "pie", radius: ["40%", "70%"], data: Object.entries(typeMap).map(([name, value]) => ({ name, value })),
            emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: "rgba(0,0,0,0.2)" } } }],
        })
      }

      // 状态分布
      const statusMap: Record<string, number> = { reachable: 0, unreachable: 0, unknown: 0 }
      items.forEach((a: any) => { statusMap[a.reachability || "unknown"] = (statusMap[a.reachability || "unknown"] || 0) + 1 })
      await nextTick()
      if (statusChartRef.value) {
        statusChart = echarts.init(statusChartRef.value)
        const colorMap: Record<string, string> = { reachable: "#00b42a", unreachable: "#f53f3f", unknown: "#86909c" }
        const labelMap: Record<string, string> = { reachable: "可达", unreachable: "不可达", unknown: "未知" }
        statusChart.setOption({
          tooltip: { trigger: "item" },
          series: [{ type: "pie", radius: ["40%", "70%"],
            data: Object.entries(statusMap).map(([k, v]) => ({ name: labelMap[k] || k, value: v, itemStyle: { color: colorMap[k] } })) }],
        })
      }
    }
  } catch (e) { console.error("ResourceOverview fetch error:", e) }
})

onUnmounted(() => { typeChart?.dispose(); statusChart?.dispose() })
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
</style>
