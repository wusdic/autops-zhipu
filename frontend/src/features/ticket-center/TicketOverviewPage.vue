<template>
  <div class="p-6">
    <h2 class="page-title">工单总览</h2>
    <el-row :gutter="16" class="mb-lg">
      <el-col :xs="12" :sm="6" v-for="card in statCards" :key="card.label">
        <div class="autops-metric-card">
          <div class="metric-label">{{ card.label }}</div>
          <div class="metric-value" :style="{ color: card.color }">{{ card.value }}</div>
        </div>
      </el-col>
    </el-row>
    <el-row :gutter="16">
      <el-col :span="16">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">工单趋势</div></div>
          <div class="autops-card-body"><el-empty description="暂无趋势数据" :image-size="80" /></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">工单分类</div></div>
          <div class="autops-card-body">
            <div v-for="cat in categories" :key="cat.name" class="cat-row">
              <span class="cat-name">{{ cat.name }}</span>
              <el-progress :percentage="cat.percentage" :stroke-width="10" style="flex:1;margin:0 12px" />
              <span class="text-tertiary font-12">{{ cat.count }}</span>
            </div>
          </div>
        </div>
        <div class="autops-card" style="margin-top:16px">
          <div class="autops-card-header"><div class="autops-card-title">SLA 达成率</div></div>
          <div class="autops-card-body" style="text-align:center">
            <div style="font-size:36px;font-weight:700;color:#00b42a;margin:12px 0">-</div>
            <div style="color:#86909c">目标: 95%</div>
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
  { label: "处理中", value: 0, color: "#ff7d00" },
  { label: "待我处理", value: 0, color: "#f53f3f" },
  { label: "今日关闭", value: 0, color: "#00b42a" },
])
const categories = ref<any[]>([])
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
.text-tertiary { color: #86909c; } .font-12 { font-size: 12px; }
.cat-row { display: flex; align-items: center; margin-bottom: 12px; }
.cat-name { width: 100px; font-size: 13px; }
</style>
