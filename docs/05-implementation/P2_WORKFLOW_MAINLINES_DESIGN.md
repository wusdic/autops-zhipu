# P2 五条自动化主线端到端串联设计

> 状态：accepted  
> 日期：2026-06-03  
> 目标：在已有页面间建立导航链路和数据传递，实现五条自动化主线的端到端可操作流程

---

## 设计原则

1. **不新增页面** — 五条主线通过已有页面的导航增强实现
2. **导航增强** — 在关键操作点添加"下一步"按钮/链接
3. **数据传递** — 通过 route query/params 在页面间传递上下文
4. **状态联动** — 操作完成后自动跳转到流程下一步

## 主线1: 发现→资产

```
AssetDiscoveryPage → [扫描] → DiscoveryResultPage → [纳管] → AssetDetailPage → [绑定模板] → InspectionTemplatePage
```

增强点:
- DiscoveryResultPage: "纳管"按钮 → `router.push({path:'/assets', query:{from:'discovery', ids:...}})`
- AssetDetailPage: "绑定巡检模板"快捷入口
- ResourceOverviewPage: 发现统计摘要

## 主线2: 巡检→异常

```
InspectionTemplatePage → [创建计划] → InspectionPlanPage → [执行] → InspectionTaskPage → [查看异常] → AnomalyListPage
```

增强点:
- InspectionTaskPage: 异常项增加"查看异常详情"链接
- InspectionResultPage: 失败项增加"创建异常"按钮
- InspectionReportPage: 报告中的异常项链接到异常列表

## 主线3: 异常→处置

```
AnomalyListPage → [详情] → AnomalyDetailPage → [匹配策略/AI分析] → IncidentResponsePage → [执行] → ExecutionDetailPage → [验证] → 关闭异常
```

增强点:
- AnomalyDetailPage: "触发AI诊断"按钮 → AiDiagnosisPanelPage
- AnomalyDetailPage: "匹配策略"按钮 → PolicySimulatePage
- AnomalyDetailPage: "创建工单"按钮 → TicketCreatePage (带异常ID)
- IncidentResponsePage: 完成后链接回异常详情关闭

## 主线4: 处置→报告

```
ExecutionDetailPage → [生成报告] → ReportGeneratePage → [预览] → ReportPreviewPage → [归档] → ReportArchivePage
```

增强点:
- ExecutionDetailPage: "生成执行报告"按钮
- TicketDetailPage: "生成工单报告"按钮
- ReportGeneratePage: 支持从执行/工单页面带参数跳转

## 主线5: 首页指挥台贯穿

```
CommandDashboardPage: 五条主线入口卡片
  → 发现入口 → AssetDiscoveryPage
  → 巡检入口 → InspectionOverviewPage
  → 异常入口 → AnomalyOverviewPage
  → 处置入口 → IncidentResponsePage
  → 报告入口 → ReportOverviewPage
```

增强点:
- CommandDashboardPage: 五条主线快捷入口
- 每条主线显示最新状态和待处理数量

## 实现方案

### 1. 导航工具函数

创建 `@/shared/composables/useWorkflowNav.ts`：

```typescript
export function useWorkflowNav() {
  const router = useRouter()
  
  // 发现→资产
  const navToAssetFromDiscovery = (ids: string[]) => {
    router.push({ path: '/assets', query: { from: 'discovery', ids: ids.join(',') } })
  }
  
  // 异常→处置
  const navToRemediationFromAnomaly = (anomalyId: string) => {
    router.push({ path: '/incident-response', query: { anomaly_id: anomalyId } })
  }
  
  // 异常→AI诊断
  const navToAIFromAnomaly = (anomalyId: string) => {
    router.push({ path: '/ai-diagnosis', query: { anomaly_id: anomalyId } })
  }
  
  // 异常→工单
  const navToTicketFromAnomaly = (anomalyId: string) => {
    router.push({ path: '/tickets/create', query: { anomaly_id: anomalyId } })
  }
  
  // 执行→报告
  const navToReportFromExecution = (executionId: string) => {
    router.push({ path: '/report/generate', query: { execution_id: executionId } })
  }
  
  // 工单→报告
  const navToReportFromTicket = (ticketId: string) => {
    router.push({ path: '/report/generate', query: { ticket_id: ticketId } })
  }
  
  return { ... }
}
```

### 2. 页面增强内容

每个流程节点的页面增加 `workflow-actions` 区域，包含"上一步"和"下一步"链接。

### 3. 数据传递约定

通过 `route.query` 传递上下文:
- `from`: 来源页面标识
- `anomaly_id`: 异常ID
- `execution_id`: 执行ID
- `ticket_id`: 工单ID
- `asset_ids`: 资产ID列表
