<template>
  <div class="p-6">
    <div class="page-header">
      <h2 class="page-title">租户管理</h2>
      <el-button type="primary"><el-icon><Plus /></el-icon> 新建租户</el-button>
    </div>
    <el-table :data="tenants" stripe v-loading="loading" empty-text="暂无租户">
      <el-table-column prop="name" label="租户名称" min-width="160" />
      <el-table-column prop="code" label="租户编码" width="120" />
      <el-table-column prop="admin" label="管理员" width="120" />
      <el-table-column prop="user_count" label="用户数" width="80" />
      <el-table-column prop="asset_count" label="资产数" width="80" />
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">{{ row.status === 'active' ? '正常' : '停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="expire_at" label="到期时间" width="120" />
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" size="small">编辑</el-button>
          <el-button text type="danger" size="small">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { Plus } from "@element-plus/icons-vue"

const loading = ref(false)
const tenants = ref<any[]>([])
onMounted(() => { loading.value = false })
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
</style>
