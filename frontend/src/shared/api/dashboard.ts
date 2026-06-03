import client from './client'
import { API } from './routes'

export const dashboardService = {
  stats: () => client.get(API.DASHBOARD.STATS),
  assetDiscovery: () => client.get(API.DASHBOARD.ASSET_DISCOVERY_SUMMARY),
  inspectionSummary: () => client.get(API.DASHBOARD.INSPECTION_SUMMARY),
  anomalySummary: () => client.get(API.DASHBOARD.ANOMALY_SUMMARY),
  automationSummary: () => client.get(API.DASHBOARD.AUTOMATION_SUMMARY),
  reportSummary: () => client.get(API.DASHBOARD.REPORT_SUMMARY),
  platformHealth: () => client.get(API.DASHBOARD.PLATFORM_HEALTH),
  myPending: (userId: string) => client.get(API.DASHBOARD.MY_PENDING, { params: { user_id: userId } }),
}
