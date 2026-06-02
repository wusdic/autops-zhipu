<template>
  <div class="p-6">
    <h2 class="page-title">知识总览</h2>
    <el-row :gutter="16" class="mb-lg">
      <el-col :xs="12" :sm="6" v-for="card in statCards" :key="card.label">
        <div class="autops-metric-card">
          <div class="metric-label">{{ card.label }}</div>
          <div class="metric-value" :style="{ color: card.color }">{{ card.value }}</div>
        </div>
      </el-col>
    </el-row>
    <el-row :gutter="16">
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">最近更新</div></div>
          <div class="autops-card-body" style="padding:0">
            <el-table :data="recentItems" stripe size="small" empty-text="暂无知识">
              <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
              <el-table-column prop="category" label="分类" width="100">
                <template #default="{ row }"><el-tag size="small">{{ row.category }}</el-tag></template>
              </el-table-column>
              <el-table-column prop="updated_at" label="更新时间" width="140" />
              <el-table-column label="操作" width="60">
                <template #default><el-button text type="primary" size="small">查看</el-button></template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">知识分类统计</div></div>
          <div class="autops-card-body">
            <div v-for="cat in categories" :key="cat.name" class="cat-row">
              <span class="cat-name">{{ cat.name }}</span>
              <el-progress :percentage="cat.percentage" :stroke-width="10" style="flex:1;margin:0 12px" />
              <span class="text-tertiary font-12">{{ cat.count }}</span>
            </div>
          </div>
        </div>
        <div class="autops-card" style="margin-top:16px">
          <div class="autops-card-header"><div class="autops-card-title">热门知识</div></div>
          <div class="autops-card-body" style="padding:0">
            <el-table :data="hotItems" stripe size="small" empty-text="暂无">
              <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
              <el-table-column prop="hit_count" label="引用次数" width="90" />
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue"

const statCards = reactive([
  { label: "知识总数", value: 0, color: "#165dff" },
  { label: "标准方案", value: 0, color: "#00b42a" },
  { label: "经验沉淀", value: 0, color: "#ff7d00" },
  { label: "待审核", value: 0, color: "#f53f3f" },
])
const recentItems = ref<any[]>([])
const hotItems = ref<any[]>([])
const categories = ref<any[]>([])
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
.text-tertiary { color: #86909c; } .font-12 { font-size: 12px; }
.cat-row { display: flex; align-items: center; margin-bottom: 12px; }
.cat-name { width: 100px; font-size: 13px; }
</style>
