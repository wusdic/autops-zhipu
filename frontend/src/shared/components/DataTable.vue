<template>
  <div class="data-table-wrapper">
    <div class="dt-header" v-if="title || $slots.toolbar">
      <div class="dt-title" v-if="title">{{ title }}</div>
      <slot name="toolbar" />
    </div>
    <el-table v-bind="$attrs" :data="data" :row-key="rowKey" v-loading="loading"
      stripe :empty-text="emptyText" style="width: 100%">
      <slot />
    </el-table>
    <div v-if="showPagination" class="dt-pagination">
      <el-pagination small
        v-model:current-page="currentPage"
        v-model:page-size="currentPageSize"
        :page-sizes="pageSizes"
        :total="total"
        :layout="paginationLayout"
        @size-change="$emit('page-change', currentPage, currentPageSize)"
        @current-change="$emit('page-change', currentPage, currentPageSize)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue"

const props = withDefaults(defineProps<{
  data: any[]
  loading?: boolean
  total?: number
  title?: string
  rowKey?: string
  emptyText?: string
  page?: number
  pageSize?: number
  pageSizes?: number[]
  showPagination?: boolean
  paginationLayout?: string
}>(), {
  loading: false, total: 0, rowKey: "id", emptyText: "暂无数据",
  page: 1, pageSize: 20, pageSizes: () => [10, 20, 50, 100],
  showPagination: true, paginationLayout: "total, sizes, prev, pager, next, jumper",
})

const emit = defineEmits<{ "update:page": [v: number]; "update:pageSize": [v: number]; "page-change": [page: number, size: number] }>()
const currentPage = computed({ get: () => props.page, set: v => emit("update:page", v) })
const currentPageSize = computed({ get: () => props.pageSize, set: v => emit("update:pageSize", v) })
</script>

<style scoped>
.data-table-wrapper { background: var(--autops-bg-1); border-radius: var(--autops-radius-md); border: 1px solid var(--autops-bg-4); }
.dt-header { display: flex; justify-content: space-between; align-items: center; padding: var(--autops-space-md) 16px; border-bottom: 1px solid var(--autops-bg-3); }
.dt-title { font-size: 15px; font-weight: 600; color: var(--autops-text-1); }
.dt-pagination { display: flex; justify-content: flex-end; padding: var(--autops-space-md) 16px; }
.data-table-wrapper :deep(.el-table) { --el-table-border-color: var(--autops-bg-3); }
</style>
