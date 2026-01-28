<script setup>
import { ref, computed, onMounted } from 'vue'

// --- State ---
const currentTab = ref('ACTIVITY') // 'ACTIVITY' or 'BALANCE'
const searchQuery = ref('')
const users = ref([])
const balances = ref([])
const transactions = ref([])
const settlementsSuggestions = ref([])
const settlementHistory = ref([])
const selectedTransaction = ref(null)
const isEditModalOpen = ref(false)
const isImportModalOpen = ref(false)
const isLoginModalOpen = ref(false)
const isProfileModalOpen = ref(false)
const backendStatus = ref('Connecting...')
const importBankType = ref('ing')
const importedTransactions = ref([])

// Authentication State
const currentUser = ref(null)
const token = ref(localStorage.getItem('wbw_token'))
const loginCredentials = ref({ username: '', password: '' })
const loginError = ref('')
const newAvatarUrl = ref('')
const newEmail = ref('')

// --- API Wrapper ---
const apiFetch = async (endpoint, options = {}) => {
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (token.value) headers['Authorization'] = `Bearer ${token.value}`
  const response = await fetch(`http://127.0.0.1:5001${endpoint}`, { ...options, headers })
  if (response.status === 401) { logout(); throw new Error('Unauthorized') }
  return response
}

// --- Computed ---
const groupMembers = computed(() => users.value.filter(u => u.is_group_member))
const externalUsers = computed(() => users.value.filter(u => !u.is_group_member))

const filteredTransactions = computed(() => {
  if (!searchQuery.value) return transactions.value
  const q = searchQuery.value.toLowerCase()
  return transactions.value.filter(t => 
    t.description.toLowerCase().includes(q) || 
    getPayerName(t.payer_id).toLowerCase().includes(q)
  )
})

const groupedTransactions = computed(() => {
  const groups = {}
  filteredTransactions.value.forEach(t => {
    const date = new Date(t.date)
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(today.getDate() - 1)
    
    let label = ''
    if (date.toDateString() === today.toDateString()) label = 'Vandaag'
    else if (date.toDateString() === yesterday.toDateString()) label = 'Gisteren'
    else label = date.toLocaleDateString('nl-NL', { day: 'numeric', month: 'long', year: 'numeric' })
    
    if (!groups[label]) groups[label] = []
    groups[label].push(t)
  })
  return groups
})

const totalGroupSpend = computed(() => transactions.value.filter(t => t.type === 'EXPENSE').reduce((acc, t) => acc + t.amount, 0))

const myBalance = computed(() => {
  if (!currentUser.value) return 0
  return balances.value.find(b => b.user_id === currentUser.value.id)?.balance || 0
})

// --- Methods ---
const fetchData = async () => {
  if (!token.value) { return } // Restricted Access screen auto-triggers
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
    if (savedUserStr) {
       currentUser.value = JSON.parse(savedUserStr)
       newAvatarUrl.value = currentUser.value.avatar_url
       newEmail.value = currentUser.value.email
    }
  } catch (e) { backendStatus.value = 'Offline' }
}

const performLogin = async () => {
  loginError.value = ''
  try {
    const res = await fetch('http://127.0.0.1:5001/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(loginCredentials.value)
    })
    const data = await res.json()
    if (res.ok) {
      token.value = data.token
      currentUser.value = data.user
      localStorage.setItem('wbw_token', data.token)
      localStorage.setItem('wbw_user', JSON.stringify(data.user))
      loginCredentials.value = { username: '', password: '' }
      newAvatarUrl.value = data.user.avatar_url
      newEmail.value = data.user.email
      await fetchData()
    } else { 
      loginError.value = data.message || 'Invalid credentials' 
    }
  } catch { 
    loginError.value = 'Server Offline - Backend unavailable' 
  }
}

const updateProfile = async () => {
  try {
    const res = await apiFetch('/users/profile', {
      method: 'PUT',
      body: JSON.stringify({ avatar_url: newAvatarUrl.value, email: newEmail.value })
    })
    if (res.ok) {
      const data = await res.json(); currentUser.value = data.user
      localStorage.setItem('wbw_user', JSON.stringify(data.user))
      await fetchData(); alert('Profiel bijgewerkt')
    }
  } catch { alert('Update mislukt') }
}

const handleAvatarUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  const formData = new FormData(); formData.append('file', file)
  try {
    const response = await fetch('http://127.0.0.1:5001/users/avatar', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token.value}` },
      body: formData
    })
    const result = await response.json()
    if (response.ok) {
      currentUser.value = result.user; localStorage.setItem('wbw_user', JSON.stringify(result.user)); await fetchData()
    }
  } catch (e) { alert('Upload mislukt') }
}

const commitSettlement = async () => {
  if (!confirm('Weet je zeker dat je de balans wilt verrekenen? Alle huidige transacties worden gearchiveerd.')) return
  try {
    const res = await apiFetch('/settlements/commit', { method: 'POST' })
    if (res.ok) {
      alert('Balans verrekend!')
      await fetchData()
      currentTab.value = 'BALANCE'
    }
  } catch { alert('Verrekening mislukt') }
}

const logout = () => {
  token.value = null
  currentUser.value = null
  localStorage.removeItem('wbw_token')
  localStorage.removeItem('wbw_user')
  // Restricted Access screen auto-triggers when token is null
}

const openTransaction = (t) => { selectedTransaction.value = JSON.parse(JSON.stringify(t)); isEditModalOpen.value = true }
const closeEditModal = () => { isEditModalOpen.value = false; selectedTransaction.value = null }

const saveTransaction = async () => {
  const isNew = !selectedTransaction.value.id
  try {
    const res = await apiFetch(isNew ? '/transactions' : `/transactions/${selectedTransaction.value.id}`, {
      method: isNew ? 'POST' : 'PUT',
      body: JSON.stringify(selectedTransaction.value)
    })
    if (res.ok) { await fetchData(); closeEditModal() }
  } catch { alert('Opslaan mislukt') }
}

const deleteTransaction = async () => {
  if (!confirm('Verwijderen?')) return
  try {
    const res = await apiFetch(`/transactions/${selectedTransaction.value.id}`, { method: 'DELETE' })
    if (res.ok) { await fetchData(); closeEditModal() }
  } catch { alert('Verwijderen mislukt') }
}

const createNewEntry = () => {
  selectedTransaction.value = { 
    id: null, description: 'Nieuwe uitgave', amount: 0, date: new Date().toISOString().split('T')[0], 
    payer_id: currentUser.value?.id, type: 'EXPENSE',
    splits: groupMembers.value.map(u => ({ user_id: u.id, weight: 1 })) 
  }
  isEditModalOpen.value = true
}

const handleReceiptUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  const formData = new FormData(); formData.append('file', file)
  try {
        const res = await fetch('http://127.0.0.1:5001/ocr/process', { 
 method: 'POST', headers: { 'Authorization': `Bearer ${token.value}` }, body: formData })
    const result = await res.json()
    if (res.ok) {
       selectedTransaction.value.amount = result.data.extracted_data.total || selectedTransaction.value.amount
       selectedTransaction.value.description = result.data.extracted_data.merchant !== 'Unknown Merchant' ? result.data.extracted_data.merchant : selectedTransaction.value.description
    }
  } catch { alert('OCR mislukt') }
}

const handleBankImport = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  const formData = new FormData(); formData.append('file', file); formData.append('bank_type', importBankType.value)
  try {
        const res = await fetch('http://127.0.0.1:5001/import/bank', { 
 method: 'POST', headers: { 'Authorization': `Bearer ${token.value}` }, body: formData })
    const data = await res.json()
    if (res.ok) importedTransactions.value = data.transactions.map(t => ({ ...t, selected: true }))
  } catch { alert('Import mislukt') }
}

const confirmImport = async () => {
  for (const t of importedTransactions.value.filter(v => v.selected)) {
    await apiFetch('/transactions', { method: 'POST', body: JSON.stringify({ date: t.date, description: t.description, amount: Math.abs(t.amount), payer_id: currentUser.value.id, type: 'EXPENSE', splits: groupMembers.value.map(u => ({ user_id: u.id, weight: 1 })) }) })
  }
  await fetchData(); isImportModalOpen.value = false; importedTransactions.value = []
}

const toggleUserInSplit = (userId) => {
  const splits = selectedTransaction.value.splits
  const idx = splits.findIndex(s => s.user_id === userId)
  if (idx !== -1) splits.splice(idx, 1)
  else splits.push({ user_id: userId, weight: 1 })
}

const incrementWeight = (uId) => {
  const s = selectedTransaction.value.splits.find(s => s.user_id === uId)
  if (s) s.weight++
}

const decrementWeight = (uId) => {
  const s = selectedTransaction.value.splits.find(s => s.user_id === uId)
  if (s && s.weight > 1) s.weight--
}

const getPayerName = (id) => users.value.find(u => u.id === id)?.name || 'Onbekend'
const getBalanceForUser = (userId) => balances.value.find(b => b.user_id === userId)?.balance || 0

onMounted(fetchData)
</script>

<template>
  <div class="min-h-screen bg-trainmore-dark text-white font-industrial p-4 md:p-8 flex flex-col">
    <!-- Header -->
    <header class="flex flex-col md:flex-row justify-between items-center mb-8 border-b border-industrial-gray pb-6 gap-4 shrink-0">
      <div class="flex items-center gap-6">
        <h1 class="text-4xl font-bold tracking-tighter uppercase italic text-brand-red text-shadow-glow">Better WBW</h1>
        <div v-if="currentUser" @click="isProfileModalOpen = true" class="flex items-center gap-3 cursor-pointer group bg-zinc-900/50 px-4 py-2 border border-zinc-800 hover:border-brand-red transition-all">
           <div class="w-8 h-8 bg-black border border-zinc-700 overflow-hidden flex items-center justify-center">
              <img v-if="currentUser.avatar_url" :src="currentUser.avatar_url" class="w-full h-full grayscale group-hover:grayscale-0 transition-all object-cover" @error="currentUser.avatar_url = null">
              <span v-else class="text-[10px] font-black text-brand-red italic">{{ currentUser.name[0] }}</span>
           </div>
           <span class="text-xs font-black uppercase tracking-widest">{{ currentUser.name }}</span>
        </div>
      </div>
      <div class="flex gap-4 w-full md:w-auto" v-if="currentUser">
        <button @click="isImportModalOpen = true" class="bg-white text-black px-8 py-3 font-bold uppercase hover:bg-brand-red hover:text-white transition-all transform active:scale-95 italic text-sm shadow-xl">Bank Import</button>
        <button @click="createNewEntry" class="border-2 border-brand-red text-brand-red px-8 py-3 font-bold uppercase hover:bg-brand-red hover:text-white transition-all transform active:scale-95 italic text-sm">Nieuwe Post</button>
      </div>
    </header>

    <!-- Main Content with Tabs -->
    <div class="flex-1 max-w-[1600px] mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-8" v-if="currentUser">
      
      <!-- Tabs Sidebar -->
      <nav class="lg:col-span-2 space-y-2 shrink-0">
         <button @click="currentTab = 'ACTIVITY'" 
                 class="w-full text-left px-6 py-4 font-black uppercase italic tracking-widest text-sm transition-all border-r-4"
                 :class="currentTab === 'ACTIVITY' ? 'bg-industrial-gray border-brand-red text-white' : 'border-transparent text-zinc-600 hover:text-zinc-400'">
            Activiteit
         </button>
         <button @click="currentTab = 'BALANCE'" 
                 class="w-full text-left px-6 py-4 font-black uppercase italic tracking-widest text-sm transition-all border-r-4"
                 :class="currentTab === 'BALANCE' ? 'bg-industrial-gray border-brand-red text-white' : 'border-transparent text-zinc-600 hover:text-zinc-400'">
            Balans
         </button>
      </nav>

      <!-- Dynamic View -->
      <div class="lg:col-span-10">
         
         <!-- ACTIVITY TAB -->
         <div v-if="currentTab === 'ACTIVITY'" class="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
            <!-- Search Bar -->
            <div class="relative max-w-xl">
               <span class="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-700">🔍</span>
               <input v-model="searchQuery" type="text" 
                      class="w-full bg-industrial-gray border border-zinc-800 p-4 pl-12 font-black uppercase italic text-sm outline-none focus:border-brand-red transition-all" 
                      placeholder="Zoek transactie of persoon...">
            </div>

            <div class="space-y-12">
               <div v-for="(txs, label) in groupedTransactions" :key="label" class="space-y-4">
                  <h3 class="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500 italic border-b border-zinc-900 pb-2">{{ label }}</h3>
                  <div class="space-y-2">
                     <div v-for="t in txs" :key="t.id" @click="openTransaction(t)" 
                          class="bg-industrial-gray/40 p-5 flex justify-between items-center hover:bg-zinc-900 border-l-2 border-transparent hover:border-brand-red transition-all cursor-pointer group shadow-lg">
                        <div class="flex items-center gap-6">
                           <div class="w-12 h-12 bg-zinc-900 flex items-center justify-center font-black italic text-brand-red border border-zinc-800 group-hover:bg-brand-red group-hover:text-white transition-all transform group-hover:rotate-3">{{ t.description[0] }}</div>
                           <div>
                              <div class="text-[10px] opacity-30 uppercase font-black tracking-widest mb-1">{{ t.type }}</div>
                              <div class="text-xl font-black group-hover:text-brand-red tracking-tight uppercase italic transition-colors">{{ t.description }}</div>
                           </div>
                        </div>
                        <div class="text-right">
                           <div class="text-3xl font-black tracking-tighter italic" :class="t.type === 'INCOME' ? 'text-zinc-500' : 'text-white'">
                              {{ t.type === 'INCOME' ? '-' : '' }}€ {{ t.amount.toFixed(2) }}
                           </div>
                           <div class="text-[10px] uppercase font-black opacity-30">Payer: <span class="text-white">{{ getPayerName(t.payer_id) }}</span></div>
                        </div>
                     </div>
                  </div>
               </div>
            </div>
            <div v-if="!filteredTransactions.length" class="h-64 border-2 border-dashed border-zinc-800 flex items-center justify-center italic text-zinc-700 font-black uppercase tracking-widest">
               Geen transacties gevonden
            </div>
         </div>

         <!-- BALANCE TAB -->
         <div v-if="currentTab === 'BALANCE'" class="grid grid-cols-1 md:grid-cols-2 gap-12 animate-in fade-in slide-in-from-right-4 duration-500">
            <!-- Left: Current State -->
            <div class="space-y-8">
               <div class="bg-industrial-gray p-10 border-l-8 border-brand-red shadow-2xl relative overflow-hidden">
                  <h2 class="text-xs uppercase font-black mb-2 tracking-[0.2em] opacity-40">Huidige Groepsbalans</h2>
                  <div class="text-7xl font-black italic tracking-tighter mb-8">€ {{ totalGroupSpend.toFixed(2) }}</div>
                  <button @click="commitSettlement" 
                          class="w-full bg-brand-red py-6 font-black uppercase italic tracking-widest text-xl hover:bg-white hover:text-black transition-all shadow-[0_0_30px_rgba(227,6,19,0.3)]">
                     Afrekening maken
                  </button>
               </div>

               <div class="bg-industrial-gray p-8 shadow-xl">
                  <h3 class="text-xs uppercase font-black mb-8 tracking-[0.2em] border-b border-zinc-800 pb-2 text-brand-red">Status per persoon</h3>
                  <div class="space-y-6">
                    <div v-for="u in groupMembers" :key="u.id" class="flex items-center justify-between group">
                      <div class="flex items-center gap-4">
                        <img :src="u.avatar_url" class="w-12 h-12 border border-zinc-800 grayscale object-cover" @error="u.avatar_url = null">
                        <span class="text-lg font-black uppercase italic tracking-tight">{{ u.name }}</span>
                      </div>
                      <div class="text-2xl font-black italic tracking-tighter" :class="getBalanceForUser(u.id) >= 0 ? 'text-zinc-400' : 'text-brand-red'">
                         {{ getBalanceForUser(u.id) >= 0 ? '+' : '' }}{{ getBalanceForUser(u.id).toFixed(2) }}
                      </div>
                    </div>
                  </div>
               </div>

               <div v-if="settlementsSuggestions.length > 0" class="bg-black/40 border border-brand-red/20 p-8 shadow-xl">
                  <h3 class="text-xs uppercase text-brand-red font-black mb-6 tracking-[0.2em] italic">Betaalvoorstel</h3>
                  <div v-for="(s, idx) in settlementsSuggestions" :key="idx" class="text-sm font-black uppercase tracking-widest border-l-4 border-brand-red pl-6 py-4 mb-4 bg-zinc-900/50">
                    <span class="text-white">{{ s.from_user }}</span> <span class="text-zinc-600 mx-2 italic text-xs">betaalt aan</span> <span class="text-brand-red">{{ s.to_user }}</span>
                    <div class="text-3xl italic text-white mt-2 tracking-tighter">€ {{ s.amount.toFixed(2) }}</div>
                  </div>
               </div>
            </div>

            <!-- Right: History -->
            <div class="space-y-8">
               <h2 class="text-2xl font-black uppercase italic tracking-tighter border-b border-zinc-800 pb-4">Oude Verrekeningen</h2>
               <div class="space-y-4">
                  <div v-for="s in settlementHistory" :key="s.id" class="bg-industrial-gray/20 border border-zinc-900 p-6 hover:border-brand-red/40 transition-all group">
                     <div class="flex justify-between items-start mb-4">
                        <div>
                           <div class="text-[10px] font-black text-brand-red uppercase mb-1">{{ new Date(s.date).toLocaleDateString('nl-NL') }}</div>
                           <div class="text-lg font-black uppercase italic tracking-tight">{{ s.description }}</div>
                        </div>
                        <div class="text-right">
                           <div class="text-[10px] font-black opacity-30 uppercase">Totaal</div>
                           <div class="text-xl font-black italic">€ {{ s.total_amount.toFixed(2) }}</div>
                        </div>
                     </div>
                     <div class="space-y-1 mt-4 border-t border-zinc-900 pt-4">
                        <div v-for="(res, ridx) in s.results" :key="ridx" class="text-[9px] font-black uppercase tracking-widest text-zinc-600">
                           {{ res.from_user }} ➜ {{ res.to_user }}: <span class="text-zinc-400">€ {{ res.amount.toFixed(2) }}</span>
                        </div>
                     </div>
                  </div>
                  <div v-if="!settlementHistory.length" class="text-center py-20 italic text-zinc-700 font-black uppercase text-xs tracking-widest">Nog geen historie</div>
               </div>
            </div>
         </div>

      </div>
    </div>

    <!-- Modals (Re-using existing logic) -->
    <Transition name="fade">
      <div v-if="isProfileModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/90 backdrop-blur-md" @click="isProfileModalOpen = false"></div>
        <div class="bg-industrial-gray w-full max-w-sm border border-zinc-800 shadow-2xl relative p-12 animate-in fade-in zoom-in duration-300">
           <div class="text-center">
              <div class="w-32 h-32 mx-auto border-2 border-brand-red p-1 bg-black overflow-hidden mb-6">
                 <img v-if="currentUser?.avatar_url" :src="currentUser.avatar_url" class="w-full h-full grayscale object-cover" @error="currentUser.avatar_url = null">
                 <span v-else class="text-4xl font-black text-brand-red flex items-center justify-center h-full">{{ currentUser?.name[0] }}</span>
              </div>
              <h2 class="text-3xl font-black uppercase italic tracking-tighter mb-8">{{ currentUser?.name }}</h2>
              <div class="space-y-4 text-left">
                 <label class="block w-full bg-zinc-900 border border-zinc-800 p-4 text-center cursor-pointer hover:border-brand-red transition-all group">
                    <span class="text-[8px] font-black uppercase tracking-widest opacity-40 group-hover:opacity-100 italic">Foto uploaden</span>
                    <input type="file" @change="handleAvatarUpload" class="hidden" accept="image/*">
                 </label>
                 <input v-model="newEmail" type="email" class="w-full bg-black border border-zinc-800 p-3 font-black text-xs text-white outline-none focus:border-brand-red" placeholder="Email">
                 <input v-model="newAvatarUrl" type="text" class="w-full bg-black border border-zinc-800 p-3 font-black text-xs text-white outline-none focus:border-brand-red" placeholder="Avatar URL">
                 <button @click="updateProfile" class="w-full bg-white text-black py-3 text-[10px] font-black uppercase tracking-widest hover:bg-brand-red hover:text-white transition-all transform active:scale-95 shadow-xl">Profiel Opslaan</button>
                 <button @click="logout" class="w-full border border-zinc-800 py-3 text-[10px] font-black uppercase tracking-widest hover:text-brand-red hover:border-brand-red transition-all">Uitloggen</button>
              </div>
           </div>
        </div>
      </div>
    </Transition>

    <!-- RESTRICTED ACCESS SCREEN - Shows when not authenticated -->
    <Transition name="fade">
      <div v-if="!currentUser && !token" class="fixed inset-0 z-[100] bg-black">
        <div class="min-h-screen flex flex-col items-center justify-center p-4">
          <!-- Animated Background Grid -->
          <div class="absolute inset-0 opacity-5">
            <div class="absolute inset-0" style="background-image: repeating-linear-gradient(0deg, transparent, transparent 50px, #E30613 50px, #E30613 51px), repeating-linear-gradient(90deg, transparent, transparent 50px, #E30613 50px, #E30613 51px);"></div>
          </div>
          
          <!-- Restricted Access Content -->
          <div class="relative z-10 text-center mb-12">
            <div class="w-24 h-24 mx-auto mb-8 border-4 border-brand-red flex items-center justify-center animate-pulse">
              <span class="text-5xl">🔒</span>
            </div>
            <h1 class="text-6xl md:text-8xl font-black uppercase italic tracking-tighter text-brand-red text-shadow-glow mb-4">
              Restricted
            </h1>
            <h2 class="text-2xl md:text-3xl font-black uppercase italic tracking-[0.3em] text-zinc-600">
              Access Denied
            </h2>
            <p class="mt-6 text-zinc-700 font-black uppercase text-xs tracking-widest">
              Authentication required to continue
            </p>
          </div>
          
          <!-- Login Form -->
          <div class="relative z-10 bg-industrial-gray w-full max-w-md border border-zinc-800 shadow-2xl p-10">
            <div class="h-1 bg-brand-red absolute top-0 left-0 right-0 shadow-[0_0_20px_rgba(227,6,19,0.5)]"></div>
            <div class="text-center mb-8">
              <span class="text-brand-red font-black uppercase italic text-2xl tracking-tighter">Better WBW</span>
              <p class="text-[10px] text-zinc-600 font-black uppercase tracking-widest mt-2 italic">Secure Login Portal</p>
            </div>
            <form @submit.prevent="performLogin" class="space-y-5">
              <div class="relative">
                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-600 text-sm">👤</span>
                <input v-model="loginCredentials.username" type="text" 
                       class="w-full bg-black border border-zinc-800 p-4 pl-12 font-black uppercase outline-none focus:border-brand-red italic text-white text-sm" 
                       placeholder="Gebruikersnaam / Email" autocomplete="username">
              </div>
              <div class="relative">
                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-600 text-sm">🔑</span>
                <input v-model="loginCredentials.password" type="password" 
                       class="w-full bg-black border border-zinc-800 p-4 pl-12 font-black uppercase outline-none focus:border-brand-red italic text-white text-sm" 
                       placeholder="Wachtwoord" autocomplete="current-password">
              </div>
              <Transition name="fade">
                <p v-if="loginError" class="text-brand-red text-center font-black uppercase italic text-[10px] bg-brand-red/10 py-2 border border-brand-red/30">
                  ⚠️ {{ loginError }}
                </p>
              </Transition>
              <button type="submit" 
                      class="w-full bg-brand-red py-5 font-black uppercase tracking-[0.3em] hover:bg-white hover:text-black transition-all transform active:scale-95 italic text-lg shadow-[0_0_30px_rgba(227,6,19,0.3)]">
                Authenticate
              </button>
            </form>
            <div class="mt-8 pt-6 border-t border-zinc-800 text-center">
              <p class="text-[8px] text-zinc-600 font-black uppercase tracking-widest italic">Default credentials: wbw2026</p>
            </div>
          </div>
          
          <!-- Footer -->
          <div class="relative z-10 mt-12 text-center">
            <p class="text-[8px] text-zinc-800 font-black uppercase tracking-[0.4em]">
              Protected by JWT · PBKDF2 Encryption
            </p>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="isEditModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/95 backdrop-blur-md" @click="closeEditModal"></div>
        <div class="bg-industrial-gray w-full max-w-2xl border border-zinc-800 shadow-2xl relative animate-in fade-in zoom-in duration-300 overflow-hidden">
          <div class="h-1 bg-brand-red absolute top-0 left-0 right-0 shadow-[0_0_15px_rgba(227,6,19,0.5)]"></div>
          
          <div class="flex border-b border-zinc-800">
             <button v-for="tType in ['EXPENSE', 'INCOME', 'TRANSFER']" :key="tType" @click="selectedTransaction.type = tType" class="flex-1 py-5 font-black uppercase italic text-[10px] tracking-[0.2em] transition-all" :class="selectedTransaction.type === tType ? 'bg-brand-red text-white' : 'hover:bg-zinc-800 text-zinc-600'">{{ tType === 'EXPENSE' ? 'Uitgave' : tType === 'INCOME' ? 'Inkomsten' : 'Transfer' }}</button>
          </div>

          <div class="p-10">
            <div class="flex justify-between items-start mb-10">
              <h2 class="text-4xl font-black uppercase italic tracking-tighter">{{ selectedTransaction.id ? 'Wijzig Post' : 'Nieuwe Post' }}</h2>
              <button @click="closeEditModal" class="text-zinc-500 hover:text-white">X</button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
              <div class="space-y-8">
                <input v-model="selectedTransaction.description" type="text" class="w-full bg-zinc-900 border border-zinc-800 p-4 font-black uppercase outline-none italic text-sm text-white focus:border-brand-red" placeholder="Omschrijving">
                <div class="grid grid-cols-2 gap-6">
                  <input v-model.number="selectedTransaction.amount" type="number" class="w-full bg-zinc-900 border border-zinc-800 p-4 font-black text-3xl tracking-tighter italic outline-none text-white focus:border-brand-red">
                  <select v-model="selectedTransaction.payer_id" class="w-full bg-zinc-900 border border-zinc-800 p-5 font-black uppercase tracking-widest text-[10px] outline-none text-white italic focus:border-brand-red">
                    <option v-for="u in users" :key="u.id" :value="u.id">{{ u.name }}</option>
                  </select>
                </div>
                <div class="border-2 border-dashed border-zinc-800 p-12 text-center hover:border-brand-red hover:bg-brand-red/5 transition-all cursor-pointer relative group">
                  <input type="file" @change="handleReceiptUpload" class="absolute inset-0 opacity-0 cursor-pointer" accept="image/*" />
                  <div class="space-y-2 pointer-events-none">
                     <div class="text-2xl opacity-20 group-hover:opacity-100 group-hover:text-brand-red transition-all">📷</div>
                     <span class="text-[10px] uppercase font-black opacity-30 tracking-widest block italic group-hover:opacity-100">Attach Receipt</span>
                  </div>
                </div>
              </div>
              <div>
                <label class="block text-[10px] uppercase opacity-40 font-black mb-6 tracking-[0.2em] italic">Distribution</label>
                <div class="space-y-3">
                  <div v-for="u in groupMembers" :key="u.id" class="flex items-center justify-between p-4 border border-zinc-800 transition-all" :class="selectedTransaction.splits.some(s => s.user_id === u.id) ? 'bg-zinc-900 border-brand-red/50 shadow-inner' : 'opacity-20'">
                    <div @click="toggleUserInSplit(u.id)" class="flex items-center gap-4 cursor-pointer select-none">
                      <div class="w-1.5 h-4" :class="selectedTransaction.splits.some(s => s.user_id === u.id) ? 'bg-brand-red shadow-[0_0_8px_rgba(227,6,19,0.5)]' : 'bg-zinc-700'"></div>
                      <span class="font-black uppercase text-[11px] italic">{{ u.name }}</span>
                    </div>
                    <div v-if="selectedTransaction.splits.some(s => s.user_id === u.id) && selectedTransaction.type !== 'TRANSFER'" class="flex items-center gap-4">
                      <div class="flex items-center gap-1.5 bg-black p-1">
                        <button @click="decrementWeight(u.id)" class="w-6 h-6 flex items-center justify-center hover:text-brand-red transition-colors font-black text-xs">-</button>
                        <span class="w-5 text-center font-black text-brand-red italic text-sm">{{ selectedTransaction.splits.find(s => s.user_id === u.id).weight }}</span>
                        <button @click="incrementWeight(u.id)" class="w-6 h-6 flex items-center justify-center hover:text-brand-red transition-colors font-black text-xs">+</button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="mt-12 flex gap-4">
              <button v-if="selectedTransaction.id" @click="deleteTransaction" class="border-2 border-zinc-800 text-zinc-600 px-8 py-5 font-black uppercase tracking-[0.2em] hover:text-red-500 hover:border-red-500 transition-all italic text-sm">Delete</button>
              <button @click="saveTransaction" class="flex-1 bg-brand-red text-white py-5 font-black uppercase tracking-[0.3em] italic text-2xl shadow-2xl transform active:scale-[0.98] transition-all">Sync Entry</button>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="isImportModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/90 backdrop-blur-md" @click="isImportModalOpen = false"></div>
        <div class="bg-industrial-gray w-full max-w-4xl border border-zinc-800 shadow-2xl relative animate-in fade-in zoom-in duration-300 overflow-hidden flex flex-col max-h-[90vh]">
          <div class="h-1 bg-brand-red shadow-[0_0_15px_rgba(227,6,19,0.5)]"></div>
          <div class="p-10 flex-1 overflow-y-auto custom-scrollbar">
            <h2 class="text-4xl font-black uppercase italic tracking-tighter mb-10">Bank Ingestion</h2>
            <div v-if="importedTransactions.length === 0" class="space-y-10">
               <div class="flex gap-6">
                  <button v-for="bank in ['ing', 'abn']" :key="bank" @click="importBankType = bank" class="flex-1 py-6 font-black uppercase border-2 transition-all italic text-xs tracking-[0.3em]" :class="importBankType === bank ? 'border-brand-red text-brand-red' : 'border-zinc-800 text-zinc-600'">{{ bank }} Format</button>
               </div>
               <div class="border-2 border-dashed border-zinc-800 p-24 text-center group hover:border-brand-red hover:bg-brand-red/5 transition-all cursor-pointer relative">
                  <input type="file" @change="handleBankImport" class="absolute inset-0 opacity-0 cursor-pointer" accept=".csv" />
                  <div class="space-y-4">
                     <div class="text-4xl opacity-20 group-hover:opacity-100 group-hover:text-brand-red transition-all transform group-hover:scale-110">📁</div>
                     <span class="text-xl font-black uppercase block italic group-hover:text-brand-red transition-colors tracking-widest">Select {{ importBankType.toUpperCase() }} file</span>
                  </div>
               </div>
            </div>
            <div v-else class="space-y-2">
               <div v-for="(t, idx) in importedTransactions" :key="idx" class="flex items-center gap-6 bg-zinc-900/50 p-4 border border-zinc-800 shadow-lg hover:bg-zinc-900 transition-all" :class="!t.selected ? 'opacity-20 grayscale' : ''">
                  <input type="checkbox" v-model="t.selected" class="w-6 h-6 accent-brand-red bg-zinc-800 border-zinc-700 rounded-none cursor-pointer">
                  <div class="flex-1 grid grid-cols-5 gap-6 items-center uppercase font-black italic">
                     <span class="text-[10px] opacity-40">{{ t.date }}</span>
                     <span class="text-sm truncate col-span-3 tracking-tight">{{ t.description }}</span>
                     <span class="text-right text-lg tracking-tighter" :class="t.amount < 0 ? 'text-brand-red' : ''">€ {{ Math.abs(t.amount).toFixed(2) }}</span>
                  </div>
               </div>
            </div>
          </div>
          <div v-if="importedTransactions.length > 0" class="p-10 border-t border-zinc-800 bg-black/50 text-center">
             <button @click="confirmImport" class="w-full bg-brand-red text-white py-6 font-black uppercase tracking-[0.4em] italic text-2xl shadow-[0_0_30px_rgba(227,6,19,0.3)] transform active:scale-95 transition-all">Commit {{ importedTransactions.filter(t => t.selected).length }} Segments</button>
          </div>
        </div>
      </div>
    </Transition>

  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;700;900&display=swap');
.text-shadow-glow { text-shadow: 0 0 15px rgba(227, 6, 19, 0.4); }
.shadow-glow { box-shadow: 0 0 15px rgba(227, 6, 19, 0.4); }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
input[type=number]::-webkit-inner-spin-button, input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
.custom-scrollbar::-webkit-scrollbar { width: 5px; }
.custom-scrollbar::-webkit-scrollbar-track { background: rgba(0,0,0,0.1); }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #E30613; }
</style>
