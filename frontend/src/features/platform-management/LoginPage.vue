<template>
  <div class="login-page">
    <el-card class="login-card">
      <template #header>
        <div class="login-header">
          <h1>AUTOPS</h1>
          <p>自治运维操作系统</p>
        </div>
      </template>
      <el-form :model="form" @submit.prevent="handleLogin" label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-button type="primary" :loading="loading" native-type="submit" style="width: 100%">登 录</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { API as APIRoutes } from '@/shared/api/routes'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { setToken } from '@/app/router/guards'
import { useAuthStore } from '@/app/store/auth'
import apiClient from '@/shared/api/client'

const router = useRouter()
const loading = ref(false)
const form = reactive({ username: 'admin', password: 'admin123' })
const authStore = useAuthStore()

async function handleLogin() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const { data } = await apiClient.post(APIRoutes.AUTH.LOGIN, {
      username: form.username,
      password: form.password,
    })
    if (data.data?.access_token) {
      setToken(data.data.access_token)
      authStore.setToken(data.data.access_token)
      if (data.data.user) {
        authStore.user = data.data.user
      }
      localStorage.setItem('username', form.username)
      ElMessage.success('登录成功')
      const redirect = (router.currentRoute.value.query.redirect as string) || '/'
      router.push(redirect)
    } else {
      ElMessage.error(data.message || '登录失败')
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--autops-terminal-bg) 0%, var(--autops-terminal-bg) 50%, var(--autops-terminal-bg) 100%);
}
.login-card {
  width: 400px;
  border-radius: var(--autops-radius-lg);
}
.login-header {
  text-align: center;
}
.login-header h1 {
  margin: 0;
  font-size: 28px;
  color: var(--autops-text-1);
}
.login-header p {
  margin: 4px 0 0;
  color: var(--autops-info);
  font-size: var(--autops-font-14);
}
</style>
