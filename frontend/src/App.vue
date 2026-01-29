<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useAppStore } from '@/stores/appStore'

// Composables
import { useToast } from '@/composables/useToast'
import { useSelection } from '@/composables/useSelection'

// Config
import { getCategoryLabel } from '@/config/categories'

// Layout Components
import AppHeader from '@/components/layout/AppHeader.vue'

// Feature Components
import LoginView from '@/components/features/auth/LoginView.vue'
import TransactionCard from '@/components/features/transactions/TransactionCard.vue'
import TransactionModal from '@/components/features/transactions/TransactionModal.vue'
import BalanceCard from '@/components/features/balance/BalanceCard.vue'
import SettlementPlan from '@/components/features/balance/SettlementPlan.vue'
import SettlementHistory from '@/components/features/balance/SettlementHistory.vue'
import ProfileModal from '@/components/features/auth/ProfileModal.vue'
import BankImportModal from '@/components/features/transactions/BankImportModal.vue'
import ActivityList from '@/components/features/activities/ActivityList.vue'
import ActivityModal from '@/components/features/activities/ActivityModal.vue'

// Bulk operation components (extracted for DRY)
import BulkActivityModal from '@/components/features/bulk/BulkActivityModal.vue'
import BulkSplitsModal from '@/components/features/bulk/BulkSplitsModal.vue'

const store = useAppStore()

// --- Composables ---
const toast = useToast()
const selection = useSelection()

// --- UI State ---
const currentTab = ref('ACTIVITY')
const searchQuery = ref('')
const selectedCategoryFilter = ref(null)
const showFilterDropdown = ref(false)
const selectedActivityId = ref(null)
const isEditModalOpen = ref(false)
const isImportModalOpen = ref(false)
const isProfileModalOpen = ref(false)
const isActivityModalOpen = ref(false)
const selectedTransaction = ref(null)
const selectedActivity = ref(null)
const settleLoading = ref(false)
const showTrash = ref(false)
const isBulkActivityModalOpen = ref(false)
const isBulkSplitsModalOpen = ref(false)
const loginError = ref('')

// --- Computed ---
const filteredTransactions = computed(() => {
  let result = store.transactions
  
  // Filter by category
  if (selectedCategoryFilter.value) {
    result = result.filter(t => t.category === selectedCategoryFilter.value)
  }
  
  // Filter by search query
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(t => 
      t.description.toLowerCase().includes(q) || 
      store.getUserName(t.payer_id).toLowerCase().includes(q)
    )
  }
  
  return result
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

// --- Methods (using store helpers) ---

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
    time: new Date().toTimeString().slice(0, 5),
    payer_id: store.currentUser?.id, type: 'EXPENSE',
    category: 'overig',
    activity_id: selectedActivityId.value,
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
  if (!confirm('Naar prullenbak verplaatsen?')) return
  try {
    const res = await store.apiFetch(`/transactions/${id}`, { method: 'DELETE' })
    const data = await res.json().catch(() => ({}))
    if (res.ok) {
      toast.show('Verplaatst naar prullenbak')
      await store.fetchData(selectedActivityId.value)
      if (showTrash.value) await store.fetchTrash(selectedActivityId.value)
      isEditModalOpen.value = false
    } else if (res.status === 403) {
      alert(data.error || 'Afgerekende transactie kan niet verwijderd worden.')
    } else {
      alert(data.error || 'Verwijderen mislukt')
    }
  } catch { 
    alert('Verwijderen mislukt') 
  }
}

const handleRestore = async (id) => {
  try {
    const res = await store.apiFetch(`/transactions/${id}/restore`, { method: 'POST' })
    if (res.ok) {
      await store.fetchData(selectedActivityId.value)
      await store.fetchTrash(selectedActivityId.value)
    } else {
      const data = await res.json().catch(() => ({}))
      alert(data.error || 'Herstellen mislukt')
    }
  } catch { alert('Herstellen mislukt') }
}

