<template>
  <div class="p-6">
    <div class="page-header"><h2 class="page-title">状态快照</h2></div>
    <p class="page-desc text-tertiary mb-md">资源当前可达性、健康状态、最新指标</p>
    <el-table :data="tableData" stripe v-loading="loading" empty-text="暂无数据">
      <el-table-column prop="asset_name" label="资产" min-width="140" show-overflow-tooltip />
      <el-table-column prop="reachability" label="可达性" width="80"  />
      <el-table-column prop="health" label="健康" width="80"  />
      <el-table-column prop="last_metric" label="最新指标" min-width="160" show-overflow-tooltip />
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
