import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  const users = ref([])
  const balances = ref([])
  const transactions = ref([])
  const deletedTransactions = ref([])
  const settlementsSuggestions = ref([])
  const settlementHistory = ref([])
  const currentUser = ref(null)
  const token = ref(localStorage.getItem('wbw_token'))
  const backendStatus = ref('Connecting...')

  const isAuthenticated = computed(() => !!token.value && !!currentUser.value)
  const groupMembers = computed(() => users.value.filter(u => u.is_group_member))

  const totalGroupSpend = computed(() => {
    return transactions.value.reduce((sum, t) => sum + t.amount, 0)
  })
  
  const apiFetch = async (endpoint, options = {}) => {
    const headers = { 'Content-Type': 'application/json', ...options.headers }
    if (token.value) headers['Authorization'] = `Bearer ${token.value}`
    
    const response = await fetch(`http://localhost:5001${endpoint}`, { ...options, headers })
    if (response.status === 401) {
      logout()
      throw new Error('Unauthorized')
    }
    return response
  }

  const fetchData = async () => {
    if (!token.value) return
    try {
      const [uR, bR, tR, sS, sH] = await Promise.all([
        apiFetch('/users'), 
        apiFetch('/balances'), 
        apiFetch('/transactions'), 
        apiFetch('/settlements/suggest'),
        apiFetch('/settlements/history')
      ])
      
      users.value = await uR.json()
      balances.value = await bR.json()
      transactions.value = await tR.json()
      settlementsSuggestions.value = await sS.json()
      settlementHistory.value = await sH.json()
      backendStatus.value = 'Online'
      
      const savedUserStr = localStorage.getItem('wbw_user')
      if (savedUserStr) currentUser.value = JSON.parse(savedUserStr)
    } catch (e) { 
      backendStatus.value = 'Offline' 
    }
  }

  const fetchTrash = async () => {
    if (!token.value) return
    try {
      const res = await apiFetch('/transactions?deleted=true')
      deletedTransactions.value = await res.json()
    } catch (e) {
      console.error('Failed to fetch trash:', e)
    }
  }

  const login = (data) => {
    token.value = data.token
    currentUser.value = data.user
    localStorage.setItem('wbw_token', data.token)
    localStorage.setItem('wbw_user', JSON.stringify(data.user))
    fetchData()
  }

  const logout = () => {
    token.value = null
    currentUser.value = null
    localStorage.removeItem('wbw_token')
    localStorage.removeItem('wbw_user')
  }

  return { 
    users, balances, transactions, deletedTransactions, settlementsSuggestions, settlementHistory, 
    currentUser, token, backendStatus, isAuthenticated, groupMembers, totalGroupSpend,
    apiFetch, fetchData, fetchTrash, login, logout 
  }
})
