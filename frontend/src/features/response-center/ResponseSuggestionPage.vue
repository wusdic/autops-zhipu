<template>
  <div class="p-6">
    <h2 class="page-title">处置建议</h2>
    <el-alert type="info" title="处置建议基于AI分析和知识库匹配生成，执行前请确认风险等级" show-icon :closable="false" style="margin-bottom:16px" />
    <el-row :gutter="16">
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">匹配的策略</div></div>
          <div class="autops-card-body">
            <el-table :data="matchedPolicies" stripe size="small" empty-text="暂无匹配策略">
              <el-table-column prop="name" label="策略名称" min-width="160" show-overflow-tooltip />
              <el-table-column prop="risk_level" label="风险" width="80">
                <template #default="{ row }">
                  <el-tag :type="{ low:'success', medium:'warning', high:'danger' }[row.risk_level as string]" size="small">{{ row.risk_level }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="match_score" label="匹配度" width="80" />
              <el-table-column label="操作" width="120">
                <template #default>
                  <el-button text type="primary" size="small">执行</el-button>
                  <el-button text size="small">Dry-run</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">知识库建议</div></div>
          <div class="autops-card-body">
            <el-table :data="knowledgeSuggestions" stripe size="small" empty-text="暂无知识库建议">
              <el-table-column prop="title" label="方案名称" min-width="160" show-overflow-tooltip />
              <el-table-column prop="source" label="来源" width="80" />
              <el-table-column prop="success_rate" label="成功率" width="80" />
              <el-table-column label="操作" width="80">
                <template #default><el-button text type="primary" size="small">查看</el-button></template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
const matchedPolicies = ref<any[]>([])
const knowledgeSuggestions = ref<any[]>([])
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
</style>
