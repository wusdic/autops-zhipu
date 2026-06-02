<template>
  <div class="p-6">
    <div class="page-header"><h2 class="page-title">状态变化</h2></div>
    <p class="page-desc text-tertiary mb-md">状态变更历史、触发来源、证据</p>
    <el-table :data="tableData" stripe v-loading="loading" empty-text="暂无数据">
      <el-table-column prop="asset_name" label="资产" min-width="140" show-overflow-tooltip />
      <el-table-column prop="attribute_name" label="属性" min-width="100" show-overflow-tooltip />
      <el-table-column prop="old_value" label="旧值" min-width="100" show-overflow-tooltip />
      <el-table-column prop="new_value" label="新值" min-width="100" show-overflow-tooltip />
      <el-table-column prop="changed_at" label="变化时间" min-width="140" show-overflow-tooltip />
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
