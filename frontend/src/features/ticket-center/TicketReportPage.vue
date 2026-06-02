<template>
  <div class="p-6">
    <h2 class="page-title">工单报告</h2>
    <el-row :gutter="16" class="mb-lg">
      <el-col :xs="12" :sm="6" v-for="card in statCards" :key="card.label">
        <div class="autops-metric-card">
          <div class="metric-label">{{ card.label }}</div>
          <div class="metric-value" :style="{ color: card.color }">{{ card.value }}</div>
        </div>
      </el-col>
    </el-row>
    <el-row :gutter="16">
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">工单趋势</div></div>
          <div class="autops-card-body"><el-empty description="暂无趋势数据" :image-size="80" /></div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">处理人统计</div></div>
          <div class="autops-card-body" style="padding:0">
            <el-table :data="assigneeStats" stripe size="small" empty-text="暂无数据">
              <el-table-column prop="name" label="处理人" min-width="120" />
              <el-table-column prop="total" label="总数" width="70" />
              <el-table-column prop="resolved" label="已解决" width="70" />
              <el-table-column prop="avg_time" label="平均耗时" width="90" />
              <el-table-column prop="sla_rate" label="SLA达成" width="80" />
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue"

const statCards = reactive([
  { label: "总工单", value: 0, color: "#165dff" },
  { label: "已关闭", value: 0, color: "#00b42a" },
  { label: "平均解决时间", value: "-", color: "#ff7d00" },
  { label: "SLA达成率", value: "-", color: "#00b42a" },
])
const assigneeStats = ref<any[]>([])
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
</style>
