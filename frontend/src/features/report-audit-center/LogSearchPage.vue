<template>
  <div class="p-6">
    <div class="page-header"><h2 class="page-title">日志检索</h2></div>
    <p class="page-desc text-tertiary mb-md">按时间/级别/来源/关键词检索日志</p>
    <el-table :data="tableData" stripe v-loading="loading" empty-text="暂无数据">
      <el-table-column prop="timestamp" label="时间" min-width="160" show-overflow-tooltip />\n      <el-table-column prop="level" label="级别" width="80"  />\n      <el-table-column prop="source" label="来源" min-width="120" show-overflow-tooltip />\n      <el-table-column prop="message" label="内容" min-width="300" show-overflow-tooltip />
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
