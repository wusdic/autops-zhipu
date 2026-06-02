<template>
  <div class="p-6">
    <div class="page-header"><h2 class="page-title">日志接入</h2></div>
    <p class="page-desc text-tertiary mb-md">日志源、解析规则、接入状态</p>
    <el-table :data="tableData" stripe v-loading="loading" empty-text="暂无数据">
      <el-table-column prop="source_name" label="日志源" min-width="160" show-overflow-tooltip />
      <el-table-column prop="parser_rule" label="解析规则" min-width="160" show-overflow-tooltip />
      <el-table-column prop="status" label="接入状态" width="80"  />
      <el-table-column prop="daily_volume" label="日志量/天" min-width="100" show-overflow-tooltip />
      <el-table-column prop="sample" label="样例日志" min-width="200" show-overflow-tooltip />
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
