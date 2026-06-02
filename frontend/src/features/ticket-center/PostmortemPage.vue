<template>
  <div class="p-6">
    <h2 class="page-title">故障复盘</h2>
    <div class="autops-card mb-lg">
      <div class="autops-card-header">
        <div class="autops-card-title">复盘记录</div>
        <el-button type="primary" size="small" @click="createPostmortem"><el-icon><Plus /></el-icon> 新建复盘</el-button>
      </div>
      <div class="autops-card-body" style="padding:0">
        <el-table :data="postmortems" stripe v-loading="loading" empty-text="暂无复盘记录">
          <el-table-column prop="title" label="故障标题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="severity" label="严重级别" width="90">
            <template #default="{ row }">
              <el-tag :type="{ critical:'danger', high:'warning', medium:'', low:'info' }[row.severity as string]" size="small">{{ row.severity }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="occurred_at" label="发生时间" width="140" />
          <el-table-column prop="duration" label="持续时长" width="90" />
          <el-table-column prop="root_cause" label="根因" min-width="160" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="{ draft:'info', review:'warning', published:'success' }[row.status as string]" size="small">{{ { draft:'草稿', review:'审核中', published:'已发布' }[row.status as string] }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button text type="primary" size="small" @click="viewPostmortem(row)">查看</el-button>
              <el-button text size="small" @click="editPostmortem(row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { Plus } from "@element-plus/icons-vue"
import api from "@/shared/api/client"
import { API } from "@/shared/api/routes"
import { ElMessage } from "element-plus"

const loading = ref(false)
const postmortems = ref<any[]>([])

function createPostmortem() { ElMessage.info("跳转创建复盘") }
function viewPostmortem(row: any) { ElMessage.info("查看复盘详情") }
function editPostmortem(row: any) { ElMessage.info("编辑复盘") }

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.get(API.TICKETS, { params: { has_postmortem: true, page_size: 50 } })
    if (res.data?.code === 0) postmortems.value = res.data.data?.items || []
  } catch (e) {} finally { loading.value = false }
})
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
</style>
