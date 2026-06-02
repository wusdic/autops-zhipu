<template>
  <div class="p-6">
    <div class="page-header">
      <h2 class="page-title">发现结果</h2>
      <div class="header-actions">
        <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 140px; margin-right: 12px">
          <el-option label="待确认" value="pending" /><el-option label="已纳管" value="managed" /><el-option label="已忽略" value="ignored" /><el-option label="重复" value="duplicate" />
        </el-select>
        <el-button type="primary" :disabled="!selectedRows.length" @click="batchManage">批量纳管</el-button>
      </div>
    </div>
    <el-table :data="filteredResults" stripe v-loading="loading" @selection-change="(v: any) => selectedRows = v" empty-text="暂无发现结果">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="ip" label="IP地址" width="150" />
      <el-table-column prop="hostname" label="主机名" min-width="140" show-overflow-tooltip />
      <el-table-column prop="asset_type" label="识别类型" width="120">
        <template #default="{ row }"><el-tag size="small">{{ row.asset_type || "未识别" }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="fingerprint" label="指纹证据" min-width="160" show-overflow-tooltip />
      <el-table-column prop="risk_tags" label="风险标记" width="120">
        <template #default="{ row }">
          <el-tag v-for="tag in (row.risk_tags || [])" :key="tag" type="danger" size="small" style="margin-right: 4px">{{ tag }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusMap[row.status] || 'info'" size="small">{{ statusLabel[row.status] || row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="discovered_at" label="发现时间" width="160">
        <template #default="{ row }"><span class="text-tertiary">{{ row.discovered_at }}</span></template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending'" text type="primary" size="small" @click="manageAsset(row)">纳管</el-button>
          <el-button v-if="row.status === 'pending'" text type="warning" size="small" @click="ignoreAsset(row)">忽略</el-button>
          <el-button text type="primary" size="small" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue"
import api from "@/shared/api/client"
import { API } from "@/shared/api/routes"

const loading = ref(false)
const results = ref<any[]>([])
const filterStatus = ref("")
const selectedRows = ref<any[]>([])
const statusMap: Record<string, string> = { pending: "warning", managed: "success", ignored: "info", duplicate: "danger" }
const statusLabel: Record<string, string> = { pending: "待确认", managed: "已纳管", ignored: "已忽略", duplicate: "重复" }

const filteredResults = computed(() => filterStatus.value ? results.value.filter(r => r.status === filterStatus.value) : results.value)
function manageAsset(row: any) { row.status = "managed" }
function ignoreAsset(row: any) { row.status = "ignored" }
function batchManage() { selectedRows.value.forEach(r => { r.status = "managed" }) }
function viewDetail(row: any) { /* TODO: drawer */ }

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.get(API.ASSETS, { params: { page_size: 100 } })
    if (res.data?.code === 0) {
      results.value = (res.data.data?.items || []).map((a: any) => ({
        ip: a.ip || a.host || "-", hostname: a.name || "-", asset_type: a.asset_type || "unknown",
        fingerprint: a.os_info || "-", risk_tags: [], status: a.reachability === "unknown" ? "pending" : "managed",
        discovered_at: a.created_at || "-"
      }))
    }
  } catch (e) { console.error(e) } finally { loading.value = false }
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
.header-actions { display: flex; align-items: center; }
.text-tertiary { color: #86909c; font-size: 12px; }
</style>
