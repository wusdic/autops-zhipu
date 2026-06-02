<template>
  <div class="p-6">
    <el-page-header @back="$router.back()" title="返回策略列表" content="策略编辑" />
    <div style="margin-top:16px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="策略名称"><el-input v-model="form.name" placeholder="输入策略名称" /></el-form-item>
        <el-form-item label="触发条件">
          <el-select v-model="form.trigger_type"><el-option label="巡检异常" value="inspection" /><el-option label="监控告警" value="monitoring" /><el-option label="日志异常" value="log" /><el-option label="配置漂移" value="config_drift" /></el-select>
        </el-form-item>
        <el-form-item label="适用范围"><el-input v-model="form.scope" placeholder="资产组、标签或IP范围" /></el-form-item>
        <el-form-item label="风险等级">
          <el-radio-group v-model="form.risk_level"><el-radio value="low">低风险</el-radio><el-radio value="medium">中风险</el-radio><el-radio value="high">高风险</el-radio></el-radio-group>
        </el-form-item>
        <el-form-item label="需要审批"><el-switch v-model="form.requires_approval" /></el-form-item>
        <el-form-item label="动作链">
          <div v-for="(action, idx) in form.action_chain" :key="idx" style="display:flex;gap:8px;margin-bottom:8px">
            <el-input v-model="action.type" placeholder="动作类型" style="flex:1" />
            <el-input v-model="action.target" placeholder="目标" style="flex:2" />
            <el-button text type="danger" @click="form.action_chain.splice(idx, 1)">删除</el-button>
          </div>
          <el-button @click="form.action_chain.push({ type: '', target: '' })">+ 添加动作</el-button>
        </el-form-item>
        <el-form-item><el-button type="primary">保存策略</el-button><el-button @click="$router.back()">取消</el-button></el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from "vue"
const form = reactive({ name: "", trigger_type: "monitoring", scope: "", risk_level: "low", requires_approval: false, action_chain: [] as { type: string; target: string }[] })
</script>
