<template>
  <div class="anomaly-center-page autops-page-container">
    <!-- 异常总览 + 异常列表合并为「异常中心」两 tab（去重 C） -->
    <PageHeader title="异常中心" desc="异常统计总览与异常明细列表" />

    <el-tabs v-model="activeTab" class="anomaly-center-tabs">
      <el-tab-pane label="总览" name="overview" lazy>
        <AnomalyOverviewPage embedded />
      </el-tab-pane>
      <el-tab-pane label="列表" name="list" lazy>
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
import PageHeader from '@/shared/components/PageHeader.vue'

const route = useRoute()
// 支持 ?tab=list 深链（去重后 /anomaly/list 重定向至此）
const activeTab = ref(route.query.tab === 'list' ? 'list' : 'overview')
</script>

<style scoped>
.anomaly-center-tabs { margin-top: var(--autops-space-md, 12px); }
</style>
