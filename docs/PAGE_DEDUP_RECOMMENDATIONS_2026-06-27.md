# 页面重复 / 功能相近 排查与取舍建议（2026-06-27）

对照 `router/index.ts`（111 条路由）与 `MainLayout.vue`（108 项左侧菜单）+ 各页 `el-tab-pane`，
系统排查重复与功能相近页面。分三级：**A 确定重复**（同一数据源/功能，应合并删一）、
**B 高度相近**（建议合并为 tab 或重定向）、**C 模式性冗余**（总览+列表，可选精简）。

---

## A. 确定重复（强烈建议处理）

### A1. 发现结果：独立页 vs 资源发现页内 tab —— ✅ 用户已指出
- 重复点：菜单 `/resources/discovery-results`（`DiscoveryResultPage.vue`）与
  `/resources/discovery`（`AssetDiscoveryPage.vue`）内 **"发现结果" tab**，二者都读 `API.DISCOVERY_RESULTS`，
  连"纳管/导入"操作都重叠（两边都调 `API.ASSET_IMPORT`）。
- **取舍**：以 `AssetDiscoveryPage`（任务/结果/纳管向导 三 tab 一体）为准。
  - 删除菜单项 `/resources/discovery-results`；
  - 路由 `/resources/discovery-results` 改 `redirect` 到 `/resources/discovery`（带 `?tab=results`，保留外链/书签）；
  - `DiscoveryResultPage.vue` 退役（或保留供 redirect 落地，二选一）。

### A2. 配置总览页 tab vs 配置中心各独立页
- 重复点：`ConfigOverviewPage.vue` 的 5 个 tab（发现模板 / 巡检规则 / 阈值规则 / 通知规则 / 配置版本）
  与菜单 `/config/discovery-templates`、`/config/inspection-rules`、`/config/threshold-rules`、
  `/config/notification-rules`、`/config/versions` 一一对应（同名同功能）。
- **取舍**：二选一，不要并存——
  - **方案①（推荐）**：保留 5 个独立页做菜单；把"配置总览"瘦身为**纯统计/入口卡片**（不再内嵌完整表格），点击卡片跳对应独立页。
  - 方案②：保留总览页 tab 容器，删除 5 个独立菜单项（仅在总览内切换）。
  - 当前是"两份完整实现"，维护成本翻倍，必须收敛其一。

### A3. 巡检报告路由已有重复（历史遗留，已部分处理）
- `/inspection-report` 已 `redirect → /inspection/reports`（✅ 已去重，无需再动，仅记录）。

---

## B. 功能高度相近（建议合并）

### B1. M5 分析中心：故障工作台 vs 5 个单步页
- `/incident` 故障工作台（`IncidentResponsePage`）已内嵌 AI 分析（证据链 steps）、关联告警等；
  而菜单另列 `/ai-diagnosis` AI诊断、`/impact-analysis` 影响分析、`/risk-grading` 风险分级、
  `/response-suggestion` 处置建议、`/closure-verification` 关闭验证——它们本质是**同一处置流程的各阶段**。
- **建议**：把这 5 个收敛为故障工作台内的 **tab / 步骤**（处置闭环：诊断→影响→分级→建议→验证），
  菜单只留"故障工作台"一个入口。单页可保留路由供深链，但不进主菜单。

### B2. AI 诊断三处入口
- `/ai-diagnosis`（M5 AI诊断面板）、`/aiops`（M8 "AI 诊断记录"）、`/ai-assistant`（M10 AI 助手）。
- **建议**：`/ai-diagnosis` 并入 B1 工作台；`/aiops`（历史记录）作为 AI 助手或工作台的"历史"tab；
  对外仅保留 `/ai-assistant` 一个常驻入口。

### B3. 人工确认台 vs 人工处置台
- `/manual-confirm`（response-center `ManualConfirmPage`）与 `/manual-handling`（ticket-center `ManualHandlingPage`），
  都是"人工介入待办"工作台，受众/动作高度重叠。
- **建议**：合并为单一"人工处置台"，用 tab 区分"待确认 / 待处置"；删冗余入口。

### B4. 状态快照 vs 状态变化
- `/monitoring/states` 状态快照 与 `/monitoring/state-changes` 状态变化，同一 state 数据的两个视图。
- **建议**：合并为一页（"当前快照 / 变更历史"两 tab）。

