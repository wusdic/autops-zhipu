<template>
  <div class="p-6">
    <div class="page-header"><h2 class="page-title">证据归档</h2></div>
    <p class="page-desc text-tertiary mb-md">告警证据、执行日志、巡检结果归档</p>
    <el-table :data="tableData" stripe v-loading="loading" empty-text="暂无数据">
      <el-table-column prop="evidence_type" label="证据类型" min-width="120" show-overflow-tooltip />\n      <el-table-column prop="source" label="来源" min-width="140" show-overflow-tooltip />\n      <el-table-column prop="asset_name" label="关联资产" min-width="140" show-overflow-tooltip />\n      <el-table-column prop="collected_at" label="采集时间" min-width="140" show-overflow-tooltip />
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
