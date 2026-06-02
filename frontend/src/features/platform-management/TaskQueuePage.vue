<template>
  <div class="p-6">
    <div class="page-header">
      <h2 class="page-title">任务队列</h2>
      <div>
        <el-select v-model="filterStatus" placeholder="状态" clearable style="width:120px;margin-right:12px">
          <el-option label="排队中" value="queued" /><el-option label="执行中" value="running" /><el-option label="完成" value="completed" /><el-option label="失败" value="failed" />
        </el-select>
      </div>
    </div>
    <el-table :data="tasks" stripe v-loading="loading" empty-text="暂无任务">
      <el-table-column prop="task_type" label="任务类型" width="120" />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="({ queued:'info', running:'warning', completed:'success', failed:'danger' } as any)[row.status]" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="80" />
      <el-table-column prop="worker" label="执行者" width="100" />
      <el-table-column prop="retries" label="重试" width="60" />
      <el-table-column prop="created_at" label="创建时间" width="160">
        <template #default="{ row }"><span class="text-tertiary">{{ row.created_at }}</span></template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'failed'" text type="warning" size="small">重试</el-button>
          <el-button v-if="row.status === 'queued'" text type="danger" size="small">取消</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
const loading = ref(false)
const tasks = ref<any[]>([])
const filterStatus = ref("")
onMounted(() => { loading.value = false })
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
.text-tertiary { color: #86909c; font-size: 12px; }
</style>
