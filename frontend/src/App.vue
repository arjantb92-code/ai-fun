<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAppStore } from '@/stores/appStore'

// Layout Components
import AppHeader from '@/components/layout/AppHeader.vue'

// Feature Components
import LoginView from '@/components/features/auth/LoginView.vue'
import TransactionCard from '@/components/features/transactions/TransactionCard.vue'
import TransactionModal from '@/components/features/transactions/TransactionModal.vue'
import BalanceCard from '@/components/features/balance/BalanceCard.vue'
import SettlementPlan from '@/components/features/balance/SettlementPlan.vue'
import ProfileModal from '@/components/features/auth/ProfileModal.vue'
import BankImportModal from '@/components/features/transactions/BankImportModal.vue'

const store = useAppStore()

// --- UI State ---
const currentTab = ref('ACTIVITY')
const searchQuery = ref('')
const isEditModalOpen = ref(false)
const isImportModalOpen = ref(false)
const isProfileModalOpen = ref(false)
const selectedTransaction = ref(null)
const loginError = ref('')
const newAvatarUrl = ref('')
const newEmail = ref('')

// --- Computed ---
const filteredTransactions = computed(() => {
  if (!searchQuery.value) return store.transactions
  const q = searchQuery.value.toLowerCase()
  return store.transactions.filter(t => 
    t.description.toLowerCase().includes(q) || 
    getPayerName(t.payer_id).toLowerCase().includes(q)
  )
})

const groupedTransactions = computed(() => {
  const groups = []
  const groupMap = {}
  filteredTransactions.value.forEach(t => {
    const date = new Date(t.date)
    const label = date.toLocaleDateString('nl-NL', { day: 'numeric', month: 'long', year: 'numeric' })
    if (!groupMap[label]) {
      groupMap[label] = []
      groups.push({ label, txs: groupMap[label] })
    }
    groupMap[label].push(t)
  })
  return groups
})

// --- Methods ---
const getPayerName = (id) => store.users.find(u => u.id === id)?.name || 'Onbekend'
const getBalanceForUser = (userId) => store.balances.find(b => b.user_id === userId)?.balance || 0

const handleLogin = async (credentials) => {
  loginError.value = ''
  try {
    const res = await fetch('http://localhost:5001/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    })
    const data = await res.json()
    if (res.ok) {
      store.login(data)
      newAvatarUrl.value = data.user.avatar_url
      newEmail.value = data.user.email
    } else {
      loginError.value = data.message
    }
  } catch {
    loginError.value = 'Server Offline'
  }
}

const openTransaction = (t) => {
  selectedTransaction.value = t
  isEditModalOpen.value = true
}

const createNewEntry = () => {
  selectedTransaction.value = { 
    id: null, description: 'Nieuwe uitgave', amount: 0, 
    date: new Date().toISOString().split('T')[0], 
    payer_id: store.currentUser?.id, type: 'EXPENSE',
    splits: store.groupMembers.map(u => ({ user_id: u.id, weight: 1 })) 
  }
  isEditModalOpen.value = true
}

const handleSave = async (tx) => {
  const isNew = !tx.id
  try {
    const res = await store.apiFetch(isNew ? '/transactions' : `/transactions/${tx.id}`, {
      method: isNew ? 'POST' : 'PUT',
      body: JSON.stringify(tx)
    })
    if (res.ok) {
      await store.fetchData()
      isEditModalOpen.value = false
    }
  } catch { alert('Opslaan mislukt') }
}

const handleDelete = async (id) => {
  if (!confirm('Verwijderen?')) return
  try {
    const res = await store.apiFetch(`/transactions/${id}`, { method: 'DELETE' })
    if (res.ok) {
      await store.fetchData()
      isEditModalOpen.value = false
    }
  } catch { alert('Verwijderen mislukt') }
}

const handleReceiptUpload = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  try {
    const res = await fetch('http://localhost:5001/ocr/process', { 
      method: 'POST', 
      headers: { 'Authorization': `Bearer ${store.token}` }, 
      body: formData 
    })
    const result = await res.json()
    if (res.ok) {
       selectedTransaction.value.amount = result.data.extracted_data.total || selectedTransaction.value.amount
       selectedTransaction.value.description = result.data.extracted_data.merchant !== 'Unknown Merchant' ? result.data.extracted_data.merchant : selectedTransaction.value.description
    }
  } catch { alert('OCR mislukt') }
}

const handleProfileSave = async ({ name, email }) => {
  try {
    const res = await store.apiFetch('/users/profile', { method: 'PUT', body: JSON.stringify({ name, email }) })
    if (res.ok) {
      const data = await res.json()
      store.currentUser = data.user
      localStorage.setItem('wbw_user', JSON.stringify(data.user))
      isProfileModalOpen.value = false
    }
  } catch { alert('Profiel opslaan mislukt') }
}

const handleBankImported = async (rows) => {
  if (!rows?.length || !store.currentUser || !store.groupMembers?.length) return
  try {
    let ok = 0
    for (const r of rows) {
      const payload = {
        description: r.description || 'Bankimport',
        amount: Math.abs(Number(r.amount)),
        date: r.date || new Date().toISOString().split('T')[0],
        payer_id: store.currentUser.id,
        type: 'EXPENSE',
        splits: store.groupMembers.map(u => ({ user_id: u.id, weight: 1 }))
      }
      const res = await store.apiFetch('/transactions', { method: 'POST', body: JSON.stringify(payload) })
      if (res.ok) ok++
    }
    await store.fetchData()
    isImportModalOpen.value = false
    alert(`${ok} transactie(s) geïmporteerd.`)
  } catch (e) {
    alert('Import mislukt: ' + (e.message || 'onbekend'))
  }
}

