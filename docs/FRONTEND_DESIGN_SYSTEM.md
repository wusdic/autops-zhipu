# AUTOPS 前端统一设计规范（单一事实源）

> 目的：消除"各页各写"。所有页面遵循同一套结构与令牌，新增页面必须照此写。
> 令牌定义在 `frontend/src/shared/styles/global.css`，复合结构组件化在 `shared/components/`。

## 1. 设计令牌（颜色/字号/间距）

全部用 `global.css` 的 CSS 变量，**禁止**在页面里写死颜色/字号/间距字面量。

| 类别 | 变量 | 说明 |
|---|---|---|
| 主色 | `--autops-primary` `#165dff` | 唯一主色，禁止混用 EP 默认蓝 |
| 文字 | `--autops-text-1..4` | 标题/次要/辅助/禁用 4 级 |
| 字号 | `--autops-font-12..20` | 收敛到 6 级，正文 14，页面标题 20 |
| 间距 | `--autops-space-xs..2xl` | 4/8/12/16/20/24 |
| 圆角 | `--autops-radius-sm/md/lg` | 4/8/12 |

## 2. 页面骨架（强制结构）

```vue
<template>
  <div class="autops-page-container">
    <PageHeader title="页面标题" desc="一句话说明">
      <template #actions>
        <el-button type="primary">主操作</el-button>
      </template>
    </PageHeader>

    <!-- 工具栏（过滤+操作） -->
    <div class="autops-toolbar">
      <div class="autops-toolbar-left"> ...过滤项... </div>
      <div class="autops-toolbar-right"> ...操作按钮... </div>
    </div>

    <!-- 内容卡片 -->
    <div class="autops-card"> ... </div>
  </div>
</template>
```

- **根容器**：一律 `autops-page-container`（内边距唯一来源）。页面专属 scoped 样式钩子可叠加自定义 class，但**不得**用它来设页面内边距。
- **页面头**：一律用 `<PageHeader>`，**禁止**再手写 `autops-page-header` 内部 div 结构。

## 3. PageHeader 组件用法

| 场景 | 写法 | 返回按钮 |
|---|---|---|
| 列表/总览/Tab 宿主页 | `<PageHeader title desc>` | 无 |
| 钻入式详情/编辑/创建页 | `<PageHeader title back desc>` | 有，link 态「返回」 |
| 标题旁徽标 | `#title-extra` 槽 | — |
| 右侧操作按钮 | `#actions` 槽 | — |

**返回按钮规则**（重要）：
- 只有从列表"钻入"的页面（路径带 `:id`，或 create/edit/preview/simulate 动作页）才有返回。
- 菜单可直达的页面、Tab 内嵌子页**一律没有返回**（靠侧边栏 + 面包屑导航）。
- 返回按钮样式固定：`link` 文字态 + `ArrowLeft` 图标 + 文案统一「返回」+ 标题左侧。不允许 plain/default、不允许"返回XX列表"等自定义文案、不允许换图标。
- 默认 `router.back()`；需固定目标时传 `:back-to`。

## 4. 复合组件（统一实现，禁止重复造轮子）

| 用途 | 组件 |
|---|---|
| 页面头 | `PageHeader` |
| 指标卡 | `OverviewCard` / `.autops-metric-card` |
| 状态/严重度徽标 | `StatusBadge` / `SeverityBadge` |
| 表格 | `DataTable` / `el-table`（全局已统一表头行高） |
| 过滤栏 | `FilterBar` / `.autops-toolbar` |
| 详情抽屉 | `DetailDrawer` |

## 5. 其它统一约定

- **对话框宽度**：仅 `480px` / `600px` / `780px` 三级。
- **表格操作列**：`<el-button size="small" plain type="primary|danger">`；查看/编辑用 primary，删除/拒绝用 danger；列宽 1-2 按钮=120，3 个=180，4+=240。
- **分页**：右对齐（全局已统一）。
- **空状态**：`.autops-empty` 或 `el-empty`。

## 6. 迁移进度（已完成）

- [x] PageHeader 组件 + 本规范
- [x] 批1：13 个详情页头迁移（带返回）
- [x] 批2：6 个菜单/内嵌页删除多余返回
- [x] 批3：全部模块（M1~M12）列表/总览/内嵌页头统一迁移 PageHeader
- [x] 批4：根容器统一 autops-page-container（含去掉 padding:0 贴边页）

**例外（保留手写头，原因如下，不纳入 PageHeader）：**
- `knowledge-center/AiDiagnosisPage.vue`：全屏聊天式布局 + 动态描述（按模式切换），非标准页头。
- `response-center/IncidentResponsePage.vue`：卡片式头部内嵌实时告警标签，为专用应急工作台头部。

> 全站约 120 个页面已统一到 PageHeader；新增页面必须遵循第 2/3 节骨架，禁止再手写 `autops-page-header` 内部结构。
