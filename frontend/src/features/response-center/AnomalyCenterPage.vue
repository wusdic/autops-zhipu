<template>
  <div class="anomaly-center-page autops-page-container">
    <!-- 统一页头：异常总览 + 异常列表合并为「异常中心」两 tab（去重 C） -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">异常中心</div>
        <div class="autops-page-desc">异常统计总览与异常明细列表</div>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="anomaly-center-tabs">
      <el-tab-pane label="总览" name="overview">
        <AnomalyOverviewPage embedded />
      </el-tab-pane>
      <el-tab-pane label="列表" name="list">
        <AnomalyListPage embedded />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import AnomalyOverviewPage from './AnomalyOverviewPage.vue'
import AnomalyListPage from './AnomalyListPage.vue'

const route = useRoute()
// 支持 ?tab=list 深链（去重后 /anomaly/list 重定向至此）
const activeTab = ref(route.query.tab === 'list' ? 'list' : 'overview')
</script>

<style scoped>
.anomaly-center-tabs { margin-top: var(--autops-space-md, 12px); }
</style>
