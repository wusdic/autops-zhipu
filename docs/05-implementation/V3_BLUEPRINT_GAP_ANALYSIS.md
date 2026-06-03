# V3 蓝图 vs 当前实现 — 全面差距分析报告

> 生成时间：2026-06-03
> 基准文档：AUTOPS 前端目标模块与子模块规划清单 V3
> 当前统计：136页面前端、252端点后端、51张表、TS零错误

---

## 一、模块级覆盖率

| 模块 | 蓝图要求页面数 | 当前页面数 | 覆盖率 | 状态 |
|---|---|---|---|---|
| G0 全局基础 | 6 页面 + 9 能力 | 4 页面 (Login/404/SessionExpired/Forbidden) | 40% | ⚠️ 缺通知中心、全局搜索、任务进度浮层 |
| M1 首页指挥台 | 8 子模块 | 3 页面 | 38% | ⚠️ 缺自动发现状态/巡检状态/异常处置看板/报告生成状态/平台健康卡片/今日摘要 |
| M2 资源中心 | 10 子模块 | 12 页面 | 120% | ✅ 超覆盖（含详情/拓扑等子页） |
| M3 配置中心 | 12 子模块 | 6 页面 | 50% | ⚠️ 缺巡检模板独立页/日志巡检规则/配置巡检规则/页面巡检规则/API巡检规则/报告模板 |
| M4 巡检中心 | 12 子模块 | 11 页面 | 92% | ✅ 基本覆盖 |
| M5 处置中心 | 10 子模块 | 13 页面 | 130% | ✅ 超覆盖 |
| M6 自动化中心 | 11 子模块 | 13 页面 | 118% | ✅ 超覆盖 |
| M7 智能知识库 | 9 子模块 | 13 页面 | 144% | ✅ 超覆盖 |
| M8 工单中心 | 8 子模块 | 10 页面 | 125% | ✅ 超覆盖 |
| M9 报表中心 | 13 子模块 | 15 页面 | 115% | ✅ 超覆盖 |
| M10 平台管理 | 14 子模块 | 18 页面 | 129% | ✅ 超覆盖 |

**结论**：M2/M4-M10 页面数量已基本达标甚至超覆盖，主要差距在 **G0全局基础能力(40%)**、**M1首页指挥台(38%)** 和 **M3配置中心(50%)**。

---

## 二、逐模块详细差距

### 2.1 G0 全局基础能力

| 蓝图要求 | 当前实现 | 差距 |
|---|---|---|
| 登录页 | ✅ LoginPage.vue (94行) | 功能完整，缺MFA预留 |
| 会话失效页 | ✅ SessionExpiredPage.vue | 功能完整 |
| 无权限页 | ✅ ForbiddenPage.vue | 功能完整 |
| 通知中心 | ❌ 未实现 | 缺全局通知浮层/通知中心页 |
| 全局搜索 | ⚠️ 有SearchPage.vue但MainLayout无搜索入口 | 需在Header加全局搜索触发器 |
| 任务进度浮层 | ❌ 未实现 | 缺统一后台任务进度浮层 |
| 范围选择器 | ❌ 未实现通用组件 | 各页面散落筛选逻辑 |
| 模板选择器 | ❌ 未实现通用组件 | 各页面独立实现 |
| 实时通道(WebSocket) | ✅ ws.ts已存在 | 未在所有需要的地方使用 |
| 统一API Client | ✅ client.ts + routes.ts | 已达标 |
| 权限控制 | ✅ v-permission指令 | 已达标 |
| 证据面板 | ❌ 未实现通用组件 | 缺统一证据展示组件 |
| 时间线组件 | ⚠️ 部分页面有el-timeline | 未抽为通用组件 |
| 任务向导 | ❌ 未实现 | 缺步骤式任务创建向导 |
| 导出中心 | ❌ 未实现 | 缺异步导出+通知 |

### 2.2 M1 首页指挥台

