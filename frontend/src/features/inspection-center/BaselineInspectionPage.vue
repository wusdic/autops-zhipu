<template>
  <div class="p-6">
    <div class="page-header">
      <h2 class="page-title">基线巡检</h2>
      <el-button type="primary" @click="handleCreate"><el-icon><Plus /></el-icon> 新建</el-button>
    </div>
    <p class="page-desc text-tertiary mb-md">安全和运维基线检查、通过率、未通过项</p>
    <el-table :data="tableData" stripe v-loading="loading" empty-text="暂无数据">
      <el-table-column prop="asset_name" label="资产" min-width="140" show-overflow-tooltip />
      <el-table-column prop="baseline_item" label="基线项" min-width="160" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="80"  />
      <el-table-column prop="risk_level" label="风险等级" width="80"  />
      <el-table-column prop="suggestion" label="整改建议" min-width="200" show-overflow-tooltip />
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
