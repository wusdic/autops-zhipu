<template>
  <div class="p-6">
    <h2 class="page-title">回滚中心</h2>
    <el-table :data="rollbacks" stripe v-loading="loading" empty-text="暂无可回滚的执行">
      <el-table-column prop="execution_id" label="执行ID" width="120" />
      <el-table-column prop="task_name" label="任务名称" min-width="180" show-overflow-tooltip />
      <el-table-column prop="executed_at" label="执行时间" width="160" />
      <el-table-column prop="status" label="执行状态" width="90">
        <template #default="{ row }">
          <el-tag :type="{ completed:'success', failed:'danger', partial:'warning' }[row.status as string]" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="has_rollback" label="可回滚" width="80">
        <template #default="{ row }">
          <el-tag :type="row.has_rollback ? 'success' : 'info'" size="small">{{ row.has_rollback ? '是' : '否' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="rollback_status" label="回滚状态" width="100" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.has_rollback && !row.rollback_status" text type="warning" size="small" @click="rollback(row)">回滚</el-button>
          <el-button text type="primary" size="small" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import api from "@/shared/api/client"
import { API } from "@/shared/api/routes"
import { ElMessage } from "element-plus"

const loading = ref(false)
const rollbacks = ref<any[]>([])

function viewDetail(row: any) { ElMessage.info("查看执行详情") }
function rollback(row: any) { row.rollback_status = "回滚中"; ElMessage.warning("回滚已触发") }

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.get(API.EXECUTIONS, { params: { page_size: 50 } })
    if (res.data?.code === 0) {
      rollbacks.value = (res.data.data?.items || []).map((e: any) => ({
        execution_id: e.id?.toString().slice(0, 8) || "-", task_name: e.execution_type || "-",
        executed_at: e.created_at || "-", status: e.status || "-", has_rollback: true, rollback_status: null,
      }))
    }
  } catch (e) { console.error(e) } finally { loading.value = false }
})
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
</style>
