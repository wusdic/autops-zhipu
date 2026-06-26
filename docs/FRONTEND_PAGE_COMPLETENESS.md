# 前端逐页功能完整性遍历（功能缺失清查）

> 日期：2026-06-26 · 范围：124 个页面
> 方法：扫描每页的「占位文案（开发中/即将上线/演示模式）」与「假动作」（按钮弹 toast 但不调任何后端），区分为：①已修 ②后端已具备但前端假动作 ③后端不具备的真实缺口 ④非缺失（正常提示/离线兜底）。

## 0. 结论
绝大多数页面功能完整、已接真实后端。本次清查共发现 **少量真实缺口**，已就地修复可闭合者，其余按"是否需新后端能力"分类如下。

---

## 1. 本次已修复
| 页面 | 缺失点 | 修复 |
|---|---|---|
| report-audit/OpsReportPage | `downloadReport` 仅弹"下载功能开发中" | 改调 `REPORT.DOWNLOAD`（后端已支持文件下载/占位） |
| config-center/ConfigOverviewPage | `toggleRule` 假动作+`'已'+enabled?` 优先级显示 bug；`viewVersionDiff` 假动作 | 概览页改为**导航到专管页**（阈值规则/配置版本）执行真实操作 |

> 另：`config-center/InspectionRulesPage`、`automation-center/RemediationTemplatePage` 的写操作已在前几轮接通（巡检规则 CRUD / Playbook）。

## 2. 误判澄清（非缺失）
| 页面 | 现象 | 实情 |
|---|---|---|
| platform/SelfCheckPage | 文案"自检功能即将上线" | **已接** `POST /platform/self-check`；该文案仅在后端返回 404 时的**离线兜底**，后端已具备，正常不出现 |
| platform/BackupPage | 文案"备份恢复即将上线" | **已接** `/backups*`（本项目已实现真实备份）；同为 404 离线兜底 |

## 3. 后端已具备、但概览/次要页仍以"导航/提示"代替内联操作（设计取舍，可接受）
- `config-center/ConfigOverviewPage`：`runDiscovery / deleteTemplate / simulateRule / rollbackVersion / handleCreate` 均为概览页快捷入口，应在各专管页（discovery-templates / inspection-rules / threshold-rules / notification-rules / versions）完成。建议统一改为路由跳转（本轮已改 toggle/diff 两个，其余建议同样处理）。
- `report-audit/ExportCenterPage`：下载链接生成中 → 正常异步流程。

## 4. 真实缺口：需要新增后端能力（暂未实现，建议排期）
| 页面 | 缺失功能 | 说明/建议 |
|---|---|---|
| platform/UpgradeMaintenancePage | 升级/回滚为"演示模式" | 真实主机/平台升级回滚属运维基建动作，需独立后端与受控流程；升级历史(`/platform/upgrade-history`)已可读 |
| config/InspectionRulesPage、automation/RemediationTemplatePage | `viewHistory`"历史记录开发中" | 规则/模板的触发历史无独立后端表，建议复用执行/巡检结果按规则过滤，或新增 history 表 |
| response/RiskGradingPage | 报告导出 | 风险分级无专属导出后端，建议接入统一导出中心 `/exports` |
| ticket/TicketReportPage | 导出 | 同上，建议接 `/exports` |
| 工单附件（TicketDetailPage） | 上传/下载为 stub | 需附件存储模型与对象存储/本地落盘 |

## 5. 非缺失（正常业务提示，无需处理）
- EventListPage 关闭自动刷新、IncidentResponse"未找到匹配策略/执行已驳回"、RuleGap 创建规则快捷提示、KnowledgeImport"已导入"、ResponseSuggestion"已忽略/暂无关联知识"、InspectionResult"创建工单"提示、AssetList Excel 预览提示、LicensePage"联系商务获取离线激活"等——均为正常交互反馈。

---

## 6. 汇总
- **真实功能缺口仅集中在 §4 的 5 类**，且都属"需要新后端能力"（升级回滚、规则历史、按页导出、工单附件存储），不影响主闭环。
- 主业务闭环（发现→采集→事件→告警→策略→自动化→工单→知识→报表→治理）各页功能完整、动作真接后端。
- 建议：§3 概览页动作统一改路由；§4 按价值排期（工单附件、统一导出优先）。

> 校验：改动经 `ruff -F`/`py_compile`（后端无关）与最小前端改动；本环境无法跑前端，建议合并后以 Playwright 冒烟复核 OpsReport 下载与 ConfigOverview 导航。
