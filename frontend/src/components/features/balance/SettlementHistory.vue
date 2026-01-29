<script setup>
import { ref } from 'vue'

defineProps({
  settlements: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['undo'])

const expandedIds = ref(new Set())

const toggleExpand = (id) => {
  if (expandedIds.value.has(id)) {
    expandedIds.value.delete(id)
  } else {
    expandedIds.value.add(id)
  }
  // Force reactivity
  expandedIds.value = new Set(expandedIds.value)
}

const isExpanded = (id) => expandedIds.value.has(id)

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleDateString('nl-NL', { day: 'numeric', month: 'long', year: 'numeric' })
}
</script>

<template>
  <div v-if="settlements.length > 0" class="space-y-4">
    <h3 class="text-xs uppercase text-brand-red font-black mb-6 tracking-[0.2em] italic border-b border-zinc-800 pb-2">Afrekening Geschiedenis</h3>
    
    <div v-for="s in settlements" :key="s.id" class="bg-industrial-gray/40 border border-zinc-800">
      <!-- Settlement Header -->
      <div class="p-6">
        <div class="flex justify-between items-start mb-4">
          <div>
            <div class="text-[10px] uppercase font-black tracking-widest opacity-40 mb-1">{{ formatDate(s.date) }}</div>
            <div class="text-lg font-black uppercase italic">{{ s.description || 'Afrekening' }}</div>
          </div>
          <div class="text-2xl font-black italic text-brand-red">€ {{ s.total_amount.toFixed(2) }}</div>
        </div>
        
        <!-- Settlement Results -->
        <div class="space-y-2 mb-4">
          <div v-for="(r, idx) in s.results" :key="idx" 
               class="text-[11px] font-black uppercase tracking-widest border-l border-zinc-700 pl-3 py-1">
            <span class="text-white">{{ r.from_user }}</span> 
            <span class="text-zinc-600 mx-1">→</span> 
            <span class="text-brand-red">{{ r.to_user }}</span>
            <span class="text-white ml-2">€ {{ r.amount.toFixed(2) }}</span>
          </div>
        </div>
        
        <!-- Action buttons -->
        <div class="flex items-center gap-4">
          <button v-if="s.transactions && s.transactions.length > 0"
                  @click="toggleExpand(s.id)"
                  class="text-[10px] font-black uppercase tracking-widest text-zinc-500 hover:text-brand-red transition-colors">
            {{ isExpanded(s.id) ? 'Verberg' : 'Toon' }} posten ({{ s.transactions.length }})
          </button>
          <button @click="emit('undo', s.id)"
                  class="text-[10px] font-black uppercase tracking-widest text-zinc-500 hover:text-brand-red transition-colors border border-zinc-700 px-3 py-1 hover:border-brand-red">
            Ongedaan maken
          </button>
        </div>
      </div>
      
      <!-- Expandable Transactions List -->
      <div v-if="isExpanded(s.id) && s.transactions" class="border-t border-zinc-800 bg-black/30 p-4">
        <div class="space-y-2 max-h-64 overflow-y-auto custom-scrollbar">
          <div v-for="t in s.transactions" :key="t.id" 
               class="flex justify-between items-center py-2 border-b border-zinc-800/50 last:border-0">
            <div class="flex-1">
              <div class="font-black uppercase italic text-sm">{{ t.description }}</div>
              <div class="text-[10px] uppercase tracking-widest opacity-40">
                {{ t.date }} {{ t.time !== '00:00' ? t.time : '' }} • {{ t.payer }}
              </div>
            </div>
            <div class="text-lg font-black italic">€ {{ t.amount.toFixed(2) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
