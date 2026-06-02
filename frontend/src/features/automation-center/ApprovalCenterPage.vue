<template>
  <div class="p-6">
    <h2 class="page-title">审批中心</h2>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="待我审批" name="pending" />
      <el-tab-pane label="已审批" name="done" />
    </el-tabs>
    <el-table :data="approvals" stripe v-loading="loading" empty-text="暂无审批">
      <el-table-column prop="execution_type" label="执行类型" width="120" />
      <el-table-column prop="target" label="目标" min-width="160" show-overflow-tooltip />
      <el-table-column prop="risk_level" label="风险等级" width="90">
        <template #default="{ row }">
          <el-tag :type="{ high: 'danger', medium: 'warning', low: 'success' }[row.risk_level as string]" size="small">{{ row.risk_level }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="applicant" label="申请人" width="100" />
      <el-table-column prop="reason" label="原因" min-width="200" show-overflow-tooltip />
      <el-table-column prop="created_at" label="申请时间" width="160" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default>
          <el-button type="success" size="small">批准</el-button>
          <el-button type="danger" size="small">拒绝</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import api from "@/shared/api/client"
import { API } from "@/shared/api/routes"

const activeTab = ref("pending")
const loading = ref(false)
const approvals = ref<any[]>([])

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.get(API.EXECUTIONS, { params: { page_size: 20, status: "awaiting_approval" } })
    if (res.data?.code === 0) {
      approvals.value = (res.data.data?.items || []).map((e: any) => ({
        execution_type: e.execution_type || "-", target: (e.asset_ids || []).join(", ") || "-",
        risk_level: e.risk_level || "medium", applicant: "-", reason: "-", created_at: e.created_at || "-"
      }))
    }
  } catch (e) { console.error(e) } finally { loading.value = false }
})
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
</style>
