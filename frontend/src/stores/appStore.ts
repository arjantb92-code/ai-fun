import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { 
  User, 
  Balance, 
  Transaction, 
  SettlementSuggestion, 
  SettlementSession, 
  Activity,
  BackendStatus,
  LoginResponse
} from '@/types'

export const useAppStore = defineStore('app', () => {
  // --- State ---
  const users = ref<User[]>([])
  const balances = ref<Balance[]>([])
  const transactions = ref<Transaction[]>([])
  const deletedTransactions = ref<Transaction[]>([])
  const settlementsSuggestions = ref<SettlementSuggestion[]>([])
  const settlementHistory = ref<SettlementSession[]>([])
  const activities = ref<Activity[]>([])
  const currentUser = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('wbw_token'))
  const backendStatus = ref<BackendStatus>('Connecting...')

  // --- Computed ---
  const isAuthenticated = computed(() => !!token.value && !!currentUser.value)
  const groupMembers = computed(() => users.value.filter(u => u.is_group_member))
  const totalGroupSpend = computed(() => {
    return transactions.value.reduce((sum, t) => sum + t.amount, 0)
  })
  
  // --- Actions ---
  const apiFetch = async (endpoint: string, options: RequestInit = {}): Promise<Response> => {
    const headers: Record<string, string> = { 
      'Content-Type': 'application/json', 
      ...(options.headers as Record<string, string> || {}) 
    }
    if (token.value) headers['Authorization'] = `Bearer ${token.value}`
    
    const response = await fetch(`http://localhost:5001${endpoint}`, { ...options, headers })
    if (response.status === 401) {
      logout()
      throw new Error('Unauthorized')
    }
    return response
  }

  const fetchData = async (activityId: number | null = null): Promise<void> => {
    if (!token.value) return
    try {
      const results = await Promise.all([
        apiFetch('/users'), 
        apiFetch(activityId ? `/balances?activity_id=${activityId}` : '/balances'), 
        apiFetch(activityId ? `/transactions?activity_id=${activityId}` : '/transactions'), 
        apiFetch(activityId ? `/settlements/suggest?activity_id=${activityId}` : '/settlements/suggest'),
        apiFetch('/settlements/history'),
        apiFetch('/activities')
      ])
      
      const [uR, bR, tR, sS, sH, aR] = results
      
      users.value = await uR.json() as User[]
      balances.value = await bR.json() as Balance[]
      transactions.value = await tR.json() as Transaction[]
      settlementsSuggestions.value = await sS.json() as SettlementSuggestion[]
      settlementHistory.value = await sH.json() as SettlementSession[]
      activities.value = await aR.json() as Activity[]
      backendStatus.value = 'Online'
      
      const savedUserStr = localStorage.getItem('wbw_user')
      if (savedUserStr) currentUser.value = JSON.parse(savedUserStr) as User
    } catch {
      backendStatus.value = 'Offline'
    }
  }

  const fetchTrash = async (activityId: number | null = null): Promise<void> => {
    if (!token.value) return
    try {
      const url = activityId ? `/transactions?deleted=true&activity_id=${activityId}` : '/transactions?deleted=true'
      const r = await apiFetch(url)
      deletedTransactions.value = await r.json() as Transaction[]
    } catch {
      deletedTransactions.value = []
    }
  }

  const login = (data: LoginResponse): void => {
    token.value = data.token
    currentUser.value = data.user
    localStorage.setItem('wbw_token', data.token)
    localStorage.setItem('wbw_user', JSON.stringify(data.user))
    fetchData()
  }

  const logout = (): void => {
    token.value = null
    currentUser.value = null
    localStorage.removeItem('wbw_token')
    localStorage.removeItem('wbw_user')
  }

  return {
    // State
    users, 
    balances, 
    transactions, 
    settlementsSuggestions, 
    settlementHistory, 
    activities,
    deletedTransactions, 
    currentUser, 
    token, 
    backendStatus, 
    // Computed
    isAuthenticated, 
    groupMembers, 
    totalGroupSpend,
    // Actions
    apiFetch, 
    fetchData, 
    fetchTrash, 
    login, 
    logout
  }
})
