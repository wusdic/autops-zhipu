import client from './client'
import { API } from './routes'

export const ticketService = {
  list: (params?: Record<string, any>) => client.get(API.TICKETS, { params }),
  get: (id: string) => client.get(API.TICKET_DETAIL(id)),
  create: (data: Record<string, any>) => client.post(API.TICKETS, data),
  update: (id: string, data: Record<string, any>) => client.put(API.TICKET_DETAIL(id), data),
  addComment: (id: string, data: { content: string }) => client.post(API.TICKET_COMMENTS(id), data),
  getComments: (id: string) => client.get(API.TICKET_COMMENTS(id)),
  getAttachments: (id: string) => client.get(API.TICKET_ATTACHMENTS(id)),
  uploadAttachment: (id: string, data: FormData) => client.post(API.TICKET_ATTACHMENTS(id), data),
  deleteAttachment: (ticketId: string, attachmentId: string) => client.delete(API.TICKET_ATTACHMENT(ticketId, attachmentId)),
  convertToKnowledge: (id: string) => client.post(API.TICKET_CONVERT_KNOWLEDGE(id)),
  stats: () => client.get(API.TICKET_STATS),
}
