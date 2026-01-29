<script setup>
import { ref } from 'vue'

defineProps({
  history: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['undo', 'restore', 'delete', 'delete-permanent'])

const expandedIds = ref(new Set())

function togglePosten(sessionId) {
  if (expandedIds.value.has(sessionId)) {
    expandedIds.value.delete(sessionId)
  } else {
    expandedIds.value.add(sessionId)
  }
  expandedIds.value = new Set(expandedIds.value)
}

function formatDate(d, time) {
  if (!d) return ''
  const opts = { day: 'numeric', month: 'short', year: 'numeric' }
  const str = new Date(d).toLocaleDateString('nl-NL', opts)
  if (time) return `${str} ${time}`
  return str
}
</script>

<template>
  <div class="bg-industrial-gray border border-zinc-800 p-8 shadow-xl">
    <h3 class="text-xs uppercase font-black mb-6 tracking-[0.2em] border-b border-zinc-800 pb-2 text-brand-red">Afrekeningen</h3>
    <template v-if="history.length > 0">
      <div v-for="s in history" :key="s.id" class="border-b border-zinc-800/50 pb-6 mb-6 last:border-0 last:mb-0 last:pb-0">
        <div class="flex justify-between items-baseline mb-2">
          <span class="text-sm font-black uppercase italic text-white">{{ s.description || 'Afrekening' }}</span>
          <span class="text-[10px] text-zinc-500">{{ s.date ? new Date(s.date).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short', year: 'numeric' }) : '' }}</span>
        </div>
        <div class="text-[10px] text-zinc-500 mb-2">Totaal: € {{ (s.total_amount || 0).toFixed(2) }}</div>
        <div v-for="(r, idx) in (s.results || [])" :key="idx" class="text-[11px] font-black uppercase tracking-widest border-l border-zinc-700 pl-3 py-1">
          <span class="text-zinc-400">{{ r.from_user }}</span>
          <span class="text-zinc-600 mx-1">➜</span>
          <span class="text-brand-red">{{ r.to_user }}</span>
          <span class="text-white ml-2">€ {{ (r.amount || 0).toFixed(2) }}</span>
        </div>
        <div class="mt-3">
          <button
            v-if="(s.transactions || []).length > 0"
            type="button"
            class="text-[11px] font-bold uppercase tracking-wider text-zinc-400 hover:text-brand-red transition-colors"
            @click="togglePosten(s.id)"
          >
            {{ expandedIds.has(s.id) ? 'Verberg posten' : 'Toon posten' }} ({{ s.transactions.length }})
          </button>
          <div v-if="expandedIds.has(s.id) && (s.transactions || []).length" class="mt-3 pl-3 border-l-2 border-zinc-700 space-y-2">
            <div
              v-for="tx in s.transactions"
              :key="tx.id"
              class="flex flex-wrap items-baseline gap-x-2 gap-y-0.5 text-[11px] text-zinc-300"
            >
              <span class="truncate min-w-0 flex-1">{{ tx.description }}</span>
              <span class="text-zinc-500 shrink-0">{{ formatDate(tx.date, tx.time) }}</span>
              <span class="text-zinc-400 shrink-0">{{ tx.payer || '—' }}</span>
              <span class="text-white font-semibold shrink-0">€ {{ (tx.amount || 0).toFixed(2) }}</span>
            </div>
          </div>
          <p v-else-if="expandedIds.has(s.id) && (!s.transactions || !s.transactions.length)" class="text-[11px] text-zinc-500 italic mt-2">Geen posten bij deze afrekening.</p>
        </div>
        <div v-if="!s.deleted_at" class="mt-3 flex gap-2">
          <button
            type="button"
            class="text-[10px] font-bold uppercase tracking-wider text-zinc-500 hover:text-brand-red transition-colors"
            @click="emit('delete', s.id)"
          >
            Ongedaan maken
          </button>
        </div>
        <div v-else class="mt-3 flex gap-2">
          <button
            type="button"
            class="text-[10px] font-bold uppercase tracking-wider text-zinc-400 hover:text-white transition-colors"
            @click="emit('restore', s.id)"
          >
            Herstel
          </button>
          <span class="text-zinc-600">·</span>
          <button
            type="button"
            class="text-[10px] font-bold uppercase tracking-wider text-zinc-500 hover:text-brand-red transition-colors"
            @click="emit('delete-permanent', s.id)"
          >
            Definitief verwijderen
          </button>
        </div>
      </div>
    </template>
    <p v-else class="text-zinc-500 text-sm italic">Nog geen afrekeningen.</p>
  </div>
</template>
