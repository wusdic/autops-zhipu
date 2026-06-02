<template>
  <div class="p-6">
    <h2 class="page-title">资产报告</h2>
    <el-row :gutter="16" class="mb-lg">
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">资产概况</div></div>
          <div class="autops-card-body">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="资产总数">0</el-descriptions-item>
              <el-descriptions-item label="在线">0</el-descriptions-item>
              <el-descriptions-item label="离线">0</el-descriptions-item>
              <el-descriptions-item label="异常">0</el-descriptions-item>
              <el-descriptions-item label="今日新增">0</el-descriptions-item>
              <el-descriptions-item label="今日变化">0</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">资产类型分布</div></div>
          <div class="autops-card-body"><el-empty description="暂无数据" :image-size="80" /></div>
        </div>
      </el-col>
    </el-row>
    <div class="autops-card">
      <div class="autops-card-header"><div class="autops-card-title">资产变化记录</div></div>
      <div class="autops-card-body" style="padding:0">
        <el-table :data="changes" stripe size="small" empty-text="暂无变化记录">
          <el-table-column prop="time" label="时间" width="160" />
          <el-table-column prop="asset_name" label="资产" min-width="160" />
          <el-table-column prop="change_type" label="变更类型" width="100">
            <template #default="{ row }"><el-tag size="small">{{ row.change_type }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="detail" label="详情" min-width="200" show-overflow-tooltip />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
const changes = ref<any[]>([])
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
</style>
