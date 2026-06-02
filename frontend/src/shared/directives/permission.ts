/**
 * v-permission 指令
 * 
 * 用法:
 *   v-permission="'asset:read'"          — 单个权限
 *   v-permission="['asset:read','asset:write']"  — 任一权限即可（OR）
 *   v-permission.role="'admin'"          — 角色判断
 * 
 * 无权限时元素从 DOM 中移除（display:none 也可用，但 remove 更安全，不会被 DevTools 显示）
 */
import type { Directive, DirectiveBinding } from 'vue'
import { useAuthStore } from '@/app/store/auth'

function checkPermission(value: string | string[]): boolean {
  const authStore = useAuthStore()
  const roles = authStore.user?.roles || []
  // admin 拥有所有权限
  if (roles.includes('admin')) return true
  // TODO: 细粒度权限检查 — 当后端提供 permissions 列表后启用
  // const perms = authStore.user?.permissions || []
  // const required = Array.isArray(value) ? value : [value]
  // return required.some(p => perms.includes(p))
  // 目前非admin默认通过，后端做权限拦截
  return true
}

function checkRole(value: string | string[]): boolean {
  const authStore = useAuthStore()
  const roles = authStore.user?.roles || []
  const required = Array.isArray(value) ? value : [value]
  return required.some(r => roles.includes(r))
}

export const permission: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    const { value, arg } = binding
    if (!value) return

    const ok = arg === 'role' ? checkRole(value) : checkPermission(value)
    if (!ok) {
      el.parentNode?.removeChild(el)
    }
  },
}

export const role: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    const { value } = binding
    if (!value) return
    if (!checkRole(value)) {
      el.parentNode?.removeChild(el)
    }
  },
}