const handleDeletePermanent = async (id) => {
  if (!confirm('Definitief verwijderen? Dit kan niet ongedaan.')) return
  try {
    const res = await store.apiFetch(`/transactions/${id}/permanent`, { method: 'DELETE' })
    if (res.ok) {
      await store.fetchData(selectedActivityId.value)
      await store.fetchTrash(selectedActivityId.value)
    } else {
      const data = await res.json().catch(() => ({}))
      alert(data.error || 'Definitief verwijderen mislukt')
    }
  } catch { alert('Definitief verwijderen mislukt') }
}

function onShowTrash(show) {
  showTrash.value = show
  if (show) store.fetchTrash(selectedActivityId.value)
  if (!show) selection.clear()
}

function selectAllVisible() {
  const ids = groupedTransactions.value.flatMap(g => g.txs.map(t => t.id))
  selection.selectAll(ids)
}

// Bulk activity assignment handler
async function handleBulkActivityApply(activityId) {
  const ids = selection.getSelectedArray()
  if (!ids.length) return
  try {
    const res = await store.apiFetch('/transactions/bulk', {
      method: 'PATCH',
      body: JSON.stringify({ transaction_ids: ids, activity_id: activityId })
    })
    if (res.ok) {
      selection.clear()
      isBulkActivityModalOpen.value = false
      await store.fetchData(selectedActivityId.value)
    } else {
      const data = await res.json().catch(() => ({}))
      alert(data.error || 'Bulk update mislukt')
    }
  } catch { alert('Bulk update mislukt') }
}

// Bulk splits assignment handler
async function handleBulkSplitsApply(splits) {
  const ids = selection.getSelectedArray()
  if (!ids.length || !splits.length) return
  try {
    const res = await store.apiFetch('/transactions/bulk', {
      method: 'PATCH',
      body: JSON.stringify({ transaction_ids: ids, splits })
    })
    if (res.ok) {
      selection.clear()
      isBulkSplitsModalOpen.value = false
      await store.fetchData(selectedActivityId.value)
    } else {
      const data = await res.json().catch(() => ({}))
      alert(data.error || 'Bulk update mislukt')
    }
  } catch { alert('Bulk update mislukt') }
}

async function handleSettlementRestore(sessionId) {
  try {
    const res = await store.apiFetch(`/settlements/${sessionId}/restore`, { method: 'POST' })
    if (res.ok) {
      await store.fetchData(selectedActivityId.value)
    } else {
      const data = await res.json().catch(() => ({}))
      alert(data.error || 'Herstellen mislukt')
    }
  } catch { alert('Herstellen mislukt') }
}

async function handleSettlementDeletePermanent(sessionId) {
  if (!confirm('Definitief verwijderen? Dit kan niet ongedaan.')) return
  try {
    const res = await store.apiFetch(`/settlements/${sessionId}/permanent`, { method: 'DELETE' })
    if (res.ok) {
      await store.fetchData(selectedActivityId.value)
    } else {
      const data = await res.json().catch(() => ({}))
      alert(data.error || 'Definitief verwijderen mislukt')
    }
  } catch { alert('Definitief verwijderen mislukt') }
}

async function handleSettlementDelete(sessionId) {
  if (!confirm('Afrekening ongedaan maken? Transacties komen terug in de lijst.')) return
  try {
    const res = await store.apiFetch(`/settlements/${sessionId}`, { method: 'DELETE' })
    if (res.ok) {
      toast.show('Afrekening ongedaan gemaakt')
      await store.fetchData(selectedActivityId.value)
    } else {
      const data = await res.json().catch(() => ({}))
      alert(data.error || 'Ongedaan maken mislukt')
    }
  } catch { alert('Ongedaan maken mislukt') }
}

