<template>
  <div class="p-6">
    <div class="page-header"><h2 class="page-title">报表预览</h2></div>
    <p class="page-desc text-tertiary mb-md">在线预览生成的报表内容</p>
    <el-table :data="tableData" stripe v-loading="loading" empty-text="暂无数据">
      <el-table-column prop="title" label="报表标题" min-width="200" show-overflow-tooltip />\n      <el-table-column prop="type" label="类型" min-width="100" show-overflow-tooltip />\n      <el-table-column prop="format" label="格式" width="80"  />\n      <el-table-column prop="generated_at" label="生成时间" min-width="140" show-overflow-tooltip />
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
