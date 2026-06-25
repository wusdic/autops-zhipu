/**
 * AUTOPS 五条自动化主线工作流导航
 *
 * 提供跨页面的流程跳转函数，支持在发现→巡检→异常→处置→报告五条主线间导航。
 * 数据通过 route.query 传递。
 */

import { useRouter, useRoute } from 'vue-router'

export function useWorkflowNav() {
  const router = useRouter()
  const route = useRoute()

  // ========== 主线1: 发现→资产 ==========

  /** 从发现结果纳管到资产列表 */
  const navToAssetFromDiscovery = (assetIds: string[]) => {
    router.push({
      path: '/assets',
      query: { from: 'discovery', ids: assetIds.join(',') },
    })
  }

  /** 从资产详情绑定巡检模板 */
  const navToInspectionFromAsset = (assetId: string) => {
    router.push({
      path: '/inspection/templates',
      query: { from: 'asset', asset_id: assetId },
    })
  }

  // ========== 主线2: 巡检→异常 ==========

  /** 从巡检任务查看异常 */
  const navToAnomalyFromInspection = (taskId: string) => {
    router.push({
      path: '/anomalies',
      query: { from: 'inspection', task_id: taskId },
    })
  }

  /** 从巡检结果生成报告 */
  const navToReportFromInspection = (taskId: string) => {
    router.push({
      path: '/report/generate',
      query: { from: 'inspection', task_id: taskId },
    })
  }

  // ========== 主线3: 异常→处置 ==========

  /** 从异常详情进入AI诊断 */
  const navToAIFromAnomaly = (anomalyId: string) => {
    router.push({
      path: '/ai-diagnosis',
      query: { from: 'anomaly', anomaly_id: anomalyId },
    })
  }

  /** 从异常详情进入故障处置 */
  const navToRemediationFromAnomaly = (anomalyId: string) => {
    router.push({
      path: '/incident-response',
      query: { from: 'anomaly', anomaly_id: anomalyId },
    })
  }

  /** 从异常详情创建工单 */
  const navToTicketFromAnomaly = (anomalyId: string) => {
    router.push({
      path: '/tickets/create',
      query: { from: 'anomaly', anomaly_id: anomalyId },
    })
  }

  /** 从异常详情匹配策略 */
  const navToPolicyFromAnomaly = (anomalyId: string) => {
    router.push({
      path: '/policies',
      query: { from: 'anomaly', anomaly_id: anomalyId },
    })
  }

  // ========== 主线4: 处置→报告 ==========

  /** 从执行详情生成报告 */
  const navToReportFromExecution = (executionId: string) => {
    router.push({
      path: '/report/generate',
      query: { from: 'execution', execution_id: executionId },
    })
  }

  /** 从工单详情生成报告 */
  const navToReportFromTicket = (ticketId: string) => {
    router.push({
      path: '/report/generate',
      query: { from: 'ticket', ticket_id: ticketId },
    })
  }

  /** 从工单详情转知识（新建知识草稿，带工单信息预填） */
  const navToKnowledgeFromTicket = (ticketId: string) => {
    router.push({
      path: '/knowledge/new/edit',
      query: { from: 'ticket', ticket_id: ticketId },
    })
  }

  // ========== 主线5: 首页指挥台 ==========

  const navToDiscovery = () => router.push('/asset-discovery')
  const navToInspection = () => router.push('/inspection')
  const navToAnomalies = () => router.push('/anomalies')
  const navToIncidentResponse = () => router.push('/incident-response')
  const navToReports = () => router.push('/reports')

  // ========== 辅助 ==========

  /** 获取当前页面从哪个工作流跳转来 */
  const getWorkflowContext = () => {
    return {
      from: route.query.from as string | undefined,
      anomalyId: route.query.anomaly_id as string | undefined,
      executionId: route.query.execution_id as string | undefined,
      ticketId: route.query.ticket_id as string | undefined,
      taskId: route.query.task_id as string | undefined,
      assetId: route.query.asset_id as string | undefined,
      assetIds: route.query.ids ? (route.query.ids as string).split(',') : [],
    }
  }

  return {
    // 主线1
    navToAssetFromDiscovery,
    navToInspectionFromAsset,
    // 主线2
    navToAnomalyFromInspection,
    navToReportFromInspection,
    // 主线3
    navToAIFromAnomaly,
    navToRemediationFromAnomaly,
    navToTicketFromAnomaly,
    navToPolicyFromAnomaly,
    // 主线4
    navToReportFromExecution,
    navToReportFromTicket,
    navToKnowledgeFromTicket,
    // 主线5
    navToDiscovery,
    navToInspection,
    navToAnomalies,
    navToIncidentResponse,
    navToReports,
    // 辅助
    getWorkflowContext,
  }
}
