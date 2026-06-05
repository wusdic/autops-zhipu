import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ticketService } from '@/shared/api'

export const useTicketStore = defineStore('ticket', () => {
  const tickets = ref<any[]>([])
  const total = ref(0)
  const currentTicket = ref<any | null>(null)
  const loading = ref(false)

  const openTickets = computed(() => tickets.value.filter(t => t.status !== 'closed' && t.status !== 'resolved'))
  const myTickets = computed(() => tickets.value.filter(t => t.assignee_id === currentTicket.value?.assignee_id))

  async function fetchList(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await ticketService.list(params)
      tickets.value = res.data?.items || []
      total.value = res.data?.total || 0
    } finally {
      loading.value = false
    }
  }

  async function fetchDetail(id: string) {
    const res = await ticketService.get(id)
    currentTicket.value = res.data
    return res.data
  }

  async function create(data: Record<string, any>) {
    const res = await ticketService.create(data)
    await fetchList()
    return res.data
  }

  async function changeStatus(id: string, status: string, comment?: string) {
    await ticketService.update(id, { status, comment })
    await fetchDetail(id)
  }

  async function addComment(id: string, content: string) {
    await ticketService.addComment(id, { content })
  }

  return { tickets, total, currentTicket, loading, openTickets, myTickets, fetchList, fetchDetail, create, changeStatus, addComment }
})
