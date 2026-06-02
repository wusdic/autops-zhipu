<template>
  <div class="p-6">
    <h2 class="page-title">执行锁</h2>
    <el-alert type="info" title="执行锁防止同一资产同时执行多个自动化任务，避免冲突和资源竞争" show-icon :closable="false" style="margin-bottom:16px" />
    <el-table :data="locks" stripe v-loading="loading" empty-text="当前无活跃锁">
      <el-table-column prop="asset_name" label="资产" min-width="160" show-overflow-tooltip />
      <el-table-column prop="lock_type" label="锁类型" width="100" />
      <el-table-column prop="execution_id" label="执行ID" width="120" />
      <el-table-column prop="execution_name" label="执行任务" min-width="160" show-overflow-tooltip />
      <el-table-column prop="locked_at" label="锁定时间" width="160" />
      <el-table-column prop="ttl" label="TTL" width="80" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-popconfirm title="确定强制释放该锁？" @confirm="forceRelease(row)">
            <template #reference><el-button text type="danger" size="small">强制释放</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { ElMessage } from "element-plus"

const loading = ref(false)
const locks = ref<any[]>([])

function forceRelease(row: any) {
  locks.value = locks.value.filter(l => l !== row)
  ElMessage.success("锁已释放")
}

onMounted(() => { loading.value = false })
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
</style>
