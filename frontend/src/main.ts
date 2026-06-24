import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import './shared/styles/global.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import router from './app/router'
import App from './App.vue'
import { permission, role } from './shared/directives'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })

// Register directives
app.directive('permission', permission)
app.directive('role', role)

// Register all icons globally
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 全局错误处理 — 捕获未处理的组件异常，避免静默丢失
app.config.errorHandler = (err, _instance, info) => {
  // 生产环境不上报到 console，开发环境输出便于调试
  if (import.meta.env.DEV) {
    console.error('[Vue Error]', info, err)
  }
}

// 捕获未处理的 Promise rejection
window.addEventListener('unhandledrejection', (event) => {
  if (import.meta.env.DEV) {
    console.error('[Unhandled Promise]', event.reason)
  }
})

app.mount('#app')
