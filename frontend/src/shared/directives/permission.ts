/**
 * v-permission 指令
 *
 * 用法:
 *   v-permission="'asset:read'"                    — 单个权限
 *   v-permission="['asset:read','asset:write']"     — 任一权限即可（OR）
 *   v-permission.role="'admin'"                     — 角色判断
 *
 * 无权限时元素从 DOM 中移除
 */
import type { Directive, DirectiveBinding } from 'vue'
import { useAuthStore } from '@/app/store/auth'

function checkPermission(value: string | string[]): boolean {
  const authStore = useAuthStore()
  const roles = authStore.user?.roles || []

  // super_admin 或 admin 拥有所有权限
  if (roles.includes('super_admin') || roles.includes('admin')) return true

  // 细粒度权限检查
  // 当后端在 user 对象中提供 permissions 列表时启用
  // 目前基于角色做基础判断：operator 有读+执行权限，viewer 只有读权限
  const required = Array.isArray(value) ? value : [value]

  // 获取角色对应的权限映射
  const rolePerms: Record<string, string[]> = {
    super_admin: ['*:*'],
    admin: ['*:*'],
    operator: [
      'asset:read', 'asset:write', 'config:read', 'collector:read',
      'event:read', 'alert:*', 'policy:read', 'automation:execute',
      'log:read', 'ticket:*', 'knowledge:read', 'inspection:*',
    ],
    viewer: [
      'asset:read', 'config:read', 'collector:read', 'event:read',
      'alert:read', 'policy:read', 'log:read', 'ticket:read',
      'knowledge:read',
    ],
    ai_operator: [
      'asset:read', 'alert:read', 'alert:*', 'knowledge:read',
      'aiops:*', 'automation:execute',
    ],
  }

  // 收集当前用户所有角色的权限
  const userPerms = new Set<string>()
  for (const role of roles) {
    const perms = rolePerms[role]
    if (perms) perms.forEach(p => userPerms.add(p))
  }
  if (userPerms.has('*:*')) return true

  // 检查所需权限是否满足
  // 支持 wildcard: "alert:*" 匹配 "alert:read"、"alert:write" 等
  return required.some(req => {
    if (userPerms.has(req)) return true
    // 通配符匹配: req="alert:read"，userPerms 有 "alert:*"
    const [domain] = req.split(':')
    if (domain && userPerms.has(`${domain}:*`)) return true
    return false
  })
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