### B5. 日志三页定位需澄清
- `/inspection/log-check` 日志巡检、`/monitoring/log-sources` 日志接入、`/logs/search` 日志检索。
- 三者**职责不同**（巡检规则 / 数据源接入 / 全文检索），**不建议合并**，但建议在命名/分组上明确区分，避免用户混淆。

### B6. 报告生成 vs 导出中心
- `/report/generate` 报告生成 与 `/export-center` 导出中心 产出物有重叠（都生成可下载文件）。
- **建议**：核对二者边界；若"导出中心"只是报告任务的下载列表，并入 `/report/tasks` 或报表总览的"导出"tab。

---

## C. 模式性冗余（总览 + 列表，按需精简）

多个模块同时存在"总览页"和"列表页"，总览常较薄：
- 巡检：`/inspections` 巡检总览 + `/inspection/results` 等；
- 监控：`/monitoring` 总览 + 各采集/告警列表；
- 异常：`/anomalies` 异常总览 + `/anomaly/list` 异常列表；
- 工单：`/ticket-overview` + `/tickets`；
- 知识：`/knowledge-overview` + `/knowledge`；
- 报表：`/reports` + 各报告页；
- 自动化：`/automation` + 各列表；
- 资源：`/resources` 资源总览 + `/assets` 资源列表。

**建议（统一原则）**：总览页只做"统计卡片 + 快捷入口 + 近期动态"，**不重复整张列表**；
若某总览页已退化为"列表的子集"，则降级为列表页顶部的统计条，删除独立菜单项。
异常总览/列表（`/anomalies` vs `/anomaly/list`）重叠最明显，可优先合并为一页两 tab。

---

## 处理优先级建议
1. **A1**（发现结果）—— 用户已指出，改动小、收益直接：删菜单项 + 路由 redirect。
2. **A2**（配置总览 vs 配置中心）—— 维护成本最高的"双份实现"，应尽快定方案收敛。
3. **B1/B2**（M5 分析中心 + AI 诊断）—— 入口最杂乱，收敛后主菜单显著变清爽。
4. B3/B4 → C 异常总览/列表 → 其余总览精简。

---

## 实施进度（2026-06-27 更新）

| 项 | 状态 | 实现 |
|---|---|---|
| A1 发现结果 | ✅ 已完成 | 删菜单项；`/resources/discovery-results` → redirect `?tab=results`；退役 DiscoveryResultPage |
| A2 配置总览 | ✅ 已完成（方案①） | 总览瘦身为统计+入口卡片，5 个独立配置页为唯一实现 |
| A3 巡检报告 | ✅ 历史已去重 | `/inspection-report` redirect |
| B1 M5 分析中心 | ✅ 已完成 | 新增 IncidentWorkbenchPage，5 单步页收敛为 6 tab；菜单只留"故障工作台"；5 旧路径 redirect |
| B2 AI 诊断入口 | ✅ 部分完成 | `/ai-diagnosis` 并入工作台（B1）；`/ai-assistant` 保留；`/aiops`（AI诊断记录）保留为知识库历史，未跨模块强并 |
| B3 人工确认/处置台 | ✅ 已完成 | 新增 ManualWorkbenchPage（待确认/待处置 两 tab）；`/manual-confirm` redirect |
| B4 状态快照/变化 | ✅ 已完成 | 新增 StateMonitorPage（当前快照/变更历史 两 tab）；`/monitoring/state-changes` redirect |
| C 异常总览/列表 | ✅ 已完成 | 新增 AnomalyCenterPage（总览/列表 两 tab）；`/anomaly/list` redirect |
| B5 日志三页 | — 不合并 | 职责不同，保留 |
| B6 报告生成/导出中心 | ⏳ 待核对边界 | 未动 |
| C 其余总览+列表 | ⏳ 可选 | 巡检/监控/工单/知识/报表/自动化/资源总览未动 |

**统一实现模式**：被合并页加 `embedded` prop（嵌入时隐藏自身页头），宿主页用 `el-tabs`（`lazy`）承载；
旧路径一律 `redirect` 到宿主 `?tab=xxx` 保留外链/书签。

> 验证：本环境无 node_modules，未跑 vue-tsc/vite build，须 CI 复核。
