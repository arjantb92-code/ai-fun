<script setup lang="ts">
import { computed } from 'vue'
import { getCategoryConfig } from '@/config/categories'
import type { Transaction, ActivityDisplay } from '@/types'

interface Props {
  transaction: Transaction
  payerName?: string
  activity?: ActivityDisplay | null
  selectable?: boolean
  selected?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  payerName: 'Onbekend',
  activity: null,
  selectable: false,
  selected: false
})

const emit = defineEmits<{
  (e: 'click'): void
  (e: 'toggle-select', id: number): void
}>()

const isIncome = computed(() => props.transaction.type === 'INCOME')
const categoryConfig = computed(() => getCategoryConfig(props.transaction.category))
</script>

<template>
  <div @click="emit('click')" 
       class="bg-industrial-gray/40 p-5 flex justify-between items-center hover:bg-zinc-900 border-l-2 transition-all cursor-pointer group shadow-lg text-white relative"
       :class="selected ? 'border-brand-red bg-brand-red/10' : 'border-transparent hover:border-brand-red'">
    <div class="flex items-center gap-6">
      <div v-if="selectable" 
           class="shrink-0 w-4 h-4 border-2 rounded-sm transition-all flex items-center justify-center opacity-0 group-hover:opacity-100"
           :class="selected ? 'opacity-100 bg-brand-red border-brand-red' : 'border-zinc-600 hover:border-brand-red/50'"
           @click.stop="emit('toggle-select', transaction.id!)">
        <svg v-if="selected" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path>
        </svg>
      </div>
      <div class="w-12 h-12 bg-zinc-900 flex items-center justify-center font-black italic text-brand-red border border-zinc-800 group-hover:bg-brand-red group-hover:text-white transition-all transform group-hover:rotate-3"
           :class="selectable && selected ? 'ring-2 ring-brand-red/50' : ''">
        {{ transaction.description[0] }}
      </div>
      <div>
        <div class="flex items-center gap-2 mb-1 flex-wrap">
          <div class="text-[10px] font-black px-2 py-0.5 border tracking-tighter uppercase italic"
               :style="{ color: categoryConfig.color, borderColor: categoryConfig.color, backgroundColor: categoryConfig.color + '15' }">
            {{ categoryConfig.icon }} {{ categoryConfig.label }}
          </div>
          <div v-if="activity" 
               class="text-[10px] font-black px-2 py-0.5 border tracking-tighter uppercase italic"
               :style="{ color: activity.color || '#E30613', borderColor: activity.color || '#E30613' }">
            {{ activity.icon || '📋' }} {{ activity.name }}
          </div>
          <div v-if="transaction.time && transaction.time !== '00:00'" 
               class="text-[10px] font-black text-white bg-brand-red/20 px-2 py-0.5 border border-brand-red/40 tracking-tighter uppercase italic">
            {{ transaction.time }}
          </div>
        </div>
        <div class="text-xl font-black group-hover:text-brand-red transition-colors tracking-tight uppercase italic">
          {{ transaction.description }}
        </div>
      </div>
    </div>
    <div class="text-right">
      <div class="text-3xl font-black tracking-tighter italic" :class="isIncome ? 'text-zinc-500' : 'text-white'">
        {{ isIncome ? '-' : '' }}€ {{ transaction.amount.toFixed(2) }}
      </div>
      <div class="text-[10px] uppercase font-black opacity-30">
        Payer: <span class="text-white">{{ payerName }}</span>
      </div>
    </div>
  </div>
</template>
