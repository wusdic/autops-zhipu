import client from './client'
import { API } from './routes'

export const discoveryTemplateService = {
  list: (params?: Record<string, any>) => client.get(API.DISCOVERY_TEMPLATES, { params }),
  get: (id: string) => client.get(API.DISCOVERY_TEMPLATE_DETAIL(id)),
  create: (data: Record<string, any>) => client.post(API.DISCOVERY_TEMPLATES, data),
  update: (id: string, data: Record<string, any>) => client.put(API.DISCOVERY_TEMPLATE_DETAIL(id), data),
  delete: (id: string) => client.delete(API.DISCOVERY_TEMPLATE_DETAIL(id)),
  toggle: (id: string) => client.post(API.DISCOVERY_TEMPLATE_TOGGLE(id)),
}
