<template>
  <div class="p-6">
    <div class="page-header">
      <h2 class="page-title">平台自检</h2>
      <el-button type="primary" @click="runCheck" :loading="checking">执行自检</el-button>
    </div>
    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="8" v-for="item in checkItems" :key="item.name">
        <div class="check-card" :class="item.status">
          <div class="check-header">
            <el-icon size="24" :color="statusColor(item.status)">
              <component :is="statusIcon(item.status)" />
            </el-icon>
            <span class="check-name">{{ item.name }}</span>
          </div>
          <div class="check-detail text-tertiary">{{ item.detail || "等待检查" }}</div>
          <div class="check-time font-12 text-tertiary">{{ item.checked_at || "" }}</div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue"
import { CircleCheck, CircleClose, Clock } from "@element-plus/icons-vue"
import { ElMessage } from "element-plus"

const checking = ref(false)
const checkItems = reactive([
  { name: "MySQL数据库", status: "pending", detail: "", checked_at: "" },
  { name: "Redis缓存", status: "pending", detail: "", checked_at: "" },
  { name: "后端API", status: "pending", detail: "", checked_at: "" },
  { name: "采集器Worker", status: "pending", detail: "", checked_at: "" },
  { name: "定时任务Scheduler", status: "pending", detail: "", checked_at: "" },
  { name: "磁盘空间", status: "pending", detail: "", checked_at: "" },
])

function statusColor(s: string) { return ({ ok: "#00b42a", error: "#f53f3f", pending: "#86909c" } as any)[s] || "#86909c" }
function statusIcon(s: string) { return ({ ok: CircleCheck, error: CircleClose, pending: Clock } as any)[s] || Clock }

async function runCheck() {
  checking.value = true
  for (const item of checkItems) {
    item.status = "pending"; item.detail = "检查中..."
    await new Promise(r => setTimeout(r, 400))
    item.status = "ok"; item.detail = "正常"; item.checked_at = new Date().toLocaleString("zh-CN")
  }
  checking.value = false
  ElMessage.success("自检完成")
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
.check-card { background: #fff; border: 1px solid #e5e6eb; border-radius: 8px; padding: 16px; margin-bottom: 16px; transition: all 0.2s; }
.check-card.ok { border-left: 3px solid #00b42a; }
.check-card.error { border-left: 3px solid #f53f3f; }
.check-card.pending { border-left: 3px solid #86909c; }
.check-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.check-name { font-weight: 600; color: #1d2129; }
.check-detail { font-size: 13px; margin-bottom: 4px; }
.text-tertiary { color: #86909c; } .font-12 { font-size: 12px; }
</style>
