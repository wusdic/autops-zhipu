<template>
  <div>
    <h2>告警列表</h2>
    <el-table :data="[]" empty-text="暂无告警" stripe>
      <el-table-column prop="title" label="告警" />
      <el-table-column prop="severity" label="严重度" />
      <el-table-column prop="status" label="状态" />
      <el-table-column prop="created_at" label="时间" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
</script>
