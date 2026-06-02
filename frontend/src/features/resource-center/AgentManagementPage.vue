<template>
  <div class="p-6">
    <h2 class="page-title">Agent 管理</h2>
    <el-table :data="agents" stripe v-loading="loading" empty-text="暂无Agent">
      <el-table-column prop="hostname" label="主机名" min-width="140" show-overflow-tooltip />
      <el-table-column prop="ip" label="IP地址" width="150" />
      <el-table-column prop="status" label="在线状态" width="100">
        <template #default="{ row }">
          <span class="status-dot" :class="row.status === 'online' ? 'dot-online' : 'dot-offline'"></span>
          {{ row.status === "online" ? "在线" : "离线" }}
        </template>
      </el-table-column>
      <el-table-column prop="version" label="版本" width="100" />
      <el-table-column prop="last_heartbeat" label="最后心跳" width="170">
        <template #default="{ row }"><span class="text-tertiary">{{ row.last_heartbeat || "-" }}</span></template>
      </el-table-column>
      <el-table-column prop="bound_asset" label="绑定资源" min-width="140" show-overflow-tooltip />
      <el-table-column prop="capabilities" label="能力" min-width="160">
        <template #default="{ row }">
          <el-tag v-for="cap in (row.capabilities || [])" :key="cap" size="small" style="margin-right: 4px">{{ cap }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" size="small" @click="upgradeAgent(row)">升级</el-button>
          <el-button text type="danger" size="small" @click="removeAgent(row)">移除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { ElMessage } from "element-plus"

const loading = ref(false)
const agents = ref<any[]>([])

function upgradeAgent(row: any) { ElMessage.info(`升级 Agent ${row.hostname} 开发中`) }
function removeAgent(row: any) { agents.value = agents.value.filter(a => a !== row) }

onMounted(() => { loading.value = false })
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.text-tertiary { color: #86909c; font-size: 12px; }
.status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; }
.dot-online { background: #00b42a; } .dot-offline { background: #c9cdd4; }
</style>
