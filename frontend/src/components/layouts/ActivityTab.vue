<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import { getCategoryLabel } from '@/config/categories'
import TransactionCard from '@/components/features/transactions/TransactionCard.vue'
import type { Transaction, CategoryKey } from '@/types'

const store = useAppStore()
const toast = useToast()
const { showConfirm } = useConfirm()

const props = defineProps<{
  transactions: Transaction[]
  deletedTransactions: Transaction[]
  selectedActivityId: number | null
  selection: {
    hasSelection: { value: boolean }
    count: { value: number }
    isSelected: (id: number | null) => boolean
    toggle: (id: number | null) => void
    clear: () => void
    selectAll: (ids: (number | null)[]) => void
    getSelectedArray: () => (number | null)[]
  }
}>()

const emit = defineEmits<{
  (e: 'open-transaction', t: Transaction): void
  (e: 'create-entry'): void
  (e: 'open-bulk-activity'): void
  (e: 'open-bulk-splits'): void
}>()

const searchQuery = ref('')
const selectedCategoryFilter = ref<CategoryKey | null>(null)
const showFilterDropdown = ref(false)
const showTrash = ref(false)

const filteredTransactions = computed(() => {
  let result = props.transactions
  if (selectedCategoryFilter.value) {
    result = result.filter(t => t.category === selectedCategoryFilter.value)
  }
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
  const groups: { label: string; txs: Transaction[] }[] = []
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

function onShowTrash(show: boolean) {
  showTrash.value = show
  if (show) store.fetchTrash(props.selectedActivityId)
  if (!show) props.selection.clear()
}

function selectAllVisible() {
  const ids = groupedTransactions.value.flatMap(g => g.txs.map(t => t.id))
  props.selection.selectAll(ids)
}

async function handleBulkDelete() {
  const ok = await showConfirm({ message: `${props.selection.count.value} transactie(s) verplaatsen naar prullenbak?` })
  if (!ok) return
  try {
    let deleted = 0
    for (const id of props.selection.getSelectedArray()) {
      if (id == null) continue
      const res = await store.apiFetch(`/transactions/${id}`, { method: 'DELETE' })
      if (res.ok) deleted++
    }
    await store.fetchData(props.selectedActivityId)
    props.selection.clear()
    toast.show(`${deleted} transactie(s) naar prullenbak`)
  } catch {
    toast.show('Verwijderen mislukt')
  }
}

async function handleRestore(id: number) {
  try {
    const res = await store.apiFetch(`/transactions/${id}/restore`, { method: 'POST' })
    if (res.ok) {
      await store.fetchData(props.selectedActivityId)
      await store.fetchTrash(props.selectedActivityId)
    } else {
      const data = await res.json().catch(() => ({})) as { error?: string }
      toast.show(data.error || 'Herstellen mislukt')
    }
  } catch {
    toast.show('Herstellen mislukt')
  }
}

async function handleDeletePermanent(id: number) {
  const ok = await showConfirm({ message: 'Definitief verwijderen? Dit kan niet ongedaan.' })
  if (!ok) return
  try {
    const res = await store.apiFetch(`/transactions/${id}/permanent`, { method: 'DELETE' })
    if (res.ok) {
      await store.fetchData(props.selectedActivityId)
      await store.fetchTrash(props.selectedActivityId)
    } else {
      const data = await res.json().catch(() => ({})) as { error?: string }
      toast.show(data.error || 'Definitief verwijderen mislukt')
    }
  } catch {
    toast.show('Definitief verwijderen mislukt')
  }
}

const getActivityName = (id: number | null) => store.getActivityInfo(id)
</script>

<template>
  <div class="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500 text-white">
    <div class="flex items-center gap-4 flex-wrap">
      <div class="flex border border-zinc-800 rounded overflow-hidden">
        <button
          type="button"
          :class="!showTrash ? 'bg-brand-red text-white' : 'bg-industrial-gray text-zinc-500 hover:text-white'"
          class="px-6 py-3 font-black uppercase italic text-[10px] tracking-widest transition-all"
          @click="onShowTrash(false)"
        >
          Transacties
        </button>
        <button
          type="button"
          :class="showTrash ? 'bg-brand-red text-white' : 'bg-industrial-gray text-zinc-500 hover:text-white'"
          class="px-6 py-3 font-black uppercase italic text-[10px] tracking-widest transition-all"
          @click="onShowTrash(true)"
        >
          Prullenbak
        </button>
      </div>
      <div v-if="!showTrash" class="relative max-w-xl flex-1 min-w-[200px]">
        <span class="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-700">🔍</span>
        <input
          v-model="searchQuery"
          type="text"
          class="w-full bg-industrial-gray border border-zinc-800 p-4 pl-12 pr-12 font-black uppercase italic text-sm outline-none focus:border-brand-red transition-all text-white"
          placeholder="Zoek transactie of persoon..."
        >
      </div>
      <div v-if="!showTrash" class="relative">
        <button
          type="button"
          class="bg-industrial-gray border border-zinc-800 p-4 font-black uppercase italic text-sm transition-all hover:border-brand-red flex items-center gap-2"
          :class="selectedCategoryFilter ? 'border-brand-red text-brand-red' : 'text-zinc-500'"
          @click="showFilterDropdown = !showFilterDropdown"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          <span class="hidden md:inline">{{ selectedCategoryFilter ? getCategoryLabel(selectedCategoryFilter) : 'Filter' }}</span>
        </button>
        <Transition name="fade">
          <div v-if="showFilterDropdown">
            <div class="fixed inset-0 z-40" @click="showFilterDropdown = false" />
            <div class="absolute top-full right-0 mt-2 bg-industrial-gray border border-zinc-800 shadow-xl z-50 min-w-[200px]">
              <button
                type="button"
                class="w-full text-left px-4 py-3 font-black uppercase italic text-xs transition-all hover:bg-zinc-900"
                :class="!selectedCategoryFilter ? 'text-brand-red bg-zinc-900' : 'text-zinc-400'"
                @click="selectedCategoryFilter = null; showFilterDropdown = false"
              >
                Alle categorieën
              </button>
              <button
                v-for="cat in store.categories"
                :key="cat.key"
                type="button"
                class="w-full text-left px-4 py-3 font-black uppercase italic text-xs transition-all hover:bg-zinc-900"
                :class="selectedCategoryFilter === cat.key ? 'text-brand-red bg-zinc-900' : 'text-zinc-400'"
                @click="selectedCategoryFilter = cat.key as CategoryKey; showFilterDropdown = false"
              >
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
        <button type="button" class="btn-action" @click="emit('open-bulk-activity')">Koppel aan activiteit</button>
        <button type="button" class="btn-action" @click="emit('open-bulk-splits')">Zelfde personen toepassen</button>
        <button type="button" class="px-4 py-2 text-[10px] font-black uppercase bg-brand-red/80 text-white hover:bg-brand-red transition-all" @click="handleBulkDelete">Verwijderen</button>
      </div>
      <div v-for="group in groupedTransactions" :key="group.label" class="space-y-4">
        <h3 class="text-sm font-black uppercase tracking-[0.2em] text-white italic border-b border-zinc-800 pb-2 mb-4">
          {{ group.label }}
        </h3>
        <div class="space-y-2">
          <TransactionCard
            v-for="t in group.txs"
            :key="t.id ?? `new-${Math.random()}`"
            :transaction="t"
            :payer-name="store.getUserName(t.payer_id)"
            :activity="getActivityName(t.activity_id)"
            :selectable="true"
            :selected="selection.isSelected(t.id)"
            @click="emit('open-transaction', t)"
            @toggle-select="selection.toggle"
          />
        </div>
      </div>
    </template>

    <template v-else>
      <div class="bg-industrial-gray border border-zinc-800 p-6">
        <h3 class="text-xs uppercase font-black mb-4 tracking-[0.2em] border-b border-zinc-800 pb-2 text-brand-red">Prullenbak</h3>
        <p v-if="!deletedTransactions.length" class="text-zinc-500 text-sm italic">Geen verwijderde transacties.</p>
        <div v-else class="space-y-2">
          <div
            v-for="t in deletedTransactions"
            :key="t.id ?? `deleted-${Math.random()}`"
            class="flex items-center justify-between gap-4 p-4 bg-zinc-900/50 border border-zinc-800 rounded"
          >
            <div>
              <span class="font-black uppercase italic text-white">{{ t.description }}</span>
              <span class="text-zinc-500 text-sm ml-2">€ {{ (t.amount || 0).toFixed(2) }}</span>
              <span class="text-zinc-500 text-[10px] block mt-1">{{ store.getUserName(t.payer_id) }} · {{ t.deleted_at ? new Date(t.deleted_at).toLocaleDateString('nl-NL') : '' }}</span>
            </div>
            <div class="flex gap-2 shrink-0">
              <button type="button" class="px-4 py-2 text-[10px] font-black uppercase bg-zinc-700 text-white hover:bg-zinc-600 transition-all" @click="handleRestore(t.id!)">Herstel</button>
              <button type="button" class="px-4 py-2 text-[10px] font-black uppercase bg-brand-red/80 text-white hover:bg-brand-red transition-all" @click="handleDeletePermanent(t.id!)">Definitief verwijderen</button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
