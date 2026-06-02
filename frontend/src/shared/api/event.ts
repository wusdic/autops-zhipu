import client from './client'
import { API } from './routes'

export const eventService = {
  list: (params?: Record<string, any>) => client.get(API.EVENTS, { params }),
  get: (id: string) => client.get(API.EVENT_DETAIL(id)),
}
