<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2 class="login-title">AUTOPS</h2>
      <p class="login-subtitle">自治运维操作系统</p>
      <el-form :model="form" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" size="large" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width: 100%" :loading="loading" native-type="submit">
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/app/store/auth'
import { ElMessage } from 'element-plus'
import apiClient from '@/shared/api/client'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

async function handleLogin() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const { data } = await apiClient.post('/auth/login', form)
    authStore.setToken(data.data.access_token)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (err: any) {
    ElMessage.error(err.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #1a1a2e;
}
.login-card {
  width: 400px;
  padding: 20px;
}
.login-title {
  text-align: center;
  font-size: 28px;
  margin-bottom: 4px;
  color: #409eff;
}
.login-subtitle {
  text-align: center;
  color: #999;
  margin-bottom: 24px;
}
</style>
