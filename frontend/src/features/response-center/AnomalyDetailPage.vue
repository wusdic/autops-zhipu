<template>
  <div class="p-6">
    <el-page-header @back="$router.back()" title="返回异常列表" content="异常详情" />
    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="16">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">异常信息</div></div>
          <div class="autops-card-body">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="异常标题">{{ anomaly.title }}</el-descriptions-item>
              <el-descriptions-item label="严重级别"><el-tag type="danger">中</el-tag></el-descriptions-item>
              <el-descriptions-item label="来源">监控告警</el-descriptions-item>
              <el-descriptions-item label="关联资产">-</el-descriptions-item>
              <el-descriptions-item label="状态"><el-tag type="warning">待处理</el-tag></el-descriptions-item>
              <el-descriptions-item label="发现时间">-</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
        <!-- 证据面板 -->
        <div class="autops-card" style="margin-top:16px">
          <div class="autops-card-header"><div class="autops-card-title">证据</div></div>
          <div class="autops-card-body"><el-empty description="暂无证据数据" /></div>
        </div>
        <!-- AI分析 -->
        <div class="autops-card" style="margin-top:16px">
          <div class="autops-card-header">
            <div class="autops-card-title">AI 分析</div>
            <el-button type="primary" size="small">触发AI分析</el-button>
          </div>
          <div class="autops-card-body"><el-empty description="点击按钮触发AI分析" /></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">处置建议</div></div>
          <div class="autops-card-body"><el-empty description="等待AI分析结果" /></div>
        </div>
        <div class="autops-card" style="margin-top:16px">
          <div class="autops-card-header"><div class="autops-card-title">操作</div></div>
          <div class="autops-card-body" style="display:flex;flex-direction:column;gap:8px">
            <el-button type="primary">确认异常</el-button>
            <el-button>转工单</el-button>
            <el-button>触发策略</el-button>
            <el-button type="danger">关闭异常</el-button>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { reactive } from "vue"
const anomaly = reactive({ title: "异常详情" })
</script>
