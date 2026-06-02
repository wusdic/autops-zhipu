<template>
  <div class="p-6">
    <div class="page-header">
      <h2 class="page-title">巡检结果</h2>
      <el-select v-model="filterResult" placeholder="结果" clearable style="width:120px">
        <el-option label="正常" value="normal" /><el-option label="异常" value="abnormal" /><el-option label="风险" value="risk" />
      </el-select>
    </div>
    <el-table :data="filteredResults" stripe v-loading="loading" empty-text="暂无巡检结果">
      <el-table-column prop="task_name" label="任务名称" min-width="160" show-overflow-tooltip />
      <el-table-column prop="asset_name" label="资产" width="140" show-overflow-tooltip />
      <el-table-column prop="check_item" label="巡检项" min-width="160" show-overflow-tooltip />
      <el-table-column prop="result" label="结果" width="80">
        <template #default="{ row }">
          <el-tag :type="resultType(row.result)" size="small">{{ resultLabel(row.result) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="actual_value" label="实际值" width="120" />
      <el-table-column prop="expected_value" label="期望值" width="120" />
      <el-table-column prop="evidence" label="证据" min-width="200" show-overflow-tooltip />
      <el-table-column prop="checked_at" label="检查时间" width="160">
        <template #default="{ row }"><span class="text-tertiary">{{ row.checked_at }}</span></template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.result !== 'normal'" text type="primary" size="small" @click="viewAnomaly(row)">异常详情</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue"
import { useRouter } from "vue-router"

const router = useRouter()
const loading = ref(false)
const results = ref<any[]>([])
const filterResult = ref("")
const filteredResults = computed(() => filterResult.value ? results.value.filter(r => r.result === filterResult.value) : results.value)

function resultType(r: string) { return ({ normal: "success", abnormal: "danger", risk: "warning" } as any)[r] || "info" }
function resultLabel(r: string) { return ({ normal: "正常", abnormal: "异常", risk: "风险" } as any)[r] || r }
function viewAnomaly(row: any) { router.push("/response/anomalies") }
onMounted(() => { loading.value = false })
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
.text-tertiary { color: #86909c; font-size: 12px; }
</style>
