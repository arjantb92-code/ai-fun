<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useAppStore } from '@/stores/appStore'
import type { 
  Transaction, 
  TransactionSplit, 
  LoginCredentials, 
  ActivityFormData,
  ActivityDisplay,
  BankImportRow,
  TabType,
  CategoryKey
} from '@/types'

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
import ActivitySelector from '@/components/features/activities/ActivitySelector.vue'

const store = useAppStore()

// --- UI State ---
const currentTab = ref<TabType>('ACTIVITY')
const searchQuery = ref('')
const selectedCategoryFilter = ref<CategoryKey | null>(null)
const showFilterDropdown = ref(false)
const selectedActivityId = ref<number | null>(null)
const isEditModalOpen = ref(false)
const isImportModalOpen = ref(false)
const isProfileModalOpen = ref(false)
const isActivityModalOpen = ref(false)
const selectedTransaction = ref<Transaction | null>(null)
const selectedActivity = ref<import('@/types').Activity | null>(null)
const settleLoading = ref(false)
const showTrash = ref(false)
const toastMessage = ref('')
const selectedTransactionIds = ref<Set<number>>(new Set())
const isBulkActivityModalOpen = ref(false)
const isBulkSplitsModalOpen = ref(false)
const bulkChosenActivityId = ref<number | null>(null)
const bulkSplits = ref<TransactionSplit[]>([])
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
      getPayerName(t.payer_id).toLowerCase().includes(q)
    )
  }
  
  return result
})

const getCategoryLabel = (key: CategoryKey | null): string => {
  if (!key) return 'Overig'
  return store.categories.find(c => c.key === key)?.label || 'Overig'
}

const groupedTransactions = computed(() => {
  interface TransactionGroup {
    label: string
    txs: Transaction[]
  }
  const groups: TransactionGroup[] = []
  const groupMap: Record<string, Transaction[]> = {}
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
const getPayerName = (id: number): string => store.users.find(u => u.id === id)?.name || 'Onbekend'
const getBalanceForUser = (userId: number): number => store.balances.find(b => b.user_id === userId)?.balance || 0

const handleLogin = async (credentials: LoginCredentials): Promise<void> => {
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
    } else {
      loginError.value = data.message
    }
  } catch {
    loginError.value = 'Server Offline'
  }
}

const openTransaction = (t: Transaction): void => {
  selectedTransaction.value = t
  isEditModalOpen.value = true
}

const createNewEntry = (): void => {
  const dateStr = new Date().toISOString().split('T')[0]
  const timeStr = new Date().toTimeString().slice(0, 5)
  selectedTransaction.value = { 
    id: null, 
    description: 'Nieuwe uitgave', 
    amount: 0, 
    date: dateStr ?? '', 
    time: timeStr,
    payer_id: store.currentUser?.id || 0, 
    type: 'EXPENSE',
    category: 'overig',
    activity_id: selectedActivityId.value,
    splits: store.groupMembers.map(u => ({ user_id: u.id, weight: 1 })) 
  }
  isEditModalOpen.value = true
}