const handleBulkDelete = async () => {
  if (!confirm(`${selection.count.value} transactie(s) verplaatsen naar prullenbak?`)) return
  try {
    let deleted = 0
    for (const id of selection.getSelectedArray()) {
      const res = await store.apiFetch(`/transactions/${id}`, { method: 'DELETE' })
      if (res.ok) deleted++
    }
    await store.fetchData(selectedActivityId.value)
    selection.clear()
    toast.show(`${deleted} transactie(s) naar prullenbak`)
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
        category: null, // Let backend auto-classify
        activity_id: selectedActivityId.value,
        splits: store.groupMembers.map(u => ({ user_id: u.id, weight: 1 }))
      }
      const res = await store.apiFetch('/transactions', { method: 'POST', body: JSON.stringify(payload) })
      if (res.ok) ok++
    }
    await store.fetchData(selectedActivityId.value)
    isImportModalOpen.value = false
    alert(`${ok} transactie(s) geïmporteerd.`)
  } catch (e) {
    alert('Import mislukt: ' + (e.message || 'onbekend'))
  }
}

const selectActivity = (id) => {
  selectedActivityId.value = id
  store.fetchData(id)
}

const openActivityModal = (activity = null) => {
  selectedActivity.value = activity
  isActivityModalOpen.value = true
}

const handleActivitySave = async (data) => {
  try {
    const isNew = !selectedActivity.value
    const endpoint = isNew ? '/activities' : `/activities/${selectedActivity.value.id}`
    const method = isNew ? 'POST' : 'PUT'
    const res = await store.apiFetch(endpoint, { method, body: JSON.stringify(data) })
    if (res.ok) {
      await store.fetchData(selectedActivityId.value)
      isActivityModalOpen.value = false
      selectedActivity.value = null
    }
  } catch { alert('Activiteit opslaan mislukt') }
}

// Use store helper for activity info
const getActivityName = (id) => store.getActivityInfo(id)

const selectedActivityLabel = () => {
  const info = store.getActivityInfo(selectedActivityId.value)
  return info ? info.name : null
}

const handleSettle = async () => {
  settleLoading.value = true
  try {
    const body = selectedActivityId.value ? { activity_id: selectedActivityId.value } : {}
    const res = await store.apiFetch('/settlements/commit', { method: 'POST', body: JSON.stringify(body) })
    if (res.ok) {
      await store.fetchData(selectedActivityId.value)
    } else {
      const data = await res.json().catch(() => ({}))
      alert(data.message || 'Afrekenen mislukt')
    }
  } catch (e) {
    alert('Afrekenen mislukt: ' + (e.message || 'onbekend'))
  } finally {
    settleLoading.value = false
  }
}

