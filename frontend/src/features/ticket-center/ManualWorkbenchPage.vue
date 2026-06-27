<template>
  <div class="manual-workbench-page autops-page-container">
    <!-- 统一页头：人工确认台 + 人工处置台合并为「人工工作台」两 tab（去重 B3） -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">人工工作台</div>
        <div class="autops-page-desc">人工确认自动/AI/策略操作，并处置需人工干预的工单</div>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="manual-workbench-tabs">
      <el-tab-pane label="待确认" name="confirm">
        <ManualConfirmPage embedded />
      </el-tab-pane>
      <el-tab-pane label="待处置" name="handling">
        <ManualHandlingPage embedded />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import ManualConfirmPage from '@/features/response-center/ManualConfirmPage.vue'
import ManualHandlingPage from './ManualHandlingPage.vue'

const route = useRoute()
// 支持 ?tab=confirm 深链（去重后 /manual-confirm 重定向至此）
const activeTab = ref(route.query.tab === 'confirm' ? 'confirm' : 'handling')
</script>

<style scoped>
.manual-workbench-tabs { margin-top: var(--autops-space-md, 12px); }
</style>
