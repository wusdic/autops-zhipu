import client from './client'
import { API } from './routes'

export const configService = {
  list: (params?: Record<string, any>) => client.get(API.CONFIGS, { params }),
  get: (id: string) => client.get(API.CONFIG_DETAIL(id)),
  create: (data: Record<string, any>) => client.post(API.CONFIGS, data),
  update: (id: string, data: Record<string, any>) => client.put(API.CONFIG_DETAIL(id), data),
  delete: (id: string) => client.delete(API.CONFIG_DETAIL(id)),
  publish: (id: string) => client.post(API.CONFIG_PUBLISH(id)),
  rollback: (id: string, data: Record<string, any>) => client.post(API.CONFIG_ROLLBACK(id), data),
  getVersions: (id: string, params?: Record<string, any>) => client.get(API.CONFIG_VERSIONS(id), { params }),
  getDiff: (id: string, params: { from_version: number; to_version: number }) => client.get(API.CONFIG_DIFF(id), { params }),
}
