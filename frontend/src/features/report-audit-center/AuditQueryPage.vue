<template>
  <div class="p-6">
    <h2 class="page-title">审计查询</h2>
    <div class="autops-card mb-lg">
      <div class="autops-card-header"><div class="autops-card-title">查询条件</div></div>
      <div class="autops-card-body">
        <el-form :inline="true" @submit.prevent="search">
          <el-form-item label="操作人"><el-input v-model="filter.user" placeholder="用户名" clearable style="width:140px" /></el-form-item>
          <el-form-item label="操作类型"><el-select v-model="filter.action" clearable style="width:140px">
            <el-option label="创建" value="create" /><el-option label="修改" value="update" /><el-option label="删除" value="delete" />
            <el-option label="登录" value="login" /><el-option label="执行" value="execute" />
          </el-select></el-form-item>
          <el-form-item label="资源"><el-input v-model="filter.resource" placeholder="资源名称" clearable style="width:140px" /></el-form-item>
          <el-form-item label="时间范围"><el-date-picker v-model="filter.dateRange" type="datetimerange" range-separator="至" style="width:340px" /></el-form-item>
          <el-form-item><el-button type="primary" @click="search">查询</el-button><el-button @click="resetFilter">重置</el-button></el-form-item>
        </el-form>
      </div>
    </div>
    <div class="autops-card">
      <div class="autops-card-body" style="padding:0">
        <el-table :data="logs" stripe v-loading="loading" empty-text="暂无审计记录">
          <el-table-column prop="created_at" label="时间" width="170" />
          <el-table-column prop="user_name" label="操作人" width="100" />
          <el-table-column prop="action" label="操作" width="80">
            <template #default="{ row }"><el-tag :type="actionColor(row.action)" size="small">{{ row.action }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="resource_type" label="资源类型" width="100" />
          <el-table-column prop="resource_name" label="资源" min-width="160" show-overflow-tooltip />
          <el-table-column prop="detail" label="详情" min-width="200" show-overflow-tooltip />
          <el-table-column prop="ip" label="来源IP" width="130" />
        </el-table>
      </div>
      <div style="padding:12px;display:flex;justify-content:flex-end">
        <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total" layout="total, prev, pager, next" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue"
import api from "@/shared/api/client"
import { API } from "@/shared/api/routes"

const loading = ref(false)
const logs = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filter = reactive({ user: "", action: "", resource: "", dateRange: [] as any[] })

function actionColor(a: string) { return ({ create: "success", update: "", delete: "danger", login: "info", execute: "warning" } as any)[a] || "info" }
function resetFilter() { filter.user = ""; filter.action = ""; filter.resource = ""; filter.dateRange = [] }

async function search() {
  loading.value = true
  try {
    const res = await api.get(API.AUDIT_LOGS, { params: { page: page.value, page_size: pageSize.value, user_name: filter.user || undefined, action: filter.action || undefined } })
    if (res.data?.code === 0) { logs.value = res.data.data?.items || []; total.value = res.data.data?.total || 0 }
  } catch (e) {} finally { loading.value = false }
}

onMounted(() => search())
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
</style>
