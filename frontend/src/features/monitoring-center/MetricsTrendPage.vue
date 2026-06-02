<template>
  <div class="p-6">
    <div class="page-header"><h2 class="page-title">指标趋势</h2></div>
    <p class="page-desc text-tertiary mb-md">CPU、内存、磁盘、网络、数据库、页面响应时间</p>
    <el-table :data="tableData" stripe v-loading="loading" empty-text="暂无数据">
      <el-table-column prop="asset_name" label="资产" min-width="140" show-overflow-tooltip />
      <el-table-column prop="metric_name" label="指标" min-width="120" show-overflow-tooltip />
      <el-table-column prop="current" label="当前值" min-width="100" show-overflow-tooltip />
      <el-table-column prop="unit" label="单位" width="60"  />
      <el-table-column prop="updated_at" label="更新时间" min-width="140" show-overflow-tooltip />
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
