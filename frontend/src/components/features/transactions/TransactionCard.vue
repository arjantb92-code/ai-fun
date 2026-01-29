<script setup>
import { computed } from 'vue'

const CATEGORY_CONFIG = {
  boodschappen: { label: 'Boodschappen', icon: '🛒', color: '#22c55e' },
  huishoudelijk: { label: 'Huishoudelijk', icon: '🏠', color: '#f59e0b' },
  winkelen: { label: 'Winkelen', icon: '🛍️', color: '#ec4899' },
  vervoer: { label: 'Vervoer', icon: '🚗', color: '#3b82f6' },
  reizen_vrije_tijd: { label: 'Reizen & Vrije Tijd', icon: '✈️', color: '#8b5cf6' },
  overig: { label: 'Overig', icon: '📦', color: '#6b7280' }
}

const props = defineProps({
  transaction: {
    type: Object,
    required: true
  },
  payerName: {
    type: String,
    default: 'Onbekend'
  },
  activity: {
    type: Object,
    default: null
  },
  selectable: {
    type: Boolean,
    default: false
  },
  selected: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click', 'toggle-select'])

const isIncome = computed(() => props.transaction.type === 'INCOME')
const categoryConfig = computed(() => CATEGORY_CONFIG[props.transaction.category] || CATEGORY_CONFIG.overig)
</script>

<template>
  <div @click="emit('click')" 
       class="bg-industrial-gray/40 p-5 flex justify-between items-center hover:bg-zinc-900 border-l-2 transition-all cursor-pointer group shadow-lg text-white relative"
       :class="selected ? 'border-brand-red bg-brand-red/10' : 'border-transparent hover:border-brand-red'">
    <div class="flex items-center gap-6">
      <div v-if="selectable" 
           class="shrink-0 w-4 h-4 border-2 rounded-sm transition-all flex items-center justify-center opacity-0 group-hover:opacity-100"
           :class="selected ? 'opacity-100 bg-brand-red border-brand-red' : 'border-zinc-600 hover:border-brand-red/50'"
           @click.stop="emit('toggle-select', transaction.id)">
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
