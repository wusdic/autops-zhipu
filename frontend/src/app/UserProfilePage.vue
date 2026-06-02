<template>
  <div class="p-6">
    <el-card>
      <template #header>
        <div class="flex items-center gap-2"><el-icon><User /></el-icon><span>个人中心</span></div>
      </template>
      <el-tabs>
        <el-tab-pane label="基本信息">
          <el-form label-width="100px" class="max-w-lg">
            <el-form-item label="用户名"><el-input :model-value="username" disabled /></el-form-item>
            <el-form-item label="角色"><el-input :model-value="role" disabled /></el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="修改密码">
          <el-form label-width="100px" class="max-w-lg">
            <el-form-item label="当前密码"><el-input type="password" show-password /></el-form-item>
            <el-form-item label="新密码"><el-input type="password" show-password /></el-form-item>
            <el-form-item label="确认密码"><el-input type="password" show-password /></el-form-item>
            <el-form-item><el-button type="primary">保存</el-button></el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="通知偏好">
          <el-form label-width="120px" class="max-w-lg">
            <el-form-item label="告警通知"><el-switch /></el-form-item>
            <el-form-item label="审批通知"><el-switch /></el-form-item>
            <el-form-item label="报告完成通知"><el-switch /></el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import { User } from '@element-plus/icons-vue'
const username = ref('admin')
const role = ref('管理员')
</script>