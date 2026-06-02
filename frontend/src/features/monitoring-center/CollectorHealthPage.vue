<template>
  <div class="p-6">
    <div class="page-header"><h2 class="page-title">采集器健康</h2></div>
    <p class="page-desc text-tertiary mb-md">在线状态、心跳、版本、任务积压</p>
    <el-table :data="tableData" stripe v-loading="loading" empty-text="暂无数据">
      <el-table-column prop="collector_type" label="采集器类型" min-width="120" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="80"  />
      <el-table-column prop="version" label="版本" width="80"  />
      <el-table-column prop="task_backlog" label="任务积压" width="80"  />
      <el-table-column prop="last_heartbeat" label="最后心跳" min-width="140" show-overflow-tooltip />
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
