# 前端页面功能与业务流有效性审计（逐页）

> 日期：2026-06-26 · 范围：`frontend/src/features/**` 全部 **124** 个页面
> 方法：数据驱动提取每页调用的 API/服务 → 对照后端真实路由 → 按业务闭环判断上下游有效性；对无网络层的页面做静态核查。
> 说明：本环境无法跑前端，结论基于「接口接线 + 闭环推理 + 抽样」，UI 细节未逐一目检。

## 0. 总体结论

- **接线层面**：124 页中 **122 页已接真实后端**（直接用 `API.*` 常量或 `shared/api/*` 服务封装），仅 **2 页为纯静态占位**（无任何后端交互）。
- **闭环层面**：经前几轮修复（事件链路、鉴权、缺失端点、模型/备份/字典/许可证/巡检规则等），**资源发现→采集→事件→告警→策略→自动化→工单→知识→报表→平台治理** 各段在「开发态」均可端到端走通。
- **主要遗留**：①生产执行器缺失，自动化执行段仅 dev 可用；②2 个静态占位页；③页面存在明显重复/重叠（124 页偏多，部分同数据多页）；④工单附件、合规/风险分级等少数页功能偏薄；⑤多租户页无数据隔离。

---

## 1. 指挥中心 command-dashboard（3）
| 页面 | 功能设计 | 接线 | 上下游有效性 | 评价 |
|---|---|---|---|---|
| CommandDashboardPage | 运维总览：告警/资产/事件/执行/平台健康聚合 | `ALERTS/ASSETS/COLLECTION_JOBS/EVENTS/EXECUTIONS/DASHBOARD.PLATFORM_HEALTH` | 入口聚合多域，下游跳各详情 | 合理 ✅ |
| BusinessHealthMapPage | 业务系统健康地图 | `BUSINESS_SYSTEMS` | 依赖业务系统建模 | 合理 ✅ |
| DailySummaryPage | 今日摘要 | `EXECUTIONS` | 数据面偏窄（仅执行） | 可增强（应聚合告警/巡检）🟡 |

## 2. 资源中心 resource-center（12）
| 页面 | 接线 | 上下游 | 评价 |
|---|---|---|---|
| AssetListPage | `ASSETS/ASSET_IMPORT/ASSET_GROUP*/CREDENTIAL_BIND/STATES.LATEST` | 纳管→分组→绑凭证→看最新状态，闭环入口 | 合理 ✅ |
| AssetDetailPage | 资产详情：关系/时间线/凭证/采集配置/策略/采集触发 | 上接发现/列表，下接采集与策略 | 合理 ✅ |
| AssetDiscoveryPage | 发现任务+结果+纳管 | `DISCOVERY_TASKS/RESULTS` → 纳管发资产创建事件→采集 | 合理（发现段核心）✅ |
| DiscoveryResultPage | 发现结果纳管 | 下游 `ASSET_IMPORT` | 与 AssetDiscovery 部分重叠 🟡 |
| AssetGroupPage / BusinessSystemPage / AssetTopologyPage | 分组/业务系统/拓扑 | 资产维度组织 | 合理 ✅ |
| CredentialPage | 凭证 CRUD+绑定（PUT/DELETE 本轮已补） | 下游被采集/巡检/执行使用 | 合理 ✅ |
| ResourceImportPage | 批量导入 `ASSET_IMPORT` | 与发现纳管并行入口 | 合理 ✅ |
| ResourceOverviewPage | 资源总览（服务封装） | 聚合入口 | 合理 ✅ |
| AgentManagementPage | 边缘采集器（Agent）管理（服务封装，`/agents`） | 采集执行单元 | 合理 ✅ |
| **LifecyclePage** | 资产生命周期 | **无任何后端交互（纯静态）** | 🔴 样子货 |

## 3. 配置中心 config-center（6）
| 页面 | 接线 | 评价 |
|---|---|---|
| ConfigOverviewPage | `CONFIGS/DISCOVERY_TEMPLATES/NOTIFICATION_RULES` | 合理 ✅ |
| ConfigVersionPage | 版本/发布/回滚/diff | 合理 ✅（注：后端漂移检测 detect_drift 逻辑有缺陷，见后端审计） |
| ThresholdRulePage / NotificationRulePage / DiscoveryTemplatePage | 服务封装 CRUD+toggle | 合理 ✅ |
| InspectionRulesPage | `/inspection/rules`（本轮新接） | 上游配置→下游巡检执行采用 | 合理 ✅ |

