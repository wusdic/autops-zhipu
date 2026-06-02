import client from './client'
import { API } from './routes'

export const knowledgeService = {
  list: (params?: Record<string, any>) => client.get(API.KNOWLEDGE, { params }),
  get: (id: string) => client.get(API.KNOWLEDGE_DETAIL(id)),
  create: (data: Record<string, any>) => client.post(API.KNOWLEDGE, data),
  update: (id: string, data: Record<string, any>) => client.put(API.KNOWLEDGE_DETAIL(id), data),
  delete: (id: string) => client.delete(API.KNOWLEDGE_DETAIL(id)),
  publish: (id: string) => client.post(API.KNOWLEDGE_PUBLISH(id)),
  view: (id: string) => client.get(API.KNOWLEDGE_VIEW(id)),
  getRelated: (id: string) => client.get(API.KNOWLEDGE_RELATED(id)),
  getVersions: (id: string) => client.get(API.KNOWLEDGE_VERSIONS(id)),
  feedback: (id: string, data: Record<string, any>) => client.post(API.KNOWLEDGE_FEEDBACK(id), data),
  convertRunbook: (id: string) => client.post(API.KNOWLEDGE_CONVERT_RUNBOOK(id)),
  importValidate: (data: FormData) => client.post(API.KNOWLEDGE_IMPORT_VALIDATE, data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  importBatch: (data: FormData) => client.post(API.KNOWLEDGE_IMPORT_BATCH, data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  export: (params?: Record<string, any>) => client.get(API.KNOWLEDGE_EXPORT, { params }),
  stats: () => client.get(API.KNOWLEDGE_STATS),
}
