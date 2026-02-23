import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { API_BASE } from '@/config/api'
import { BRAND_RED } from '@/config/theme'
import type { 
  User, 
  Balance, 
  Transaction, 
  SettlementSuggestion, 
  SettlementSession, 
  Activity,
  BalanceList,
  BackendStatus,
  LoginResponse,
  CategoryKey
} from '@/types'

interface Category {
  key: CategoryKey
  label: string
}

export const useAppStore = defineStore('app', () => {
  // --- State ---
  const users = ref<User[]>([])
  const balances = ref<Balance[]>([])
  const transactions = ref<Transaction[]>([])
  const deletedTransactions = ref<Transaction[]>([])
  const settlementsSuggestions = ref<SettlementSuggestion[]>([])
  const settlementHistory = ref<SettlementSession[]>([])
  const activities = ref<Activity[]>([])
  const balanceLists = ref<BalanceList[]>([])
  const currentBalanceListId = ref<number | null>(
    localStorage.getItem('wbw_balance_list_id') 
      ? parseInt(localStorage.getItem('wbw_balance_list_id')!) 
      : null
  )
  const categories = ref<Category[]>([
    { key: 'boodschappen', label: 'Boodschappen' },
    { key: 'huishoudelijk', label: 'Huishoudelijk' },
    { key: 'winkelen', label: 'Winkelen' },
    { key: 'vervoer', label: 'Vervoer' },
    { key: 'reizen_vrije_tijd', label: 'Reizen & Vrije Tijd' },
    { key: 'overig', label: 'Overig' }
  ])
  const currentUser = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('wbw_token'))
  const backendStatus = ref<BackendStatus>('Connecting...')
  const isLoading = ref(false)

  // --- Computed ---
  const isAuthenticated = computed(() => !!token.value && !!currentUser.value)
  const hasSelectedBalanceList = computed(() => !!currentBalanceListId.value)
  const currentBalanceList = computed(() => 
    balanceLists.value.find(bl => bl.id === currentBalanceListId.value) || null
  )
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
    
    const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers })
    if (response.status === 401) {
      logout()
      throw new Error('Unauthorized')
    }
    return response
  }

  const fetchBalanceLists = async (): Promise<void> => {
    if (!token.value) return
    try {
      const r = await apiFetch('/balance-lists')
      balanceLists.value = await r.json() as BalanceList[]
    } catch {
      balanceLists.value = []
    }
  }

  const fetchData = async (activityId: number | null = null): Promise<void> => {
    if (!token.value) return
    isLoading.value = true
    try {
      // Build query params based on current balance list
      const blParam = currentBalanceListId.value ? `balance_list_id=${currentBalanceListId.value}` : ''
      const actParam = activityId ? `activity_id=${activityId}` : ''
      const buildUrl = (base: string, ...params: string[]) => {
        const filtered = params.filter(Boolean)
        return filtered.length ? `${base}?${filtered.join('&')}` : base
      }

      const results = await Promise.all([
        apiFetch(buildUrl('/users', blParam)), 
        apiFetch(buildUrl('/balances', blParam, actParam)), 
        apiFetch(buildUrl('/transactions', blParam, actParam)), 
        apiFetch(buildUrl('/settlements/suggest', blParam, actParam)),
        apiFetch(buildUrl('/settlements/history', blParam)),
        apiFetch(buildUrl('/activities', blParam)),
        apiFetch('/balance-lists')
      ])
      
      const [uR, bR, tR, sS, sH, aR, blR] = results
      
      users.value = await uR.json() as User[]
      balances.value = await bR.json() as Balance[]
      transactions.value = await tR.json() as Transaction[]
      settlementsSuggestions.value = await sS.json() as SettlementSuggestion[]
      settlementHistory.value = await sH.json() as SettlementSession[]
      activities.value = await aR.json() as Activity[]
      balanceLists.value = await blR.json() as BalanceList[]
      backendStatus.value = 'Online'
      
      const savedUserStr = localStorage.getItem('wbw_user')
      if (savedUserStr) currentUser.value = JSON.parse(savedUserStr) as User
    } catch {
      backendStatus.value = 'Offline'
    } finally {
      isLoading.value = false
    }
  }

  const fetchTrash = async (activityId: number | null = null): Promise<void> => {
    if (!token.value) return
    try {
      const params = ['deleted=true']
      if (currentBalanceListId.value) params.push(`balance_list_id=${currentBalanceListId.value}`)
      if (activityId) params.push(`activity_id=${activityId}`)
      const url = `/transactions?${params.join('&')}`
      const r = await apiFetch(url)
      deletedTransactions.value = await r.json() as Transaction[]
    } catch {
      deletedTransactions.value = []
    }
  }

  const setCurrentUser = (user: User | null): void => {
    currentUser.value = user
    if (user) {
      localStorage.setItem('wbw_user', JSON.stringify(user))
    } else {
      localStorage.removeItem('wbw_user')
    }
  }

  const login = (data: LoginResponse): void => {
    token.value = data.token
    setCurrentUser(data.user)
    localStorage.setItem('wbw_token', data.token)
    // Clear balance list selection on new login
    currentBalanceListId.value = null
    localStorage.removeItem('wbw_balance_list_id')
    fetchBalanceLists()
  }

  const $reset = (): void => {
    users.value = []
    balances.value = []
    transactions.value = []
    deletedTransactions.value = []
    settlementsSuggestions.value = []
    settlementHistory.value = []
    activities.value = []
    balanceLists.value = []
    currentBalanceListId.value = null
    currentUser.value = null
    token.value = null
    backendStatus.value = 'Connecting...'
    isLoading.value = false
    localStorage.removeItem('wbw_token')
    localStorage.removeItem('wbw_user')
    localStorage.removeItem('wbw_balance_list_id')
  }

  const selectBalanceList = (id: number | null): void => {
    currentBalanceListId.value = id
    if (id) {
      localStorage.setItem('wbw_balance_list_id', id.toString())
    } else {
      localStorage.removeItem('wbw_balance_list_id')
    }
  }

  const createBalanceList = async (data: { name: string; currency: string }): Promise<BalanceList | null> => {
    try {
      const r = await apiFetch('/balance-lists', {
        method: 'POST',
        body: JSON.stringify(data)
      })
      const json = await r.json()
      if (json.balance_list) {
        balanceLists.value.push(json.balance_list)
        return json.balance_list
      }
      return null
    } catch {
      return null
    }
  }

  const joinBalanceList = async (inviteCode: string): Promise<{ success: boolean; message: string; balanceList?: BalanceList }> => {
    try {
      const r = await apiFetch(`/balance-lists/join/${inviteCode}`, {
        method: 'POST'
      })
      const json = await r.json()
      if (json.status === 'success' || json.status === 'already_member') {
        await fetchBalanceLists()
        return { 
          success: true, 
          message: json.status === 'already_member' ? 'Je bent al lid van deze balans.' : 'Je bent toegevoegd!',
          balanceList: json.balance_list 
        }
      }
      return { success: false, message: json.error || 'Onbekende fout' }
    } catch {
      return { success: false, message: 'Kon niet verbinden' }
    }
  }

  const lookupBalanceList = async (inviteCode: string): Promise<{ id: number; name: string; currency: string; member_count: number; is_member: boolean } | null> => {
    try {
      const r = await apiFetch(`/balance-lists/lookup/${inviteCode}`)
      if (r.ok) {
        return await r.json()
      }
      return null
    } catch {
      return null
    }
  }

  const logout = (): void => {
    $reset()
  }

  const getUserName = (id: number): string =>
    users.value.find(u => u.id === id)?.name ?? 'Onbekend'

  const getBalanceForUser = (userId: number): number =>
    balances.value.find(b => b.user_id === userId)?.balance ?? 0

  const getActivityInfo = (id: number | null): { name: string; icon: string; color: string } | null => {
    if (!id) return null
    const a = activities.value.find(a => a.id === id)
    return a ? { name: a.name, icon: a.icon ?? '📋', color: a.color ?? BRAND_RED } : null
  }

  return {
    // State
    users, 
    balances, 
    transactions, 
    settlementsSuggestions, 
    settlementHistory, 
    activities,
    balanceLists,
    currentBalanceListId,
    categories,
    deletedTransactions, 
    currentUser, 
    token, 
    backendStatus,
    isLoading,
    // Computed
    isAuthenticated, 
    hasSelectedBalanceList,
    currentBalanceList,
    groupMembers, 
    totalGroupSpend,
    // Actions
    apiFetch, 
    fetchData, 
    fetchBalanceLists,
    fetchTrash, 
    login, 
    logout,
    setCurrentUser,
    $reset,
    getUserName,
    getBalanceForUser,
    getActivityInfo,
    selectBalanceList,
    createBalanceList,
    joinBalanceList,
    lookupBalanceList
  }
})