| 蓝图要求 | 当前实现 | 差距 |
|---|---|---|
| 态势总览 | ✅ CommandDashboardPage | 有stats卡片区 |
| 自动发现状态 | ⚠️ dashboard API有asset-discovery端点 | DashboardPage未展示发现任务卡片 |
| 自动巡检状态 | ⚠️ dashboard API有inspection端点 | DashboardPage未展示巡检状态卡片 |
| 异常处置看板 | ⚠️ dashboard API有anomaly/automation端点 | DashboardPage缺异常处置分流卡片 |
| 待我处理 | ⚠️ dashboard API有my-pending端点 | DashboardPage未使用 |
| 报告生成状态 | ⚠️ dashboard API有report端点 | DashboardPage未展示 |
| 平台健康卡片 | ⚠️ dashboard API有platform-health端点 | DashboardPage未展示 |
| 今日摘要 | ❌ 未实现 | 缺值班交接摘要视图 |
| 实时刷新 | ❌ 未实现 | 缺首页自动刷新 |
| 下钻能力 | ⚠️ useWorkflowNav有部分 | 卡片点击无跳转 |

**差距总结**：DashboardPage有API支撑但前端展示严重不足，需大幅增强为8+卡片的综合指挥台。

### 2.3 M3 配置中心

| 蓝图要求 | 当前实现 | 差距 |
|---|---|---|
| 配置总览 | ✅ ConfigOverviewPage (新建) | 刚创建，功能完整 |
| 凭证库 | ✅ CredentialsPage.vue | 已有页面 |
| 发现模板 | ✅ DiscoveryTemplatePage (新建) | 刚创建 |
| 巡检模板 | ⚠️ InspectionTemplatePage在inspection-center | 路由在巡检中心不在配置中心 |
| 日志巡检规则 | ✅ InspectionRulesPage (新建,有log_check tab) | 合并在规则页中 |
| 配置巡检规则 | ✅ InspectionRulesPage (新建,有config_check tab) | 合并在规则页中 |
| 页面巡检规则 | ✅ InspectionRulesPage (新建,有page_check tab) | 合并在规则页中 |
| API巡检规则 | ❌ 未在InspectionRulesPage中 | 缺API巡检规则tab |
| 阈值规则 | ✅ ThresholdRulePage (新建) | 刚创建 |
| 通知规则 | ✅ NotificationRulePage (新建) | 刚创建 |
| 报告模板 | ⚠️ ReportTemplatePage在report-audit-center | 配置中心缺报告模板入口 |
| 配置版本 | ✅ ConfigVersionPage (新建) | 刚创建 |

**差距总结**：配置中心页面数达标，但缺API巡检规则tab，报告模板入口需从报表中心链接过来。

### 2.4 M4-M10 其他模块

这些模块页面数量已超覆盖，主要差距在**功能深度**而非页面缺失：

| 功能深度差距 | 影响模块 | 严重度 |
|---|---|---|
| 后端缺少阈值规则/notification/discovery-template的专属API | M3 配置中心 | P0 - 页面调用API会返回空 |
| notification service.py 和 log service.py 未实现 | M4 巡检中心/M9 报表 | P0 - 核心域逻辑缺失 |
| anomaly/inspection/report 三个域缺少 handlers.py | 五条主线事件驱动 | P1 - 事件处理缺失 |
| 范围选择器/模板选择器通用组件未抽离 | G0 全局 | P1 - 代码重复 |
| 首页DashboardPage严重不足(需8+卡片) | M1 指挥台 | P0 - 用户第一印象 |

---

## 三、后端API差距

### 3.1 完全缺失的API类别（0个端点）

| API类别 | 影响前端页面 | 优先级 |
|---|---|---|
| 阈值规则 CRUD (threshold-rules) | ThresholdRulePage | P0 |
| 通知规则 CRUD (notification-rules) | NotificationRulePage | P0 |
| 发现模板 CRUD (discovery-templates) | DiscoveryTemplatePage | P0 |
| 配置版本管理 (config-versions) | ConfigVersionPage | P0 |
| API巡检规则 (api-checks) | InspectionRulesPage API tab | P1 |

### 3.2 后端域服务缺失

| 域 | service.py | handlers.py | 影响 |
|---|---|---|---|
| log | ❌ 缺失 | ✅ 116行 | 日志检索/巡检无法工作 |
| notification | ❌ 缺失 | ✅ 166行 | 通知规则无法执行 |
| anomaly | ✅ 345行 | ❌ 缺失 | 异常事件处理缺失 |
| inspection | ✅ 224行 | ❌ 缺失 | 巡检事件处理缺失 |
| report | ✅ 213行 | ❌ 缺失 | 报告事件处理缺失 |

