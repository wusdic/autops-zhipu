<template>
  <div class="p-6">
    <div class="page-header">
      <h2 class="page-title">AI 判断</h2>
    </div>
    <el-row :gutter="16">
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">输入上下文</div></div>
          <div class="autops-card-body">
            <el-form label-width="90px">
              <el-form-item label="异常描述"><el-input type="textarea" v-model="input.description" :rows="3" placeholder="描述异常现象" /></el-form-item>
              <el-form-item label="关联资产"><el-input v-model="input.asset" placeholder="资产名称或IP" /></el-form-item>
              <el-form-item label="附加证据"><el-input type="textarea" v-model="input.evidence" :rows="4" placeholder="粘贴日志、指标截图等" /></el-form-item>
              <el-form-item><el-button type="primary" @click="runDiagnosis" :loading="loading">开始AI诊断</el-button></el-form-item>
            </el-form>
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">AI 诊断结果</div></div>
          <div class="autops-card-body">
            <template v-if="result">
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="根因分析">{{ result.root_cause }}</el-descriptions-item>
                <el-descriptions-item label="置信度">
                  <el-progress :percentage="result.confidence" :stroke-width="8" style="width:160px" />
                </el-descriptions-item>
                <el-descriptions-item label="风险等级">
                  <el-tag :type="riskType(result.risk_level)">{{ result.risk_level }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="影响范围">{{ result.impact_scope }}</el-descriptions-item>
              </el-descriptions>
              <div style="margin-top:12px"><strong>建议动作：</strong></div>
              <div v-for="(a, i) in result.actions" :key="i" style="padding:8px 0;border-bottom:1px solid #f2f3f5">
                <div>{{ i+1 }}. {{ a.description }}</div>
                <div class="text-tertiary font-12">风险: {{ a.risk }} | 预计: {{ a.time }}</div>
              </div>
              <div style="margin-top:16px;display:flex;gap:8px">
                <el-button type="primary" size="small">采纳建议</el-button>
                <el-button size="small">转人工判断</el-button>
              </div>
            </template>
            <el-empty v-else description="输入异常信息后开始AI诊断" :image-size="80" />
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue"

const loading = ref(false)
const input = reactive({ description: "", asset: "", evidence: "" })
const result = ref<any>(null)

function riskType(r: string) { return ({ low: "success", medium: "warning", high: "danger", unknown: "info" } as any)[r] || "info" }

async function runDiagnosis() {
  loading.value = true
  try {
    await new Promise(r => setTimeout(r, 2000))
    result.value = {
      root_cause: "基于证据分析，疑似磁盘空间不足导致服务不可用",
      confidence: 68,
      risk_level: "medium",
      impact_scope: "该服务器上所有服务受影响",
      actions: [
        { description: "清理/tmp和日志目录", risk: "low", time: "5分钟" },
        { description: "扩容磁盘到200GB", risk: "medium", time: "30分钟" },
      ],
    }
  } finally { loading.value = false }
}
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
.text-tertiary { color: #86909c; } .font-12 { font-size: 12px; }
</style>
