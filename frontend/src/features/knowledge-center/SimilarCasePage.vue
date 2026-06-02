<template>
  <div class="p-6">
    <h2 class="page-title">相似案例</h2>
    <div class="autops-card mb-lg">
      <div class="autops-card-body">
        <el-form :inline="true" @submit.prevent="search">
          <el-form-item label="关键词"><el-input v-model="keyword" placeholder="输入异常描述或关键词" style="width:300px" clearable /></el-form-item>
          <el-form-item label="资产类型"><el-select v-model="assetType" clearable style="width:140px">
            <el-option label="Linux" value="linux" /><el-option label="Windows" value="windows" /><el-option label="数据库" value="database" />
          </el-select></el-form-item>
          <el-form-item><el-button type="primary" @click="search">搜索相似案例</el-button></el-form-item>
        </el-form>
      </div>
    </div>
    <el-row :gutter="16">
      <el-col :span="24">
        <div class="autops-card">
          <div class="autops-card-body" style="padding:0">
            <el-table :data="cases" stripe v-loading="loading" empty-text="暂无相似案例">
              <el-table-column prop="title" label="案例标题" min-width="200" show-overflow-tooltip />
              <el-table-column prop="similarity" label="相似度" width="80">
                <template #default="{ row }"><span :style="{ color: row.similarity >= 80 ? '#00b42a' : '#ff7d00' }">{{ row.similarity }}%</span></template>
              </el-table-column>
              <el-table-column prop="asset_type" label="资产类型" width="100" />
              <el-table-column prop="root_cause" label="根因" min-width="160" show-overflow-tooltip />
              <el-table-column prop="resolution" label="解决方案" min-width="200" show-overflow-tooltip />
              <el-table-column prop="occurred_at" label="发生时间" width="140" />
              <el-table-column label="操作" width="80">
                <template #default><el-button text type="primary" size="small">详情</el-button></template>
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
import { ElMessage } from "element-plus"

const keyword = ref("")
const assetType = ref("")
const loading = ref(false)
const cases = ref<any[]>([])

async function search() {
  if (!keyword.value) { ElMessage.warning("请输入关键词"); return }
  loading.value = true
  await new Promise(r => setTimeout(r, 1000))
  loading.value = false
  ElMessage.info("搜索完成")
}
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
</style>
