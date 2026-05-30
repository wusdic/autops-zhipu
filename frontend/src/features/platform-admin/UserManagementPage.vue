<template>
  <div>
    <h2>用户管理</h2>
    <el-table :data="[]" empty-text="暂无用户" stripe>
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="display_name" label="显示名" />
      <el-table-column prop="status" label="状态" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
</script>
