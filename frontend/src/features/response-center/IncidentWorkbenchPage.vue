<template>
  <div class="incident-workbench-page autops-page-container">
    <!-- 故障工作台 + AI诊断/影响分析/风险分级/处置建议/关闭验证收敛为闭环 tab（去重 B1/B2） -->
    <PageHeader title="故障工作台" desc="故障处置闭环：工作台 → AI诊断 → 影响分析 → 风险分级 → 处置建议 → 关闭验证" />

    <el-tabs v-model="activeTab" class="incident-workbench-tabs">
      <el-tab-pane label="工作台" name="workbench" lazy>
        <IncidentResponsePage embedded />
      </el-tab-pane>
      <el-tab-pane label="AI 诊断" name="ai" lazy>
        <AiDiagnosisPage embedded />
      </el-tab-pane>
      <el-tab-pane label="影响分析" name="impact" lazy>
        <ImpactAnalysisPage embedded />
      </el-tab-pane>
      <el-tab-pane label="风险分级" name="risk" lazy>
        <RiskGradingPage embedded />
      </el-tab-pane>
      <el-tab-pane label="处置建议" name="suggestion" lazy>
        <ResponseSuggestionPage embedded />
      </el-tab-pane>
      <el-tab-pane label="关闭验证" name="closure" lazy>
        <ClosureVerificationPage embedded />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import IncidentResponsePage from './IncidentResponsePage.vue'
import AiDiagnosisPage from '@/features/knowledge-center/AiDiagnosisPage.vue'
import ImpactAnalysisPage from './ImpactAnalysisPage.vue'
import RiskGradingPage from './RiskGradingPage.vue'
import ResponseSuggestionPage from './ResponseSuggestionPage.vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import ClosureVerificationPage from './ClosureVerificationPage.vue'

const route = useRoute()
// 支持 ?tab=ai|impact|risk|suggestion|closure 深链（去重后旧路径重定向至此）
const valid = ['workbench', 'ai', 'impact', 'risk', 'suggestion', 'closure']
const q = String(route.query.tab || '')
const activeTab = ref(valid.includes(q) ? q : 'workbench')
</script>

<style scoped>
.incident-workbench-tabs { margin-top: var(--autops-space-md, 12px); }
</style>
