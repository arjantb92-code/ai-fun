<script setup>
import { computed } from 'vue'

const props = defineProps({
  transaction: {
    type: Object,
    required: true
  },
  payerName: {
    type: String,
    default: 'Onbekend'
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

const handleClick = (e) => {
  if (props.selectable) {
    emit('toggle-select', props.transaction.id)
  } else {
    emit('click')
  }
}

const handleCheckboxClick = (e) => {
  e.stopPropagation()
  emit('toggle-select', props.transaction.id)
}
</script>

<template>
  <div @click="handleClick" 
       class="p-5 flex justify-between items-center hover:bg-zinc-900 border-l-2 transition-all cursor-pointer group shadow-lg text-white"
       :class="[
         selected ? 'bg-brand-red/10 border-brand-red' : 'bg-industrial-gray/40 border-transparent hover:border-brand-red'
       ]">
    <div class="flex items-center gap-6">
      <!-- Checkbox for selection mode -->
      <div v-if="selectable" 
           @click="handleCheckboxClick"
           class="w-6 h-6 border-2 flex items-center justify-center transition-all"
           :class="selected ? 'bg-brand-red border-brand-red' : 'border-zinc-600 hover:border-brand-red'">
        <span v-if="selected" class="text-white text-sm font-black">✓</span>
      </div>
      
      <div class="w-12 h-12 bg-zinc-900 flex items-center justify-center font-black italic text-brand-red border border-zinc-800 group-hover:bg-brand-red group-hover:text-white transition-all transform group-hover:rotate-3">
        {{ transaction.description[0] }}
      </div>
      <div>
        <div class="flex items-center gap-3 mb-1">
          <div v-if="transaction.time && transaction.time !== '00:00'" 
               class="text-[11px] font-black text-white bg-brand-red/20 px-2 py-0.5 border border-brand-red/40 tracking-tighter uppercase italic">
            {{ transaction.time }}
          </div>
          <div class="text-[10px] opacity-60 uppercase font-black tracking-widest">
            {{ transaction.type }}
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
