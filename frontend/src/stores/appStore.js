import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  const users = ref([])
  const balances = ref([])
  const transactions = ref([])
  const settlementsSuggestions = ref([])
  const settlementHistory = ref([])
  const activities = ref([])
  const deletedTransactions = ref([])
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

  const fetchData = async (activityId = null) => {
    if (!token.value) return
    try {
      const endpoints = [
        apiFetch('/users'), 
        apiFetch(activityId ? `/balances?activity_id=${activityId}` : '/balances'), 
        apiFetch(activityId ? `/transactions?activity_id=${activityId}` : '/transactions'), 
        apiFetch(activityId ? `/settlements/suggest?activity_id=${activityId}` : '/settlements/suggest'),
        apiFetch('/settlements/history'),
        apiFetch('/activities')
      ]
      const [uR, bR, tR, sS, sH, aR] = await Promise.all(endpoints)
      
      users.value = await uR.json()
      balances.value = await bR.json()
      transactions.value = await tR.json()
      settlementsSuggestions.value = await sS.json()
      settlementHistory.value = await sH.json()
      activities.value = await aR.json()
      backendStatus.value = 'Online'
      
      const savedUserStr = localStorage.getItem('wbw_user')
      if (savedUserStr) currentUser.value = JSON.parse(savedUserStr)
    } catch (e) {
      backendStatus.value = 'Offline'
    }
  }

  const fetchTrash = async (activityId = null) => {
    if (!token.value) return
    try {
      const url = activityId ? `/transactions?deleted=true&activity_id=${activityId}` : '/transactions?deleted=true'
      const r = await apiFetch(url)
      deletedTransactions.value = await r.json()
    } catch {
      deletedTransactions.value = []
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
    users, balances, transactions, settlementsSuggestions, settlementHistory, activities,
    deletedTransactions, currentUser, token, backendStatus, isAuthenticated, groupMembers, totalGroupSpend,
    apiFetch, fetchData, fetchTrash, login, logout
  }
})
