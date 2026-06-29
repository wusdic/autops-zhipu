<script setup lang="ts">
/**
 * PageHeader —— 全站统一页面头组件（唯一事实源）
 * ───────────────────────────────────────────────────────────────
 * 设计规范（禁止页面再手写 autops-page-header 内部结构）：
 *  - 列表/总览/宿主页：<PageHeader title desc>，无返回按钮
 *  - 钻入式详情/编辑/创建页：<PageHeader title back desc>，返回按钮统一为
 *    link 文字态 + ArrowLeft 图标 + 文案「返回」，置于标题左侧
 *  - 标题旁徽标用 #title-extra 槽；右侧操作按钮用 #actions 槽
 *  - 字号/间距/颜色全部由本组件依 global.css 令牌定义，页面不得覆盖
 *
 * 用法：
 *   <PageHeader title="资产列表" desc="管理所有纳管资源">
 *     <template #actions><el-button type="primary">新建</el-button></template>
 *   </PageHeader>
 *
 *   <PageHeader title="资产详情" back :back-to="'/resources/assets'">
 *     <template #title-extra><el-tag>在线</el-tag></template>
 *     <template #actions><el-button>编辑</el-button></template>
 *   </PageHeader>
 */
import { ArrowLeft } from '@element-plus/icons-vue'
import { useRouter, type RouteLocationRaw } from 'vue-router'

const props = withDefaults(
  defineProps<{
    /** 主标题 */
    title?: string
    /** 描述文字（标题下方一行小字） */
    desc?: string
    /** 是否显示返回按钮（仅钻入式详情/编辑/创建页使用） */
    back?: boolean
    /** 返回按钮文案，默认「返回」 */
    backText?: string
    /** 返回目标路由；不传则 router.back() 回上一页 */
    backTo?: RouteLocationRaw
  }>(),
  { title: '', desc: '', back: false, backText: '返回', backTo: undefined },
)

const router = useRouter()

function onBack() {
  if (props.backTo) router.push(props.backTo)
  else router.back()
}
</script>

<template>
  <div class="autops-page-header autops-page-header--between">
    <div class="page-header__left">
      <el-button v-if="back" link class="page-header__back" @click="onBack">
        <el-icon><ArrowLeft /></el-icon>
        <span>{{ backText }}</span>
      </el-button>
      <div class="page-header__titles">
        <div class="autops-page-title-row">
          <span class="autops-page-title">{{ title }}</span>
          <slot name="title-extra" />
        </div>
        <div v-if="desc" class="autops-page-desc">{{ desc }}</div>
      </div>
    </div>
    <div v-if="$slots.actions" class="autops-header-actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<style scoped>
.page-header__left {
  display: flex;
  align-items: center;
  gap: var(--autops-space-md);
  min-width: 0;
}

.page-header__back {
  font-size: var(--autops-font-14);
  color: var(--autops-text-2);
  padding: 0;
  height: auto;
}

.page-header__back:hover {
  color: var(--autops-primary);
}

.page-header__back .el-icon {
  margin-right: 2px;
}

.page-header__titles {
  min-width: 0;
}
</style>
