<template>
  <div class="p-6">
    <h2 class="page-title">升级维护</h2>
    <el-row :gutter="16" class="mb-lg">
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">当前版本</div></div>
          <div class="autops-card-body">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="版本号">{{ versionInfo.current }}</el-descriptions-item>
              <el-descriptions-item label="构建时间">{{ versionInfo.build_time }}</el-descriptions-item>
              <el-descriptions-item label="数据库版本">{{ versionInfo.db_version }}</el-descriptions-item>
              <el-descriptions-item label="最后升级">{{ versionInfo.last_upgrade }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">升级操作</div></div>
          <div class="autops-card-body" style="display:flex;flex-direction:column;gap:8px">
            <el-upload action="" :auto-upload="false" :limit="1" accept=".tar.gz,.zip">
              <el-button type="primary">选择升级包</el-button>
            </el-upload>
            <el-button @click="checkUpgrade" :loading="checking">检查更新</el-button>
            <el-button type="warning" @click="preCheck" :loading="prechecking">升级预检</el-button>
            <el-button type="danger" @click="startUpgrade" :disabled="!canUpgrade">执行升级</el-button>
          </div>
        </div>
      </el-col>
    </el-row>
    <div class="autops-card">
      <div class="autops-card-header"><div class="autops-card-title">升级历史</div></div>
      <div class="autops-card-body" style="padding:0">
        <el-table :data="history" stripe size="small" empty-text="暂无升级记录">
          <el-table-column prop="version" label="版本" width="120" />
          <el-table-column prop="upgraded_at" label="升级时间" width="160" />
          <el-table-column prop="operator" label="操作人" width="100" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="{ success:'success', failed:'danger', rolled_back:'warning' }[row.status as string]" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="detail" label="详情" min-width="200" show-overflow-tooltip />
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button v-if="row.status === 'failed'" text type="warning" size="small">回滚</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue"
import { ElMessage } from "element-plus"

const versionInfo = reactive({ current: "v1.0.0", build_time: "-", db_version: "-", last_upgrade: "-" })
const checking = ref(false)
const prechecking = ref(false)
const canUpgrade = ref(false)
const history = ref<any[]>([])

async function checkUpgrade() { checking.value = true; await new Promise(r => setTimeout(r, 1500)); checking.value = false; ElMessage.info("当前已是最新版本") }
async function preCheck() { prechecking.value = true; await new Promise(r => setTimeout(r, 2000)); prechecking.value = false; canUpgrade.value = true; ElMessage.success("预检通过") }
function startUpgrade() { ElMessage.warning("升级将暂停服务，请确认已备份") }
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
</style>
