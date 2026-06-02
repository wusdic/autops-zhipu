<template>
  <div class="p-6">
    <h2 class="page-title">关闭验证</h2>
    <el-alert type="warning" title="关闭异常前需验证所有指标恢复正常，确保问题真正解决" show-icon :closable="false" style="margin-bottom:16px" />
    <el-row :gutter="16">
      <el-col :span="16">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">验证检查项</div></div>
          <div class="autops-card-body">
            <el-table :data="checkItems" stripe empty-text="暂无验证项">
              <el-table-column prop="name" label="检查项" min-width="200" show-overflow-tooltip />
              <el-table-column prop="type" label="类型" width="100">
                <template #default="{ row }"><el-tag size="small">{{ row.type }}</el-tag></template>
              </el-table-column>
              <el-table-column prop="expected" label="期望值" width="120" />
              <el-table-column prop="actual" label="实际值" width="120" />
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="{ pass:'success', fail:'danger', pending:'info' }[row.status as string]" size="small">{{ { pass:'通过', fail:'失败', pending:'待验' }[row.status as string] }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80">
                <template #default="{ row }">
                  <el-button text type="primary" size="small" @click="verify(row)">验证</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">验证结果</div></div>
          <div class="autops-card-body" style="text-align:center">
            <div class="verify-stat">
              <span class="verify-pass">0</span><span class="text-tertiary"> / 0 通过</span>
            </div>
          </div>
        </div>
        <div class="autops-card" style="margin-top:16px">
          <div class="autops-card-header"><div class="autops-card-title">操作</div></div>
          <div class="autops-card-body" style="display:flex;flex-direction:column;gap:8px">
            <el-button type="primary" @click="verifyAll">全部验证</el-button>
            <el-button type="success" :disabled="true">确认关闭</el-button>
            <el-button @click="addCheckItem">添加检查项</el-button>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
import { ElMessage } from "element-plus"

const checkItems = ref<any[]>([])

function verify(row: any) { row.status = "pass"; ElMessage.success("验证通过") }
function verifyAll() { checkItems.value.forEach(i => { i.status = "pass" }); ElMessage.success("全部验证通过") }
function addCheckItem() { ElMessage.info("添加检查项") }
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.text-tertiary { color: #86909c; }
.verify-stat { font-size: 24px; margin: 16px 0; }
.verify-pass { color: #00b42a; font-weight: 700; font-size: 32px; }
</style>
