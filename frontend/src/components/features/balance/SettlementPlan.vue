<script setup lang="ts">
import type { SettlementSuggestion } from '@/types'

interface Props {
  settlements: SettlementSuggestion[]
  activityName?: string | null
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  activityName: null,
  loading: false
})

const emit = defineEmits<{
  (e: 'settle'): void
}>()
</script>

<template>
  <div class="bg-black/40 border border-brand-red/20 p-8 shadow-xl space-y-6">
    <h3 class="text-xs uppercase text-brand-red font-black tracking-[0.2em] italic">Betaalvoorstel</h3>
    <template v-if="settlements.length > 0">
      <div v-for="(s, idx) in settlements" :key="idx" 
           class="text-[11px] font-black uppercase tracking-widest border-l border-zinc-800 pl-4 py-2 mb-4">
        <span class="text-white">{{ s.from_user }}</span> 
        <span class="text-zinc-600 mx-1">➜</span> 
        <span class="text-brand-red">{{ s.to_user }}</span>
        <div class="text-lg italic text-white mt-1">€ {{ s.amount.toFixed(2) }}</div>
      </div>
      <button 
        type="button"
        @click="emit('settle')"
        :disabled="loading"
        class="w-full py-4 font-black uppercase italic bg-brand-red text-white hover:bg-red-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {{ loading ? 'Bezig...' : (activityName ? `Afrekenen: ${activityName}` : 'Alles afrekenen') }}
      </button>
    </template>
    <p v-else class="text-zinc-500 text-sm italic">Geen openstaande stand. Alles is vereffend.</p>
  </div>
</template>
