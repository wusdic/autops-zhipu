<template>
  <div class="p-6">
    <div class="page-header"><h2 class="page-title">报表任务</h2></div>
    <p class="page-desc text-tertiary mb-md">报表生成任务队列、进度、日志</p>
    <el-table :data="tableData" stripe v-loading="loading" empty-text="暂无数据">
      <el-table-column prop="title" label="报表标题" min-width="180" show-overflow-tooltip />\n      <el-table-column prop="template_name" label="模板" min-width="120" show-overflow-tooltip />\n      <el-table-column prop="status" label="状态" width="80"  />\n      <el-table-column prop="progress" label="进度" min-width="100" show-overflow-tooltip />\n      <el-table-column prop="started_at" label="开始时间" min-width="140" show-overflow-tooltip />
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