watch(selectedActivityId, () => {
  store.fetchData(selectedActivityId.value)
  if (showTrash.value) store.fetchTrash(selectedActivityId.value)
})

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
           <div class="pt-4">
             <ActivityList 
               :activities="store.activities"
               :selected-id="selectedActivityId"
               @select="selectActivity"
               @new="openActivityModal()"
             />
           </div>
        </nav>

        <div class="lg:col-span-10">
           <div v-if="currentTab === 'ACTIVITY'" class="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500 text-white">
              <div class="flex items-center gap-4 flex-wrap">
                 <div class="flex border border-zinc-800 rounded overflow-hidden">
                    <button type="button" :class="!showTrash ? 'bg-brand-red text-white' : 'bg-industrial-gray text-zinc-500 hover:text-white'" class="px-6 py-3 font-black uppercase italic text-[10px] tracking-widest transition-all" @click="onShowTrash(false)">Transacties</button>
                    <button type="button" :class="showTrash ? 'bg-brand-red text-white' : 'bg-industrial-gray text-zinc-500 hover:text-white'" class="px-6 py-3 font-black uppercase italic text-[10px] tracking-widest transition-all" @click="onShowTrash(true)">Prullenbak</button>
                 </div>
                 <div v-if="!showTrash" class="relative max-w-xl flex-1 min-w-[200px]">
                    <span class="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-700">🔍</span>
                    <input v-model="searchQuery" type="text" class="w-full bg-industrial-gray border border-zinc-800 p-4 pl-12 pr-12 font-black uppercase italic text-sm outline-none focus:border-brand-red transition-all text-white" placeholder="Zoek transactie of persoon...">
                 </div>
                 <!-- Category Filter -->
                 <div v-if="!showTrash" class="relative">
                    <button @click="showFilterDropdown = !showFilterDropdown"
                            class="bg-industrial-gray border border-zinc-800 p-4 font-black uppercase italic text-sm transition-all hover:border-brand-red flex items-center gap-2"
                            :class="selectedCategoryFilter ? 'border-brand-red text-brand-red' : 'text-zinc-500'">
                       <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                         <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"></path>
                       </svg>
                       <span class="hidden md:inline">{{ selectedCategoryFilter ? getCategoryLabel(selectedCategoryFilter) : 'Filter' }}</span>
                    </button>
                    <!-- Filter Dropdown -->
                    <Transition name="fade">
                      <div v-if="showFilterDropdown">
                         <div class="fixed inset-0 z-40" @click="showFilterDropdown = false"></div>
                         <div class="absolute top-full right-0 mt-2 bg-industrial-gray border border-zinc-800 shadow-xl z-50 min-w-[200px]">
                           <button @click="selectedCategoryFilter = null; showFilterDropdown = false"
                                   class="w-full text-left px-4 py-3 font-black uppercase italic text-xs transition-all hover:bg-zinc-900"
                                   :class="!selectedCategoryFilter ? 'text-brand-red bg-zinc-900' : 'text-zinc-400'">
                             Alle categorieën
                           </button>
                           <button v-for="cat in store.categories" :key="cat.key"
                                   @click="selectedCategoryFilter = cat.key; showFilterDropdown = false"
                                   class="w-full text-left px-4 py-3 font-black uppercase italic text-xs transition-all hover:bg-zinc-900"
                                   :class="selectedCategoryFilter === cat.key ? 'text-brand-red bg-zinc-900' : 'text-zinc-400'">
                             {{ cat.label }}
                           </button>
                         </div>
                      </div>
                    </Transition>
                 </div>
              </div>
              <template v-if="!showTrash">
                 <div v-if="selection.hasSelection.value" class="flex flex-wrap items-center gap-4 p-4 bg-zinc-900/80 border border-zinc-800 rounded">
                    <span class="font-black uppercase italic text-brand-red">{{ selection.count.value }} geselecteerd</span>
                    <span class="text-zinc-600 text-[10px] font-medium uppercase tracking-wider flex items-center gap-1">
                      <button type="button" class="hover:text-brand-red transition-colors" @click="selectAllVisible">Alles aanvinken</button>
                      <span class="opacity-50">·</span>
                      <button type="button" class="hover:text-brand-red transition-colors" @click="selection.clear">Selectie leegmaken</button>
                    </span>
                    <button type="button" class="btn-action" @click="isBulkActivityModalOpen = true">Koppel aan activiteit</button>
                    <button type="button" class="btn-action" @click="isBulkSplitsModalOpen = true">Zelfde personen toepassen</button>
                    <button type="button" class="px-4 py-2 text-[10px] font-black uppercase bg-brand-red/80 text-white hover:bg-brand-red transition-all" @click="handleBulkDelete">Verwijderen</button>
                 </div>
                 <div v-for="group in groupedTransactions" :key="group.label" class="space-y-4">
                    <h3 class="text-sm font-black uppercase tracking-[0.2em] text-white italic border-b border-zinc-800 pb-2 mb-4">{{ group.label }}</h3>
                    <div class="space-y-2">
                       <TransactionCard v-for="t in group.txs" :key="t.id" 
                                       :transaction="t" 
                                       :payer-name="store.getUserName(t.payer_id)"
                                       :activity="getActivityName(t.activity_id)"
                                       :selectable="true"
                                       :selected="selection.isSelected(t.id)"
                                       @click="openTransaction(t)"
                                       @toggle-select="selection.toggle" />
                    </div>
                 </div>
              </template>
              <template v-else>
                 <div class="bg-industrial-gray border border-zinc-800 p-6">
                    <h3 class="text-xs uppercase font-black mb-4 tracking-[0.2em] border-b border-zinc-800 pb-2 text-brand-red">Prullenbak</h3>
                    <p v-if="!store.deletedTransactions.length" class="text-zinc-500 text-sm italic">Geen verwijderde transacties.</p>
                    <div v-else class="space-y-2">
                       <div v-for="t in store.deletedTransactions" :key="t.id" class="flex items-center justify-between gap-4 p-4 bg-zinc-900/50 border border-zinc-800 rounded">
                          <div>
                             <span class="font-black uppercase italic text-white">{{ t.description }}</span>
                             <span class="text-zinc-500 text-sm ml-2">€ {{ (t.amount || 0).toFixed(2) }}</span>
                             <span class="text-zinc-500 text-[10px] block mt-1">{{ store.getUserName(t.payer_id) }} · {{ t.deleted_at ? new Date(t.deleted_at).toLocaleDateString('nl-NL') : '' }}</span>
                          </div>
                          <div class="flex gap-2 shrink-0">
                             <button type="button" class="px-4 py-2 text-[10px] font-black uppercase bg-zinc-700 text-white hover:bg-zinc-600 transition-all" @click="handleRestore(t.id)">Herstel</button>
                             <button type="button" class="px-4 py-2 text-[10px] font-black uppercase bg-brand-red/80 text-white hover:bg-brand-red transition-all" @click="handleDeletePermanent(t.id)">Definitief verwijderen</button>
                          </div>
                       </div>
                    </div>
                 </div>
              </template>
              <div v-if="toast.isVisible.value" class="fixed bottom-8 left-1/2 -translate-x-1/2 bg-brand-red text-white px-6 py-3 font-black uppercase italic text-sm shadow-xl z-50 animate-in fade-in duration-300">
                 {{ toast.message.value }}
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
                        <div class="text-2xl font-black italic tracking-tighter" :class="store.getBalanceForUser(u.id) >= 0 ? 'text-zinc-400' : 'text-brand-red'">
                           {{ store.getBalanceForUser(u.id) >= 0 ? '+' : '' }}{{ store.getBalanceForUser(u.id).toFixed(2) }}
                        </div>
                      </div>
                    </div>
                 </div>
                 <SettlementPlan 
                   :settlements="store.settlementsSuggestions" 
                   :activity-name="selectedActivityLabel()"
                   :loading="settleLoading"
                   @settle="handleSettle"
                 />
                 <SettlementHistory 
                   :history="store.settlementHistory"
                   @restore="handleSettlementRestore"
                   @delete="handleSettlementDelete"
                   @delete-permanent="handleSettlementDeletePermanent" />
              </div>
           </div>
        </div>
      </div>

      <TransactionModal :is-open="isEditModalOpen" 
                        :transaction="selectedTransaction"
                        :users="store.users"
                        :group-members="store.groupMembers"
                        :activities="store.activities"
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

      <ActivityModal :is-open="isActivityModalOpen"
                     :activity="selectedActivity"
                     @close="isActivityModalOpen = false; selectedActivity = null"
                     @save="handleActivitySave" />

      <!-- Bulk Operation Modals (extracted components) -->
      <BulkActivityModal 
        :is-open="isBulkActivityModalOpen"
        :activities="store.activities"
        :initial-activity-id="selectedActivityId"
        @close="isBulkActivityModalOpen = false"
        @apply="handleBulkActivityApply"
      />

      <BulkSplitsModal 
        :is-open="isBulkSplitsModalOpen"
        :group-members="store.groupMembers"
        @close="isBulkSplitsModalOpen = false"
        @apply="handleBulkSplitsApply"
      />
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
