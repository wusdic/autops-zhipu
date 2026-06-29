<template>
  <div class="business-report-page autops-page-container">
    <!-- 成品报告按类型收敛为「业务报告」一个入口（去重 步骤5） -->
    <PageHeader title="业务报告" desc="运维 / 资产 / 自动化 / 合规 各类成品报告" />

    <el-tabs v-model="activeTab" class="business-report-tabs">
      <el-tab-pane label="运维报告" name="ops" lazy>
        <OpsReportPage embedded />
      </el-tab-pane>
      <el-tab-pane label="资产报告" name="asset" lazy>
        <AssetReportPage embedded />
      </el-tab-pane>
      <el-tab-pane label="自动化报告" name="automation" lazy>
        <AutomationReportPage embedded />
      </el-tab-pane>
      <el-tab-pane label="合规报告" name="compliance" lazy>
        <ComplianceReportPage embedded />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/shared/components/PageHeader.vue'
import OpsReportPage from './OpsReportPage.vue'
import AssetReportPage from './AssetReportPage.vue'
import AutomationReportPage from './AutomationReportPage.vue'
import ComplianceReportPage from './ComplianceReportPage.vue'

const route = useRoute()
const valid = ['ops', 'asset', 'automation', 'compliance']
const q = String(route.query.tab || '')
const activeTab = ref(valid.includes(q) ? q : 'ops')
</script>

<style scoped>
.business-report-tabs { margin-top: var(--autops-space-md, 12px); }
</style>
