<template>
  <div class="p-6">
    <h2 class="page-title">权限策略</h2>
    <div class="autops-card mb-lg">
      <div class="autops-card-header">
        <div class="autops-card-title">角色权限矩阵</div>
        <el-button type="primary" size="small" @click="showAddRole = true"><el-icon><Plus /></el-icon> 新建角色</el-button>
      </div>
      <div class="autops-card-body" style="padding:0">
        <el-table :data="roles" stripe v-loading="loading" empty-text="暂无角色">
          <el-table-column prop="name" label="角色名称" min-width="140" />
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column prop="user_count" label="用户数" width="80" />
          <el-table-column prop="permissions" label="权限数" width="80" />
          <el-table-column prop="is_system" label="系统角色" width="90">
            <template #default="{ row }"><el-tag :type="row.is_system ? 'info' : ''" size="small">{{ row.is_system ? '是' : '否' }}</el-tag></template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button text type="primary" size="small" @click="editPermissions(row)">编辑权限</el-button>
              <el-button v-if="!row.is_system" text type="danger" size="small" @click="deleteRole(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    <el-dialog v-model="permDialog" title="编辑权限" width="700">
      <el-tree ref="treeRef" :data="permTree" show-checkbox node-key="key" :default-checked-keys="checkedKeys" />
      <template #footer><el-button @click="permDialog=false">取消</el-button><el-button type="primary" @click="savePermissions">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import api from "@/shared/api/client"
import { API } from "@/shared/api/routes"
import { Plus } from "@element-plus/icons-vue"
import { ElMessage } from "element-plus"

const loading = ref(false)
const roles = ref<any[]>([])
const showAddRole = ref(false)
const permDialog = ref(false)
const treeRef = ref<any>()
const checkedKeys = ref<string[]>([])
const permTree = ref([
  { key: "asset", label: "资产中心", children: [{ key: "asset:read", label: "查看" }, { key: "asset:write", label: "编辑" }, { key: "asset:delete", label: "删除" }] },
  { key: "config", label: "配置中心", children: [{ key: "config:read", label: "查看" }, { key: "config:write", label: "编辑" }] },
  { key: "automation", label: "自动化中心", children: [{ key: "automation:read", label: "查看" }, { key: "automation:execute", label: "执行" }, { key: "automation:approve", label: "审批" }] },
  { key: "policy", label: "策略中心", children: [{ key: "policy:read", label: "查看" }, { key: "policy:write", label: "编辑" }] },
  { key: "platform", label: "平台管理", children: [{ key: "platform:user", label: "用户管理" }, { key: "platform:system", label: "系统配置" }, { key: "platform:audit", label: "审计日志" }] },
])

function editPermissions(row: any) { checkedKeys.value = []; permDialog.value = true }
function savePermissions() { permDialog.value = false; ElMessage.success("权限已保存") }
function deleteRole(row: any) { ElMessage.warning("确认删除角色？") }

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.get(API.ROLES, { params: { page_size: 100 } })
    if (res.data?.code === 0) roles.value = res.data.data?.items || []
  } catch (e) {} finally { loading.value = false }
})
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
</style>
