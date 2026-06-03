import client from './client'
import { API } from './routes'

export const monitoringService = {
  collectionResults: (params?: Record<string, any>) => client.get(API.MONITORING.COLLECTION_RESULTS, { params }),
  metricsTrend: (assetId: string, params?: Record<string, any>) => client.get(API.MONITORING.METRICS_TREND(assetId), { params }),
  stateSnapshots: (params?: Record<string, any>) => client.get(API.MONITORING.STATE_SNAPSHOTS, { params }),
  logSources: (params?: Record<string, any>) => client.get(API.MONITORING.LOG_SOURCES, { params }),
  collectorHealth: () => client.get(API.MONITORING.COLLECTOR_HEALTH),
}
