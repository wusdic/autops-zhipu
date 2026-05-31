<template>
  <el-timeline>
    <el-timeline-item
      v-for="(item, idx) in items"
      :key="idx"
      :timestamp="item.time || item.created_at"
      :type="typeMap[item.type || item.severity] || 'primary'"
      :icon="item.icon"
      placement="top"
    >
      <el-card shadow="hover" :body-style="{ padding: '12px' }">
        <div v-if="item.title" style="font-weight: 600; margin-bottom: 4px">{{ item.title }}</div>
        <div style="color: #666; font-size: 13px">{{ item.description || item.content || item.message }}</div>
        <div v-if="item.user" style="color: #999; font-size: 12px; margin-top: 4px">操作人: {{ item.user }}</div>
      </el-card>
    </el-timeline-item>
  </el-timeline>
  <el-empty v-if="!items.length" description="暂无时间线记录" />
</template>

<script setup lang="ts">
defineProps<{ items: Array<Record<string, any>> }>()
const typeMap: Record<string, string> = { critical: 'danger', high: 'warning', info: 'primary', success: 'success' }
</script>
