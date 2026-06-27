# 全局状态/标签统一（单一事实源，2026-06-27）

## 问题
此前同一取值在不同地方文案/颜色不一致，存在**三套并行的标签体系**：
1. `src/shared/utils/labels.ts`（此前无人引用）
2. `StatusBadge.vue` / `SeverityBadge.vue`（各自维护一套 map）
3. 每个页面内的局部 `statusLabel/statusType/...` 函数（最分散，且常缺失取值→显示空白）

且 `labels.ts` 本身与后端 canonical 取值漂移（工单缺 assigned/pending_approval/rejected；
执行缺 awaiting_approval/dry_running/verifying/rolling_back/…；告警缺 escalated；
资产用 retired 而非 decommissioned）。

## 处置：labels.ts 作为唯一事实源
- 重写 `labels.ts`，按后端 canonical 值对齐并对历史/同义值容错；为每个实体提供
  `xxxLabel()` / `xxxTag()`：
  - severity / assetStatus / reachability / health / alertStatus /
    ticketStatus / priority / execStatus / policyStatus / risk / knowledge /
    assetType / env / credType
- 共享组件改为消费 labels.ts（影响面最大）：
  - `StatusBadge.vue`：合并各实体 map（单一来源）
  - `SeverityBadge.vue`：直接用 severityLabel/severityTagType
- 关键列表页局部函数改为委托 labels.ts：
  - 资产 `AssetListPage`（type/status/health）
  - 工单 `TicketListPage`（status/priority）
  - 执行 `ExecutionListPage`（risk；status 本就走 StatusBadge）
  - 告警 `AlertListPage` 通过 SeverityBadge/StatusBadge 已统一

## 后端 canonical 取值（前端必须遵循）
- 资产 status：active / inactive / maintenance / decommissioned；reachability：reachable / unreachable / unknown；health：healthy / warning / critical / unknown
- 告警 status：firing / acknowledged / resolved / escalated / suppressed；severity：info / warning / critical
- 工单 status：open / assigned / in_progress / pending_approval / resolved / closed / rejected
- 执行 status：pending / dry_running / dry_run_completed / dry_run_failed / awaiting_approval / approved / running / verifying / completed / failed / cancelled / rolling_back / rolled_back / rollback_failed

## 已逐页收敛（severity/risk/health/status 委托 labels.ts）
- 工单：TicketList/TicketDetail/TicketOverview
- 自动化：ExecutionList/ExecutionDetail/AutomationOverview/PolicyList/PlaybookList/PolicySimulate
- 响应：IncidentResponse/ManualConfirm/AiDiagnosisPanel/ResponseSuggestion/RiskGrading
- 监控：AlertList/AlertDetail/AlertRule/StateSnapshot
- 资源：AssetList/AssetDetail/AssetGroup/BusinessSystem/AssetTopology
- 巡检/配置/知识：InspectionReport(×2)/InspectionRules/ConfigOverview/AiDiagnosis/AIToolPolicy
- 共享组件：StatusBadge / SeverityBadge

## 刻意保留（领域特有子状态，非四大实体 canonical，强行套用会误标）
- 工单子工作流：ManualHandling/Postmortem 的处置/复盘状态
- 审批工作流：ApprovalCenter 的 pending/approved/rejected
- 巡检结果 pass/fail、报表任务状态、模型服务/自检/采集器状态、
  事件/异常(anomaly) 状态、Incident 的 major/minor 严重度
> 这些属于各自领域的独立词表，应在 labels.ts 中**另设**对应映射后再收敛，
> 不并入四大实体的 canonical 维度。

## 原则
**新增/修改页面一律用 labels.ts，不再写局部 map。**

## 验证
前端本环境无 node_modules，未跑 vue-tsc/build；改动均为"局部 map→引用共享函数"的等价替换，
须 CI 复核类型检查与构建。
