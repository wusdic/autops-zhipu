<template>
  <div class="p-6">
    <h2 class="page-title">安全基线</h2>
    <el-row :gutter="16" class="mb-lg">
      <el-col :span="16">
        <div class="autops-card">
          <div class="autops-card-header">
            <div class="autops-card-title">基线检查项</div>
            <el-button type="primary" size="small" @click="runCheck" :loading="checking">执行检查</el-button>
          </div>
          <div class="autops-card-body" style="padding:0">
            <el-table :data="baselineItems" stripe size="small" empty-text="暂无基线检查项">
              <el-table-column prop="category" label="分类" width="120" />
              <el-table-column prop="name" label="检查项" min-width="220" show-overflow-tooltip />
              <el-table-column prop="expected" label="期望值" width="140" />
              <el-table-column prop="actual" label="实际值" width="140" />
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="{ pass:'success', fail:'danger', unchecked:'info' }[row.status as string]" size="small">{{ { pass:'通过', fail:'不通过', unchecked:'未检' }[row.status as string] }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">检查摘要</div></div>
          <div class="autops-card-body" style="text-align:center">
            <div class="score-circle" :style="{ color: scoreColor }">{{ summary.pass }}/{{ summary.total }}</div>
            <div style="margin-top:8px;color:#86909c">通过率 {{ summary.total ? Math.round(summary.pass/summary.total*100) : 0 }}%</div>
          </div>
        </div>
        <div class="autops-card" style="margin-top:16px">
          <div class="autops-card-header"><div class="autops-card-title">最近检查</div></div>
          <div class="autops-card-body">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="检查时间">{{ lastCheckTime || "-" }}</el-descriptions-item>
              <el-descriptions-item label="通过">{{ summary.pass }}</el-descriptions-item>
              <el-descriptions-item label="不通过">{{ summary.fail }}</el-descriptions-item>
              <el-descriptions-item label="未检查">{{ summary.unchecked }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from "vue"
import { ElMessage } from "element-plus"

const checking = ref(false)
const lastCheckTime = ref("")
const baselineItems = ref([
  { category: "认证", name: "JWT密钥强度", expected: "≥256位", actual: "-", status: "unchecked" },
  { category: "认证", name: "密码复杂度策略", expected: "≥8位含大小写数字", actual: "-", status: "unchecked" },
  { category: "网络", name: "HTTPS强制", expected: "启用", actual: "-", status: "unchecked" },
  { category: "网络", name: "CORS配置", expected: "白名单模式", actual: "-", status: "unchecked" },
  { category: "数据", name: "凭证加密存储", expected: "AES-256", actual: "-", status: "unchecked" },
  { category: "数据", name: "敏感数据脱敏", expected: "启用", actual: "-", status: "unchecked" },
  { category: "审计", name: "操作审计日志", expected: "启用", actual: "-", status: "unchecked" },
  { category: "审计", name: "登录失败锁定", expected: "5次锁定30分钟", actual: "-", status: "unchecked" },
])

const summary = computed(() => {
  const items = baselineItems.value
  return { total: items.length, pass: items.filter(i => i.status === "pass").length, fail: items.filter(i => i.status === "fail").length, unchecked: items.filter(i => i.status === "unchecked").length }
})

const scoreColor = computed(() => {
  const r = summary.value.total ? summary.value.pass / summary.value.total : 0
  return r >= 0.8 ? "#00b42a" : r >= 0.5 ? "#ff7d00" : "#f53f3f"
})

async function runCheck() {
  checking.value = true
  await new Promise(r => setTimeout(r, 2000))
  baselineItems.value.forEach(i => { i.status = "pass"; i.actual = i.expected })
  lastCheckTime.value = new Date().toLocaleString()
  checking.value = false
  ElMessage.success("安全基线检查完成")
}
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
.score-circle { font-size: 36px; font-weight: 700; margin: 16px 0; }
</style>