## 4. 监控中心 monitoring-center（13）
| 页面 | 接线 | 上下游 | 评价 |
|---|---|---|---|
| MonitoringOverviewPage | 告警/资产/采集/事件/状态变化聚合 | 监控总览入口 | 合理 ✅ |
| CollectorPage | 采集任务/结果/边缘采集器（GET/DELETE 本轮补全） | 采集段核心 | 合理 ✅ |
| CollectionResultPage / CollectorHealthPage | 服务封装 | 与 CollectorPage 数据重叠 | 偏重叠 🟡 |
| MetricsTrendPage / StateSnapshotPage / StateChangePage | 指标/状态快照/变化 | 采集→状态段 | 合理 ✅ |
| EventListPage | 事件流+关联告警 | 状态→事件→告警 中枢 | 合理 ✅ |
| AlertListPage / AlertDetailPage | 告警生命周期+证据链+转工单 | 事件→告警→工单/诊断 | 合理 ✅ |
| AlertRulePage | 告警规则 CRUD（DELETE 本轮补） | 上游配置告警匹配 | 合理 ✅ |
| LogSourcePage / ConfigPage | 日志源/配置事实（服务封装） | 辅助 | 合理 ✅ |

## 5. 处置中心 response-center（12）
| 页面 | 接线 | 评价 |
|---|---|---|
| IncidentResponsePage | 告警/事件/执行/策略/通知渠道/诊断 一体处置台 | 功能最重，闭环处置核心 ✅ |
| AnomalyListPage / AnomalyDetailPage / AnomalyOverviewPage | `/anomalies*`（服务封装） | 异常域处置 ✅ |
| ImpactAnalysisPage | `ANOMALY.IMPACT_ANALYSIS` | 影响分析 ✅ |
| AiDiagnosisPanelPage / IncidentWorkspacePage | 告警+事件 | 与 IncidentResponse/AiDiagnosis **功能重叠明显** 🟡 |
| ManualConfirmPage | `/approvals*`（本轮修正路径） | 审批处置 ✅ |
| ClosureVerificationPage | `TICKETS` | 关闭验证，功能偏薄 🟡 |
| RiskGradingPage | `ASSETS` | 风险分级，单数据源、设计偏薄 🟡 |
| ResponseSuggestionPage / AlertCorrelationPage | 服务封装/聚合 | 设计偏薄，价值待验证 🟡 |

## 6. 自动化中心 automation-center（13）
| 页面 | 接线 | 上下游 | 评价 |
|---|---|---|---|
| ScriptListPage / PlaybookListPage | 脚本/剧本 CRUD | 策略动作来源 | 合理 ✅ |
| PolicyListPage / PolicyEditPage / PolicySimulatePage | 策略 CRUD+模拟 | 告警→策略→执行 | 合理 ✅ |
| ExecutionListPage / ExecutionDetailPage | 执行+日志+验证+审批/取消/回滚 | 自动化执行段核心 | 合理 ✅ |
| ApprovalCenterPage / DryRunDetailPage / RollbackCenterPage / ExecutionLockPage | 审批/试运行/回滚/并发锁 | 执行治理 | 合理 ✅ |
| AutomationOverviewPage | `/automation/stats` | 总览 | 合理 ✅ |
| **RemediationTemplatePage** | 修复模板 | **无后端交互（纯静态 mock）** | 🔴 样子货 |
| ⚠️ 全段共性 | — | **生产无可用执行器（仅 LocalDevExecutor，prod 抛错）** | 🔴 执行段生产不可用 |

## 7. 巡检中心 inspection-center（11）
| 页面 | 接线 | 评价 |
|---|---|---|
| InspectionOverviewPage | `/inspection/stats` | 合理 ✅ |
| InspectionPlanPage / InspectionTaskPage / InspectionTemplatePage | 服务封装 CRUD/触发 | 计划→任务（本轮已真正执行） ✅ |
| InspectionResultPage / InspectionDetailPage / InspectionReportPage | 结果/详情/报告 | 任务→结果→报告 ✅ |
| Page/Config/Log/BaselineInspectionPage | `/inspection/{page,config,log,baseline}-checks`（本轮 check_type 落地后生效） | 分类巡检结果 ✅ |

## 8. 知识中心 knowledge-center（11）
| 页面 | 接线 | 评价 |
|---|---|---|
| KnowledgeListPage/DetailPage/EditPage | CRUD+发布+版本+反馈+转 runbook（DELETE 本轮补） | 知识沉淀闭环 ✅ |
| KnowledgeImportPage / KnowledgeOverviewPage | 导入/总览 | ✅ |
| KnowledgeReviewPage / SimilarCasePage / RuleGapPage | 评审/相似案例/规则缺口（服务封装+告警规则/策略） | ✅（RuleGap 设计较巧） |
| AiDiagnosisPage | AI 诊断记录+Agent 运行+反馈 | 与 response 域 AI 诊断重叠 🟡 |
| PromptTemplatePage / AIToolPolicyPage | `/aiops/prompt-templates`、`/aiops/tool-policies` | AI 治理 ✅ |

