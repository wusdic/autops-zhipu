<template>
  <div class="p-6">
    <div class="page-header">
      <h2 class="page-title">外部集成</h2>
      <el-button type="primary"><el-icon><Plus /></el-icon> 添加集成</el-button>
    </div>
    <el-row :gutter="16">
      <el-col :xs="12" :sm="8" :md="6" v-for="item in integrations" :key="item.name">
        <div class="integration-card">
          <div class="int-header">
            <span class="int-name">{{ item.name }}</span>
            <el-tag :type="item.connected ? 'success' : 'info'" size="small">{{ item.connected ? '已连接' : '未连接' }}</el-tag>
          </div>
          <div class="int-type text-tertiary">{{ item.type }}</div>
          <div class="int-desc text-tertiary">{{ item.description }}</div>
          <div style="margin-top:12px">
            <el-button text type="primary" size="small">配置</el-button>
            <el-button text type="success" size="small">测试连接</el-button>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
import { Plus } from "@element-plus/icons-vue"

const integrations = ref([
  { name: "LDAP/AD", type: "认证", description: "企业目录服务集成", connected: false },
  { name: "邮件通知", type: "通知", description: "SMTP邮件发送", connected: false },
  { name: "Webhook", type: "事件", description: "外部事件推送", connected: false },
  { name: "Prometheus", type: "监控", description: "指标数据接入", connected: false },
])
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
.integration-card { background: #fff; border: 1px solid #e5e6eb; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
.int-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.int-name { font-weight: 600; color: #1d2129; }
.int-type { font-size: 12px; margin-bottom: 4px; }
.int-desc { font-size: 13px; }
.text-tertiary { color: #86909c; }
</style>
