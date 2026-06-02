<template>
  <div class="p-6">
    <el-page-header @back="$router.back()" title="返回" content="Dry-run 预演" />
    <div style="margin-top:16px">
      <el-alert type="info" title="Dry-run 模式：仅预演执行计划，不实际修改系统" show-icon :closable="false" style="margin-bottom:16px" />
      <el-row :gutter="16">
        <el-col :span="12">
          <div class="autops-card">
            <div class="autops-card-header"><div class="autops-card-title">执行计划</div></div>
            <div class="autops-card-body">
              <el-steps direction="vertical" :active="0">
                <el-step title="前置检查" description="验证目标资源状态" />
                <el-step title="执行动作" description="执行主要操作" />
                <el-step title="验证结果" description="确认操作是否成功" />
              </el-steps>
            </div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="autops-card">
            <div class="autops-card-header"><div class="autops-card-title">影响分析</div></div>
            <div class="autops-card-body">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="目标资源">-</el-descriptions-item>
                <el-descriptions-item label="影响范围">-</el-descriptions-item>
                <el-descriptions-item label="风险等级">-</el-descriptions-item>
                <el-descriptions-item label="预计变更">-</el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
          <div style="margin-top:16px;display:flex;gap:8px">
            <el-button type="primary">执行Dry-run</el-button>
            <el-button>返回编辑</el-button>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>
