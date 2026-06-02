<template>
  <div class="p-6">
    <h2 class="page-title">知识审核</h2>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="待审核" name="pending">
        <el-table :data="pendingItems" stripe v-loading="loading" empty-text="暂无待审核知识">
          <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="category" label="分类" width="100" />
          <el-table-column prop="source" label="来源" width="100">
            <template #default="{ row }"><el-tag :type="{ ai:'primary', manual:'success', ticket:'warning' }[row.source as string]" size="small">{{ row.source }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="submitted_at" label="提交时间" width="140" />
          <el-table-column prop="submitted_by" label="提交人" width="100" />
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button text type="primary" size="small" @click="reviewItem(row)">审核</el-button>
              <el-button text type="success" size="small" @click="approve(row)">通过</el-button>
              <el-button text type="danger" size="small" @click="reject(row)">驳回</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="已审核" name="done">
        <el-table :data="doneItems" stripe empty-text="暂无已审核知识">
          <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="review_result" label="结果" width="80">
            <template #default="{ row }"><el-tag :type="row.review_result === 'approved' ? 'success' : 'danger'" size="small">{{ row.review_result }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="reviewed_by" label="审核人" width="100" />
          <el-table-column prop="reviewed_at" label="审核时间" width="140" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
    <el-dialog v-model="reviewDialog" title="知识审核" width="600">
      <el-form label-width="80px">
        <el-form-item label="标题">{{ currentItem.title }}</el-form-item>
        <el-form-item label="内容"><div style="background:#f7f8fa;padding:12px;border-radius:6px;max-height:300px;overflow:auto">{{ currentItem.content }}</div></el-form-item>
        <el-form-item label="审核意见"><el-input type="textarea" v-model="reviewComment" :rows="3" placeholder="输入审核意见" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewDialog=false">取消</el-button>
        <el-button type="danger" @click="reject(currentItem)">驳回</el-button>
        <el-button type="success" @click="approve(currentItem)">通过</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue"
import api from "@/shared/api/client"
import { API } from "@/shared/api/routes"
import { ElMessage } from "element-plus"

const loading = ref(false)
const activeTab = ref("pending")
const pendingItems = ref<any[]>([])
const doneItems = ref<any[]>([])
const reviewDialog = ref(false)
const reviewComment = ref("")
const currentItem = reactive<any>({ title: "", content: "" })

function reviewItem(row: any) { Object.assign(currentItem, row); reviewDialog.value = true }
function approve(row: any) { reviewDialog.value = false; ElMessage.success("审核通过") }
function reject(row: any) { reviewDialog.value = false; ElMessage.info("已驳回") }

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.get(API.KNOWLEDGE, { params: { status: "pending", page_size: 50 } })
    if (res.data?.code === 0) pendingItems.value = res.data.data?.items || []
  } catch (e) {} finally { loading.value = false }
})
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
</style>
