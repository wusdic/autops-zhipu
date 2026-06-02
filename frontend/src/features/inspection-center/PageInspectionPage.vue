<template>
  <div class="p-6">
    <div class="page-header">
      <h2 class="page-title">页面巡检</h2>
      <el-button type="primary" @click="handleCreate"><el-icon><Plus /></el-icon> 新建</el-button>
    </div>
    <p class="page-desc text-tertiary mb-md">URL可用性、状态码、关键字、响应时间、截图检测</p>
    <el-table :data="tableData" stripe v-loading="loading" empty-text="暂无数据">
      <el-table-column prop="url" label="URL地址" min-width="200" show-overflow-tooltip />
      <el-table-column prop="status_code" label="状态码" width="80"  />
      <el-table-column prop="response_time" label="响应时间(ms)" min-width="100" show-overflow-tooltip />
      <el-table-column prop="keyword_match" label="关键字匹配" min-width="100" show-overflow-tooltip />
      <el-table-column prop="available" label="可用" width="80"  />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default>
          <el-button text type="primary" size="small">查看</el-button>
          <el-button text type="danger" size="small">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { Plus } from "@element-plus/icons-vue"
import { ElMessage } from "element-plus"

const loading = ref(false)
const tableData = ref<any[]>([])
function handleCreate() { ElMessage.info("功能开发中") }
onMounted(() => { loading.value = false })
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
.page-desc { font-size: 13px; }
.text-tertiary { color: #86909c; } .mb-md { margin-bottom: 12px; }
</style>
