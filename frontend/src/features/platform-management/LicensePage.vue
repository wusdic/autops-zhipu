<template>
  <div class="p-6">
    <h2 class="page-title">授权许可</h2>
    <el-row :gutter="16">
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">当前授权</div></div>
          <div class="autops-card-body">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="授权类型">{{ license.type }}</el-descriptions-item>
              <el-descriptions-item label="授权对象">{{ license.holder }}</el-descriptions-item>
              <el-descriptions-item label="有效期至">
                <span :style="{ color: license.expired ? '#f53f3f' : '#00b42a' }">{{ license.expires_at }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="资产上限">{{ license.max_assets }}</el-descriptions-item>
              <el-descriptions-item label="当前资产">{{ license.current_assets }}</el-descriptions-item>
              <el-descriptions-item label="功能模块">{{ license.modules }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">更新授权</div></div>
          <div class="autops-card-body">
            <el-form label-width="80px">
              <el-form-item label="授权文件"><el-upload action="" :auto-upload="false" :limit="1"><el-button>选择文件</el-button></el-upload></el-form-item>
              <el-form-item label="授权密钥"><el-input type="textarea" :rows="4" v-model="licenseKey" placeholder="粘贴授权密钥" /></el-form-item>
              <el-form-item><el-button type="primary" @click="activate">激活</el-button></el-form-item>
            </el-form>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue"
import { ElMessage } from "element-plus"

const license = reactive({ type: "社区版", holder: "-", expires_at: "-", expired: false, max_assets: 100, current_assets: 0, modules: "基础模块" })
const licenseKey = ref("")

function activate() { if (!licenseKey.value) { ElMessage.warning("请输入授权密钥"); return } ElMessage.success("授权已更新") }
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
</style>
