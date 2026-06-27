<template>
  <div class="state-monitor-page">
    <!-- 统一页头：状态快照 + 状态变化合并为「状态监控」两 tab（去重 B4） -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">状态监控</div>
        <div class="autops-page-desc">资源当前快照与状态变更历史</div>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="state-monitor-tabs">
      <el-tab-pane label="当前快照" name="snapshot">
        <StateSnapshotPage embedded />
      </el-tab-pane>
      <el-tab-pane label="变更历史" name="changes">
        <StateChangePage embedded />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import StateSnapshotPage from './StateSnapshotPage.vue'
import StateChangePage from './StateChangePage.vue'

const route = useRoute()
// 支持 ?tab=changes 深链（去重后 /monitoring/state-changes 重定向至此）
const activeTab = ref(route.query.tab === 'changes' ? 'changes' : 'snapshot')
</script>

<style scoped>
.state-monitor-tabs { margin-top: var(--autops-space-md, 12px); }
</style>