### 3.3 Dashboard API 已有但前端未用

后端已有以下dashboard端点，但前端DashboardPage未充分调用：
- `/api/v1/dashboard/stats` ✅ 已用
- `/api/v1/dashboard/asset-discovery` ❌ 未用
- `/api/v1/dashboard/inspection` ❌ 未用
- `/api/v1/dashboard/anomaly` ❌ 未用
- `/api/v1/dashboard/automation` ❌ 未用
- `/api/v1/dashboard/report` ❌ 未用
- `/api/v1/dashboard/platform-health` ❌ 未用
- `/api/v1/dashboard/my-pending` ❌ 未用

---

## 四、五条自动化主线端到端差距

### 主线1：自动发现资产

```text
配置发现模板 → 创建发现任务 → 运行发现 → 查看结果 → 去重 → 纳管 → 绑定巡检
```

| 步骤 | 前端 | 后端 | 状态 |
|---|---|---|---|
| 配置发现模板 | ✅ DiscoveryTemplatePage | ❌ 缺API | ⚠️ |
| 创建发现任务 | ✅ DiscoveryTaskPage | ✅ discovery API | ✅ |
| 运行发现 | ✅ 进度展示 | ✅ | ✅ |
| 查看结果 | ✅ DiscoveryResultPage | ✅ | ✅ |
| 去重合并 | ⚠️ 基础UI | ⚠️ | ⚠️ |
| 确认纳管 | ✅ 纳管按钮 | ✅ asset API | ✅ |
| 绑定巡检模板 | ✅ AssetDetailPage | ✅ | ✅ |

**差距**：发现模板后端API缺失，纳管向导不够完善。

### 主线2：自动按要求巡检

```text
配置巡检模板 → 绑定资产范围 → 创建巡检计划 → 执行 → 结果 → 异常
```

| 步骤 | 前端 | 后端 | 状态 |
|---|---|---|---|
| 配置巡检模板 | ✅ InspectionTemplatePage | ✅ inspection API | ✅ |
| 绑定资产范围 | ✅ | ✅ | ✅ |
| 创建巡检计划 | ✅ InspectionPlanPage | ✅ | ✅ |
| 执行巡检 | ✅ InspectionTaskPage | ✅ | ✅ |
| 巡检结果 | ✅ InspectionResultPage | ✅ | ✅ |
| 异常发现 | ✅ AnomalyListPage | ✅ anomaly API | ✅ |

**状态**：✅ 基本闭环完整。

### 主线3：自动发现异常

**状态**：✅ 闭环完整（巡检→异常→处置→工单→报告）

### 主线4：自动处置

**状态**：✅ 闭环完整（策略→dry-run→审批→执行→验证→回滚）

### 主线5：自动出具报告

**状态**：✅ 闭环基本完整（模板→生成→预览→下载→审计）

---

## 五、优先级排序

### P0 — 必须立即修复（阻塞核心功能）

1. **DashboardPage大幅增强** — 当前仅stats卡片，需增加7+卡片(发现状态/巡检状态/异常处置/待我处理/报告状态/平台健康/今日摘要)
2. **后端缺失API** — 阈值规则/通知规则/发现模板/配置版本 CRUD端点
3. **后端缺失服务** — log service + notification service 实现
4. **全局搜索入口** — MainLayout Header加搜索图标+快捷键

### P1 — 应尽快修复 ✅ 已完成 (commit a061788)

5. **InspectionRulesPage增加API巡检规则tab** ✅
6. **通用范围选择器组件** — AssetRangeSelector.vue ✅
7. **通用模板选择器组件** — TemplateSelector.vue ✅
8. **通知中心浮层** — NotificationBell集成到Header ✅
9. **任务进度浮层** — TaskProgressIndicator集成到Header ✅
10. **anomaly/inspection/report handlers.py实现** ✅ (18域handlers全部就位)

### P2 — 可延后

11. 报告模板入口从配置中心链接
12. 证据面板通用组件
13. 时间线通用组件
14. 任务向导步骤组件
15. 导出中心（异步导出+通知）
16. 模型服务详细指标图表
17. 许可证管理页面