onMounted(() => store.fetchData())
</script>

<template>
  <div class="min-h-screen bg-trainmore-dark text-white font-industrial p-4 md:p-8 flex flex-col">
    <LoginView v-if="!store.isAuthenticated" :error="loginError" @login="handleLogin" />
    
       <template v-else>
      <div v-if="store.backendStatus === 'Offline'" class="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50">
        <div class="bg-red-700 text-white p-8 rounded-lg shadow-2xl text-center">
          <h2 class="text-2xl font-bold mb-4">Verbinding Verbroken!</h2>
          <p class="mb-4">De backend server is niet bereikbaar op <span class="font-mono bg-black/30 p-1 rounded">http://localhost:5001</span>.</p>
          <p>Controleer of de server draait en probeer het opnieuw.</p>
        </div>
      </div>
      <AppHeader @open-profile="isProfileModalOpen = true">
        <template #actions>
          <div class="flex gap-4 w-full md:w-auto text-white">
            <button @click="isImportModalOpen = true" class="bg-white text-black px-8 py-3 font-bold uppercase hover:bg-brand-red hover:text-white transition-all transform active:scale-95 italic text-sm shadow-xl">Bank Import</button>
            <button @click="createNewEntry" class="border-2 border-brand-red text-brand-red px-8 py-3 font-bold uppercase hover:bg-brand-red hover:text-white transition-all transform active:scale-95 italic text-sm">Nieuwe Post</button>
          </div>
        </template>
      </AppHeader>

      <div class="flex-1 max-w-[1600px] mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-8">
        <nav class="lg:col-span-2 space-y-2 shrink-0">
           <button @click="currentTab = 'ACTIVITY'" 
                   class="w-full text-left px-6 py-4 font-black uppercase italic tracking-widest text-sm transition-all border-r-4 text-white"
                   :class="currentTab === 'ACTIVITY' ? 'bg-industrial-gray border-brand-red' : 'border-transparent text-zinc-600 hover:text-zinc-400'">
              Activiteit
           </button>
           <button @click="currentTab = 'BALANCE'" 
                   class="w-full text-left px-6 py-4 font-black uppercase italic tracking-widest text-sm transition-all border-r-4 text-white"
                   :class="currentTab === 'BALANCE' ? 'bg-industrial-gray border-brand-red' : 'border-transparent text-zinc-600 hover:text-zinc-400'">
              Balans
           </button>
        </nav>

        <div class="lg:col-span-10">
           <div v-if="currentTab === 'ACTIVITY'" class="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500 text-white">
              <div class="relative max-w-xl">
                 <span class="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-700">🔍</span>
                 <input v-model="searchQuery" type="text" class="w-full bg-industrial-gray border border-zinc-800 p-4 pl-12 font-black uppercase italic text-sm outline-none focus:border-brand-red transition-all text-white" placeholder="Zoek transactie of persoon...">
              </div>
              <div v-for="group in groupedTransactions" :key="group.label" class="space-y-4">
                 <h3 class="text-sm font-black uppercase tracking-[0.2em] text-white italic border-b border-zinc-800 pb-2 mb-4">{{ group.label }}</h3>
                 <div class="space-y-2">
                    <TransactionCard v-for="t in group.txs" :key="t.id" 
                                    :transaction="t" 
                                    :payer-name="getPayerName(t.payer_id)"
                                    @click="openTransaction(t)" />
                 </div>
              </div>
           </div>

           <div v-if="currentTab === 'BALANCE'" class="grid grid-cols-1 md:grid-cols-2 gap-12 animate-in fade-in slide-in-from-right-4 duration-500 text-white">
              <div class="space-y-8">
                 <BalanceCard :balance="store.totalGroupSpend" label="Huidige Groepsbalans" />
                 <div class="bg-industrial-gray p-8 shadow-xl">
                    <h3 class="text-xs uppercase font-black mb-8 tracking-[0.2em] border-b border-zinc-800 pb-2 text-brand-red">Status per persoon</h3>
                    <div class="space-y-6">
                      <div v-for="u in store.groupMembers" :key="u.id" class="flex items-center justify-between group">
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
                 <SettlementPlan :settlements="store.settlementsSuggestions" />
              </div>
           </div>
        </div>
      </div>

      <TransactionModal :is-open="isEditModalOpen" 
                        :transaction="selectedTransaction"
                        :users="store.users"
                        :group-members="store.groupMembers"
                        @close="isEditModalOpen = false"
                        @save="handleSave"
                        @delete="handleDelete"
                        @upload-receipt="handleReceiptUpload" />

      <ProfileModal :is-open="isProfileModalOpen"
                   :user="store.currentUser"
                   @close="isProfileModalOpen = false"
                   @save="handleProfileSave" />

      <BankImportModal :is-open="isImportModalOpen"
                       @close="isImportModalOpen = false"
                       @imported="handleBankImported" />
    </template>
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
