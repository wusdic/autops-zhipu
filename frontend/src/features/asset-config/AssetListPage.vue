<template>
  <div>
    <h2>资产列表</h2>
    <el-table :data="[]" empty-text="暂无资产" stripe>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="asset_type" label="类型" />
      <el-table-column prop="ip" label="IP" />
      <el-table-column prop="status" label="状态" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
</script>
