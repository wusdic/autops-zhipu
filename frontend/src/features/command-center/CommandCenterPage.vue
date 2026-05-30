<template>
  <div class="command-center">
    <h2>运维指挥台</h2>
    <el-row :gutter="20">
      <el-col :span="6"><el-card><el-statistic title="活跃告警" :value="0" /></el-card></el-col>
      <el-col :span="6"><el-card><el-statistic title="今日工单" :value="0" /></el-card></el-col>
      <el-col :span="6"><el-card><el-statistic title="采集成功率" :value="'--'" /></el-card></el-col>
      <el-col :span="6"><el-card><el-statistic title="平台健康" :value="'--'" /></el-card></el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.command-center h2 { margin-bottom: 20px; }
</style>
