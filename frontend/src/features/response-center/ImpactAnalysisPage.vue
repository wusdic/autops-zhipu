<template>
  <div class="p-6">
    <h2 class="page-title">影响分析</h2>
    <el-row :gutter="16">
      <el-col :span="16">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">影响范围拓扑</div></div>
          <div class="autops-card-body"><div ref="topoRef" style="height:400px;display:flex;align-items:center;justify-content:center">
            <el-empty description="选择异常后展示影响范围拓扑图" :image-size="100" />
          </div></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">影响统计</div></div>
          <div class="autops-card-body">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="直接影响资产">0</el-descriptions-item>
              <el-descriptions-item label="间接影响资产">0</el-descriptions-item>
              <el-descriptions-item label="影响业务系统">0</el-descriptions-item>
              <el-descriptions-item label="受影响用户">0</el-descriptions-item>
              <el-descriptions-item label="预计损失">-</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
        <div class="autops-card" style="margin-top:16px">
          <div class="autops-card-header"><div class="autops-card-title">受影响资产列表</div></div>
          <div class="autops-card-body">
            <el-table :data="affectedAssets" stripe size="small" empty-text="暂无数据">
              <el-table-column prop="name" label="资产" min-width="120" />
              <el-table-column prop="impact_type" label="影响类型" width="100" />
              <el-table-column prop="level" label="影响程度" width="80" />
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
const topoRef = ref<HTMLElement>()
const affectedAssets = ref<any[]>([])
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
</style>
