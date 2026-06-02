import client from './client'
import { API } from './routes'

export const assetService = {
  list: (params?: Record<string, any>) => client.get(API.ASSETS, { params }),
  get: (id: string) => client.get(API.ASSET_DETAIL(id)),
  create: (data: Record<string, any>) => client.post(API.ASSETS, data),
  update: (id: string, data: Record<string, any>) => client.put(API.ASSET_DETAIL(id), data),
  delete: (id: string) => client.delete(API.ASSET_DETAIL(id)),
  import: (data: FormData) => client.post(API.ASSET_IMPORT, data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  getRelations: (id: string) => client.get(API.ASSET_RELATIONS(id)),
  addRelation: (id: string, data: Record<string, any>) => client.post(API.ASSET_RELATIONS(id), data),
  deleteRelation: (assetId: string, relId: string) => client.delete(API.ASSET_RELATION_DELETE(assetId, relId)),
  getTimeline: (id: string) => client.get(API.ASSET_TIMELINE(id)),
  getCredentials: (id: string) => client.get(API.ASSET_CREDENTIALS(id)),
  bindCredential: (id: string, data: Record<string, any>) => client.post(API.ASSET_CREDENTIALS(id), data),
  unbindCredential: (assetId: string, credId: string) => client.delete(API.ASSET_CREDENTIAL_UNBIND(assetId, credId)),
  getCollectionConfigs: (id: string) => client.get(API.ASSET_COLLECTION_CONFIGS(id)),
  triggerCollection: (id: string) => client.post(API.ASSET_COLLECTION_TRIGGER(id)),
  getPolicies: (id: string) => client.get(API.ASSET_POLICIES(id)),
  bindPolicy: (id: string, data: Record<string, any>) => client.post(API.ASSET_POLICIES(id), data),
  unbindPolicy: (assetId: string, policyId: string) => client.delete(API.ASSET_POLICY_UNBIND(assetId, policyId)),
  discover: (data: Record<string, any>) => client.post(API.DISCOVERY_TASKS, data),
  getDiscoveryTasks: (params?: Record<string, any>) => client.get(API.DISCOVERY_TASKS, { params }),
  getDiscoveryResults: (params?: Record<string, any>) => client.get(API.DISCOVERY_RESULTS, { params }),
}
