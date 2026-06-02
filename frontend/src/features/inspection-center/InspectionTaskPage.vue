<template>
  <div class="p-6">
    <div class="page-header">
      <h2 class="page-title">巡检任务</h2>
      <div>
        <el-select v-model="filterStatus" placeholder="状态" clearable style="width:120px;margin-right:12px">
          <el-option label="执行中" value="running" /><el-option label="已完成" value="completed" /><el-option label="失败" value="failed" /><el-option label="待执行" value="pending" />
        </el-select>
        <el-button type="primary" @click="createTask"><el-icon><Plus /></el-icon> 立即巡检</el-button>
      </div>
    </div>
    <el-table :data="filteredTasks" stripe v-loading="loading" empty-text="暂无巡检任务">
      <el-table-column prop="name" label="任务名称" min-width="180" show-overflow-tooltip />
      <el-table-column prop="plan_name" label="计划来源" width="150" />
      <el-table-column prop="asset_count" label="资产数" width="80" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="progress" label="进度" width="120">
        <template #default="{ row }">
          <el-progress :percentage="row.progress" :status="row.status === 'failed' ? 'exception' : row.progress === 100 ? 'success' : ''" :stroke-width="6" />
        </template>
      </el-table-column>
      <el-table-column prop="started_at" label="开始时间" width="160">
        <template #default="{ row }"><span class="text-tertiary">{{ row.started_at || "-" }}</span></template>
      </el-table-column>
      <el-table-column prop="completed_at" label="结束时间" width="160">
        <template #default="{ row }"><span class="text-tertiary">{{ row.completed_at || "-" }}</span></template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" size="small" @click="viewResult(row)">结果</el-button>
          <el-button v-if="row.status === 'failed'" text type="warning" size="small" @click="retryTask(row)">重试</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import { Plus } from "@element-plus/icons-vue"
import { ElMessage } from "element-plus"

const router = useRouter()
const loading = ref(false)
const tasks = ref<any[]>([])
const filterStatus = ref("")
const filteredTasks = computed(() => filterStatus.value ? tasks.value.filter(t => t.status === filterStatus.value) : tasks.value)

function statusType(s: string) { return ({ completed: "success", failed: "danger", running: "warning", pending: "info" } as any)[s] || "info" }
function statusLabel(s: string) { return ({ completed: "已完成", failed: "失败", running: "执行中", pending: "待执行" } as any)[s] || s }
function createTask() { ElMessage.info("立即巡检：选择资产和模板后执行") }
function viewResult(row: any) { router.push("/inspection/results") }
function retryTask(row: any) { row.status = "running"; row.progress = 0; ElMessage.success("已重新执行") }
onMounted(() => { loading.value = false })
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
.text-tertiary { color: #86909c; font-size: 12px; }
</style>
