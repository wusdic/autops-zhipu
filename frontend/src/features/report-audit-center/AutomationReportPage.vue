<template>
  <div class="p-6">
    <h2 class="page-title">自动化报告</h2>
    <el-row :gutter="16" class="mb-lg">
      <el-col :xs="12" :sm="6" v-for="card in statCards" :key="card.label">
        <div class="autops-metric-card">
          <div class="metric-label">{{ card.label }}</div>
          <div class="metric-value" :style="{ color: card.color }">{{ card.value }}</div>
        </div>
      </el-col>
    </el-row>
    <div class="autops-card">
      <div class="autops-card-header"><div class="autops-card-title">自动化执行统计</div></div>
      <div class="autops-card-body" style="padding:0">
        <el-table :data="stats" stripe size="small" empty-text="暂无数据">
          <el-table-column prop="category" label="分类" min-width="160" />
          <el-table-column prop="total" label="执行总数" width="100" />
          <el-table-column prop="success" label="成功" width="80">
            <template #default="{ row }"><span style="color:#00b42a">{{ row.success }}</span></template>
          </el-table-column>
          <el-table-column prop="failed" label="失败" width="80">
            <template #default="{ row }"><span style="color:#f53f3f">{{ row.failed }}</span></template>
          </el-table-column>
          <el-table-column prop="success_rate" label="成功率" width="100" />
          <el-table-column prop="avg_duration" label="平均耗时" width="100" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue"

const statCards = reactive([
  { label: "今日执行", value: 0, color: "#165dff" },
  { label: "成功率", value: "0%", color: "#00b42a" },
  { label: "自动处置", value: 0, color: "#ff7d00" },
  { label: "平均耗时", value: "-", color: "#86909c" },
])
const stats = ref<any[]>([])
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
</style>