const handleSave = async (tx: Transaction): Promise<void> => {
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

const handleDelete = async (id: number): Promise<void> => {
  if (!confirm('Naar prullenbak verplaatsen?')) return
  try {
    const res = await store.apiFetch(`/transactions/${id}`, { method: 'DELETE' })
    const data = await res.json().catch(() => ({})) as { error?: string }
    if (res.ok) {
      toastMessage.value = 'Verplaatst naar prullenbak'
      setTimeout(() => { toastMessage.value = '' }, 2500)
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

const handleRestore = async (id: number): Promise<void> => {
  try {
    const res = await store.apiFetch(`/transactions/${id}/restore`, { method: 'POST' })
    if (res.ok) {
      await store.fetchData(selectedActivityId.value)
      await store.fetchTrash(selectedActivityId.value)
    } else {
      const data = await res.json().catch(() => ({})) as { error?: string }
      alert(data.error || 'Herstellen mislukt')
    }
  } catch { alert('Herstellen mislukt') }
}

const handleDeletePermanent = async (id: number): Promise<void> => {
  if (!confirm('Definitief verwijderen? Dit kan niet ongedaan.')) return
  try {
    const res = await store.apiFetch(`/transactions/${id}/permanent`, { method: 'DELETE' })
    if (res.ok) {
      await store.fetchData(selectedActivityId.value)
      await store.fetchTrash(selectedActivityId.value)
    } else {
      const data = await res.json().catch(() => ({})) as { error?: string }
      alert(data.error || 'Definitief verwijderen mislukt')
    }
  } catch { alert('Definitief verwijderen mislukt') }
}

function onShowTrash(show: boolean): void {
  showTrash.value = show
  if (show) store.fetchTrash(selectedActivityId.value)
  if (!show) clearSelection()
}

function toggleSelect(id: number): void {
  const s = new Set(selectedTransactionIds.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  selectedTransactionIds.value = s
}

function clearSelection(): void {
  selectedTransactionIds.value = new Set()
}

function selectAllVisible(): void {
  const ids = groupedTransactions.value.flatMap(g => g.txs.map(t => t.id).filter((id): id is number => id !== null))
  selectedTransactionIds.value = new Set(ids)
}

function openBulkActivityModal(): void {
  bulkChosenActivityId.value = selectedActivityId.value
  isBulkActivityModalOpen.value = true
}

async function handleBulkActivityApply(): Promise<void> {
  const ids = Array.from(selectedTransactionIds.value)
  if (!ids.length) return
  try {
    const res = await store.apiFetch('/transactions/bulk', {
      method: 'PATCH',
      body: JSON.stringify({ transaction_ids: ids, activity_id: bulkChosenActivityId.value })
    })
    if (res.ok) {
      clearSelection()
      isBulkActivityModalOpen.value = false
      await store.fetchData(selectedActivityId.value)
    } else {
      const data = await res.json().catch(() => ({})) as { error?: string }
      alert(data.error || 'Bulk update mislukt')
    }
  } catch { alert('Bulk update mislukt') }
}

function openBulkSplitsModal(): void {
  bulkSplits.value = (store.groupMembers || []).map(u => ({ user_id: u.id, weight: 1 }))
  isBulkSplitsModalOpen.value = true
}

function toggleUserInBulkSplits(userId: number): void {
  const idx = bulkSplits.value.findIndex(s => s.user_id === userId)
  if (idx !== -1) bulkSplits.value.splice(idx, 1)
  else bulkSplits.value.push({ user_id: userId, weight: 1 })
  bulkSplits.value = [...bulkSplits.value]
}

function incrementBulkWeight(userId: number): void {
  const s = bulkSplits.value.find(s => s.user_id === userId)
  if (s) s.weight++
  bulkSplits.value = [...bulkSplits.value]
}

function decrementBulkWeight(userId: number): void {
  const s = bulkSplits.value.find(s => s.user_id === userId)
  if (s && s.weight > 1) s.weight--
  bulkSplits.value = [...bulkSplits.value]
}

async function handleBulkSplitsApply(): Promise<void> {
  const ids = Array.from(selectedTransactionIds.value)
  if (!ids.length || !bulkSplits.value.length) return
  try {
    const res = await store.apiFetch('/transactions/bulk', {
      method: 'PATCH',
      body: JSON.stringify({ transaction_ids: ids, splits: bulkSplits.value })
    })
    if (res.ok) {
      clearSelection()
      isBulkSplitsModalOpen.value = false
      await store.fetchData(selectedActivityId.value)
    } else {
      const data = await res.json().catch(() => ({})) as { error?: string }
      alert(data.error || 'Bulk update mislukt')
    }
  } catch { alert('Bulk update mislukt') }
}

async function handleSettlementRestore(sessionId: number): Promise<void> {
  try {
    const res = await store.apiFetch(`/settlements/${sessionId}/restore`, { method: 'POST' })
    if (res.ok) {
      await store.fetchData(selectedActivityId.value)
    } else {
      const data = await res.json().catch(() => ({})) as { error?: string }
      alert(data.error || 'Herstellen mislukt')
    }
  } catch { alert('Herstellen mislukt') }
}

async function handleSettlementDeletePermanent(sessionId: number): Promise<void> {
  if (!confirm('Definitief verwijderen? Dit kan niet ongedaan.')) return
  try {
    const res = await store.apiFetch(`/settlements/${sessionId}/permanent`, { method: 'DELETE' })
    if (res.ok) {
      await store.fetchData(selectedActivityId.value)
    } else {
      const data = await res.json().catch(() => ({})) as { error?: string }
      alert(data.error || 'Definitief verwijderen mislukt')
    }
  } catch { alert('Definitief verwijderen mislukt') }
}

async function handleSettlementDelete(sessionId: number): Promise<void> {
  if (!confirm('Afrekening ongedaan maken? Transacties komen terug in de lijst.')) return
  try {
    const res = await store.apiFetch(`/settlements/${sessionId}`, { method: 'DELETE' })
    if (res.ok) {
      toastMessage.value = 'Afrekening ongedaan gemaakt'
      setTimeout(() => { toastMessage.value = '' }, 2500)
      await store.fetchData(selectedActivityId.value)
    } else {
      const data = await res.json().catch(() => ({})) as { error?: string }
      alert(data.error || 'Ongedaan maken mislukt')
    }
  } catch { alert('Ongedaan maken mislukt') }
}

const handleBulkDelete = async (): Promise<void> => {
  if (!confirm(`${selectedTransactionIds.value.size} transactie(s) verplaatsen naar prullenbak?`)) return
  try {
    let deleted = 0
    for (const id of selectedTransactionIds.value) {
      const res = await store.apiFetch(`/transactions/${id}`, { method: 'DELETE' })
      if (res.ok) deleted++
    }
    await store.fetchData(selectedActivityId.value)
    clearSelection()
    toastMessage.value = `${deleted} transactie(s) naar prullenbak`
    setTimeout(() => { toastMessage.value = '' }, 2500)
  } catch { alert('Verwijderen mislukt') }
}

const handleReceiptUpload = async (file: File): Promise<void> => {
  const formData = new FormData()
  formData.append('file', file)
  try {
    const res = await fetch('http://localhost:5001/ocr/process', { 
      method: 'POST', 
      headers: { 'Authorization': `Bearer ${store.token}` }, 
      body: formData 
    })
    const result = await res.json() as { data?: { extracted_data?: { total?: number; merchant?: string } } }
    if (res.ok && selectedTransaction.value) {
       selectedTransaction.value.amount = result.data?.extracted_data?.total || selectedTransaction.value.amount
       selectedTransaction.value.description = result.data?.extracted_data?.merchant !== 'Unknown Merchant' 
         ? (result.data?.extracted_data?.merchant || selectedTransaction.value.description) 
         : selectedTransaction.value.description
    }
  } catch { alert('OCR mislukt') }
}

const handleProfileSave = async ({ name, email }: { name: string; email: string }): Promise<void> => {
  try {
    const res = await store.apiFetch('/users/profile', { method: 'PUT', body: JSON.stringify({ name, email }) })
    if (res.ok) {
      const data = await res.json() as { user: import('@/types').User }
      store.currentUser = data.user
      localStorage.setItem('wbw_user', JSON.stringify(data.user))
      isProfileModalOpen.value = false
    }
  } catch { alert('Profiel opslaan mislukt') }
}

const handleBankImported = async (rows: BankImportRow[]): Promise<void> => {
  if (!rows?.length || !store.currentUser || !store.groupMembers?.length) return
  try {
    let ok = 0
    for (const r of rows) {
      const payload = {
        description: r.description || 'Bankimport',
        amount: Math.abs(Number(r.amount)),
        date: r.date || new Date().toISOString().split('T')[0],
        payer_id: store.currentUser.id,
        type: 'EXPENSE' as const,
        category: null as CategoryKey | null, // Let backend auto-classify
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
    alert('Import mislukt: ' + ((e as Error).message || 'onbekend'))
  }
}

const selectActivity = (id: number | null): void => {
  selectedActivityId.value = id
  store.fetchData(id)
}

const openActivityModal = (activity: import('@/types').Activity | null = null): void => {
  selectedActivity.value = activity
  isActivityModalOpen.value = true
}

const handleActivitySave = async (data: ActivityFormData): Promise<void> => {
  try {
    const isNew = !selectedActivity.value
    const endpoint = isNew ? '/activities' : `/activities/${selectedActivity.value?.id}`
    const method = isNew ? 'POST' : 'PUT'
    const res = await store.apiFetch(endpoint, { method, body: JSON.stringify(data) })
    if (res.ok) {
      await store.fetchData(selectedActivityId.value)
      isActivityModalOpen.value = false
      selectedActivity.value = null
    }
  } catch { alert('Activiteit opslaan mislukt') }
}

const getActivityName = (id: number | null): ActivityDisplay | null => {
  if (!id) return null
  const a = store.activities.find(a => a.id === id)
  return a ? { name: a.name, icon: a.icon, color: a.color } : null
}

const selectedActivityLabel = (): string | null => {
  if (!selectedActivityId.value) return null
  const a = store.activities.find(a => a.id === selectedActivityId.value)
  return a ? a.name : null
}

const handleSettle = async (): Promise<void> => {
  settleLoading.value = true
  try {
    const body = selectedActivityId.value ? { activity_id: selectedActivityId.value } : {}
    const res = await store.apiFetch('/settlements/commit', { method: 'POST', body: JSON.stringify(body) })
    if (res.ok) {
      await store.fetchData(selectedActivityId.value)
    } else {
      const data = await res.json().catch(() => ({})) as { message?: string }
      alert(data.message || 'Afrekenen mislukt')
    }
  } catch (e) {
    alert('Afrekenen mislukt: ' + ((e as Error).message || 'onbekend'))
  } finally {
    settleLoading.value = false
  }
}

const updateBulkActivityId = (v: number | string | null): void => {
  bulkChosenActivityId.value = (v === 'null' || v === '' || v == null) ? null : Number(v)
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
                                   @click="selectedCategoryFilter = cat.key as CategoryKey; showFilterDropdown = false"
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
                 <div v-if="selectedTransactionIds.size > 0" class="flex flex-wrap items-center gap-4 p-4 bg-zinc-900/80 border border-zinc-800 rounded">
                    <span class="font-black uppercase italic text-brand-red">{{ selectedTransactionIds.size }} geselecteerd</span>
                    <span class="text-zinc-600 text-[10px] font-medium uppercase tracking-wider flex items-center gap-1">
                      <button type="button" class="hover:text-brand-red transition-colors" @click="selectAllVisible">Alles aanvinken</button>
                      <span class="opacity-50">·</span>
                      <button type="button" class="hover:text-brand-red transition-colors" @click="clearSelection">Selectie leegmaken</button>
                    </span>
                    <button type="button" class="px-4 py-2 text-[10px] font-black uppercase bg-industrial-gray border border-zinc-700 text-white hover:border-brand-red transition-all" @click="openBulkActivityModal">Koppel aan activiteit</button>
                    <button type="button" class="px-4 py-2 text-[10px] font-black uppercase bg-industrial-gray border border-zinc-700 text-white hover:border-brand-red transition-all" @click="openBulkSplitsModal">Zelfde personen toepassen</button>
                    <button type="button" class="px-4 py-2 text-[10px] font-black uppercase bg-brand-red/80 text-white hover:bg-brand-red transition-all" @click="handleBulkDelete">Verwijderen</button>
                 </div>
                 <div v-for="group in groupedTransactions" :key="group.label" class="space-y-4">
                    <h3 class="text-sm font-black uppercase tracking-[0.2em] text-white italic border-b border-zinc-800 pb-2 mb-4">{{ group.label }}</h3>
                    <div class="space-y-2">
                       <TransactionCard v-for="t in group.txs" :key="t.id ?? `new-${Math.random()}`" 
                                       :transaction="t" 
                                       :payer-name="getPayerName(t.payer_id)"
                                       :activity="getActivityName(t.activity_id)"
                                       :selectable="true"
                                       :selected="selectedTransactionIds.has(t.id!)"
                                       @click="openTransaction(t)"
                                       @toggle-select="toggleSelect" />
                    </div>
                 </div>
              </template>
              <template v-else>
                 <div class="bg-industrial-gray border border-zinc-800 p-6">
                    <h3 class="text-xs uppercase font-black mb-4 tracking-[0.2em] border-b border-zinc-800 pb-2 text-brand-red">Prullenbak</h3>
                    <p v-if="!store.deletedTransactions.length" class="text-zinc-500 text-sm italic">Geen verwijderde transacties.</p>
                    <div v-else class="space-y-2">
                       <div v-for="t in store.deletedTransactions" :key="t.id ?? `deleted-${Math.random()}`" class="flex items-center justify-between gap-4 p-4 bg-zinc-900/50 border border-zinc-800 rounded">
                          <div>
                             <span class="font-black uppercase italic text-white">{{ t.description }}</span>
                             <span class="text-zinc-500 text-sm ml-2">€ {{ (t.amount || 0).toFixed(2) }}</span>
                             <span class="text-zinc-500 text-[10px] block mt-1">{{ getPayerName(t.payer_id) }} · {{ t.deleted_at ? new Date(t.deleted_at).toLocaleDateString('nl-NL') : '' }}</span>
                          </div>
                          <div class="flex gap-2 shrink-0">
                             <button type="button" class="px-4 py-2 text-[10px] font-black uppercase bg-zinc-700 text-white hover:bg-zinc-600 transition-all" @click="handleRestore(t.id!)">Herstel</button>
                             <button type="button" class="px-4 py-2 text-[10px] font-black uppercase bg-brand-red/80 text-white hover:bg-brand-red transition-all" @click="handleDeletePermanent(t.id!)">Definitief verwijderen</button>
                          </div>
                       </div>
                    </div>
                 </div>
              </template>
              <div v-if="toastMessage" class="fixed bottom-8 left-1/2 -translate-x-1/2 bg-brand-red text-white px-6 py-3 font-black uppercase italic text-sm shadow-xl z-50 animate-in fade-in duration-300">
                 {{ toastMessage }}
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
                          <img :src="u.avatar_url || ''" class="w-12 h-12 border border-zinc-800 grayscale object-cover" @error="(e) => (e.target as HTMLImageElement).style.display = 'none'">
                          <span class="text-lg font-black uppercase italic tracking-tight">{{ u.name }}</span>
                        </div>
                        <div class="text-2xl font-black italic tracking-tighter" :class="getBalanceForUser(u.id) >= 0 ? 'text-zinc-400' : 'text-brand-red'">
                           {{ getBalanceForUser(u.id) >= 0 ? '+' : '' }}{{ getBalanceForUser(u.id).toFixed(2) }}
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

      <Transition name="fade">
        <div v-if="isBulkActivityModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div class="absolute inset-0 bg-black/95 backdrop-blur-md" @click="isBulkActivityModalOpen = false"></div>
          <div class="bg-industrial-gray w-full max-w-md border border-zinc-800 shadow-2xl relative p-8 text-white">
            <h3 class="text-lg font-black uppercase italic mb-4">Koppel aan activiteit</h3>
            <ActivitySelector v-if="store.activities?.length"
                              :activities="store.activities"
                              :selected-id="bulkChosenActivityId"
                              @update:selected-id="updateBulkActivityId" />
            <div class="mt-6 flex gap-4">
              <button type="button" class="px-6 py-3 border border-zinc-700 text-zinc-400 font-black uppercase text-sm" @click="isBulkActivityModalOpen = false">Annuleren</button>
              <button type="button" class="flex-1 bg-brand-red text-white py-3 font-black uppercase text-sm" @click="handleBulkActivityApply">Toepassen</button>
            </div>
          </div>
        </div>
      </Transition>

      <Transition name="fade">
        <div v-if="isBulkSplitsModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div class="absolute inset-0 bg-black/95 backdrop-blur-md" @click="isBulkSplitsModalOpen = false"></div>
          <div class="bg-industrial-gray w-full max-w-md border border-zinc-800 shadow-2xl relative p-8 text-white max-h-[90vh] overflow-y-auto">
            <h3 class="text-lg font-black uppercase italic mb-4">Zelfde personen toepassen</h3>
            <div class="space-y-2">
              <div v-for="u in store.groupMembers" :key="u.id"
                   class="flex items-center justify-between p-4 border border-zinc-800 transition-all"
                   :class="bulkSplits.some(s => s.user_id === u.id) ? 'bg-zinc-900 border-brand-red/50' : 'opacity-50'">
                <div class="flex items-center gap-4 cursor-pointer" @click="toggleUserInBulkSplits(u.id)">
                  <div class="w-1.5 h-4" :class="bulkSplits.some(s => s.user_id === u.id) ? 'bg-brand-red' : 'bg-zinc-700'"></div>
                  <span class="font-black uppercase text-[11px] italic">{{ u.name }}</span>
                </div>
                <div v-if="bulkSplits.some(s => s.user_id === u.id)" class="flex items-center gap-2">
                  <button type="button" class="w-6 h-6 hover:text-brand-red font-black text-xs" @click="decrementBulkWeight(u.id)">−</button>
                  <span class="font-black text-brand-red text-sm w-6 text-center">{{ bulkSplits.find(s => s.user_id === u.id)?.weight ?? 1 }}</span>
                  <button type="button" class="w-6 h-6 hover:text-brand-red font-black text-xs" @click="incrementBulkWeight(u.id)">+</button>
                </div>
              </div>
            </div>
            <div class="mt-6 flex gap-4">
              <button type="button" class="px-6 py-3 border border-zinc-700 text-zinc-400 font-black uppercase text-sm" @click="isBulkSplitsModalOpen = false">Annuleren</button>
              <button type="button" class="flex-1 bg-brand-red text-white py-3 font-black uppercase text-sm" @click="handleBulkSplitsApply">Toepassen</button>
            </div>
          </div>
        </div>
      </Transition>
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
