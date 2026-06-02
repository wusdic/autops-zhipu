<template>
  <div class="p-6">
    <div class="page-header"><h2 class="page-title">采集结果</h2></div>
    <p class="page-desc text-tertiary mb-md">原始输出、标准化指标、解析结果、错误详情</p>
    <el-table :data="tableData" stripe v-loading="loading" empty-text="暂无数据">
      <el-table-column prop="asset_name" label="资产" min-width="140" show-overflow-tooltip />
      <el-table-column prop="collector_type" label="采集器" min-width="100" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="80"  />
      <el-table-column prop="output_summary" label="输出摘要" min-width="200" show-overflow-tooltip />
      <el-table-column prop="collected_at" label="采集时间" min-width="140" show-overflow-tooltip />
    </el-table>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from "vue"
const loading = ref(false)
const tableData = ref<any[]>([])
onMounted(() => {})
</script>
<style scoped>
.page-header { margin-bottom: 8px; }
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
.page-desc { font-size: 13px; } .text-tertiary { color: #86909c; } .mb-md { margin-bottom: 12px; }
</style>