## 9. 报表审计中心 report-audit-center（15）
| 页面 | 接线 | 评价 |
|---|---|---|
| ReportTemplate/Generate/Task/Preview/OverviewPage | 报告模板/生成/任务/预览（本轮生成器落地） | ✅ |
| ReportArchivePage / OpsReportPage / AssetReportPage / AutomationReportPage / InspectionReportPage | 各类报表 | ✅（与 inspection 域 InspectionReport 重复 🟡） |
| ComplianceReportPage | `/report/*`（本轮修正路径+合规生成） | ✅（合规建模仍较浅） |
| ExportCenterPage | 导出 CRUD | ✅ |
| AuditQueryPage / LogSearchPage | 审计/日志检索（`AUDIT`） | ✅ |
| EvidenceArchivePage | 告警证据链归档 | ✅ |

## 10. 平台管理 platform-management（18）
| 页面 | 接线 | 评价 |
|---|---|---|
| UserManagementPage / RoleManagementPage / PermissionPolicyPage / ApiKeyPage | 用户/角色/权限/Key（本轮 require_admin 收口） | ✅ |
| AuditLogPage / PlatformHealthPage / SelfCheckPage / SystemConfigPage | 审计/健康/自检/系统配置 | ✅ |
| BackupPage | 备份（本轮 DB 持久化+真实产物） | ✅ |
| DictionaryPage | 字典（本轮建表+CRUD） | ✅ |
| IntegrationPage / TaskQueuePage | 集成/任务队列（队列列名本轮修正） | ✅ |
| TenantManagementPage | 租户（本轮建表） | ⚠️ 无数据隔离（伪多租户） 🟡 |
| LicensePage / UpgradeMaintenancePage | 许可证/升级历史（本轮新增端点） | ✅ |
| ModelServicePage | 模型服务（本轮新增 CRUD+测试+全局配置） | ✅ |
| LoginPage | 登录（走 authStore，正常无业务 API） | ✅ |

## 11. 工单中心 ticket-center（9）+ AI 中心（1）
| 页面 | 接线 | 评价 |
|---|---|---|
| TicketList/Detail/Create/OverviewPage | 工单全生命周期+评论+转知识 | ✅（闭环"沉淀"段） |
| SlaManagementPage / AssignmentRulePage / TicketReportPage / PostmortemPage / ManualHandlingPage | SLA/派单/报表/复盘/人工处理 | ✅（附件为 stub 🟡） |
| ai-center/AiAssistantPage | `/ai/chat` `/ai/execute`（本轮新增） | ✅ |

---

## 12. 需处理的问题清单（按优先级）

**🔴 高**
1. **生产执行器缺失**：`automation` 全段（执行/审批/回滚/试运行/策略落地）在生产不可用（仅 `LocalDevExecutor`，prod 抛错）。建议实现 SSH/sandbox executor 或明确降级声明。
2. **2 个纯静态占位页**：`resource-center/LifecyclePage`、`automation-center/RemediationTemplatePage`——无任何后端。建议接后端或下线/标注 Beta。

**🟡 中（设计合理性）**
3. **页面重复/重叠**（124 页偏多）：
   - AI 诊断三处：`knowledge/AiDiagnosisPage`、`response/AiDiagnosisPanelPage`、`response/IncidentResponsePage`、`response/IncidentWorkspacePage`。
   - 巡检报告两处：`inspection/InspectionReportPage` 与 `report-audit/InspectionReportPage`。
   - 采集结果/健康：`CollectorPage`/`CollectionResultPage`/`CollectorHealthPage` 数据重叠。
   - 发现结果两处：`AssetDiscoveryPage` 内含 + `DiscoveryResultPage`。
   建议合并或明确分工，降低维护面与用户困惑。
4. **功能偏薄页**：`RiskGradingPage`/`ResponseSuggestionPage`/`ClosureVerificationPage`/`DailySummaryPage`/合规报告——单数据源或聚合浅，建议补全或合并。
5. **工单附件为 stub**：无真实上传/存储模型。
6. **多租户伪隔离**：有租户页但核心表无 `tenant_id`，跨租户不隔离。

**说明**：经本轮系列修复，「接口缺失/假数据/点击空白/跳登录」类**结构性**问题已基本清零；剩余为**功能深度与设计收敛**问题，属产品取舍，建议按上表排期。
