<script setup>
import { computed } from 'vue'

const props = defineProps({
  balance: {
    type: Number,
    required: true
  },
  label: {
    type: String,
    default: 'Personal Balance'
  }
})

const isPositive = computed(() => props.balance >= 0)
</script>

<template>
  <div class="bg-industrial-gray p-8 border-l-4 border-brand-red shadow-2xl relative overflow-hidden group hover:border-l-8 transition-all">
    <div class="absolute right-[-20px] top-[-20px] text-brand-red opacity-5 text-9xl font-bold italic select-none group-hover:opacity-10 transition-opacity">WBW</div>
    <h2 class="text-xs uppercase opacity-40 font-black mb-4 tracking-[0.2em]">{{ label }}</h2>
    <div class="text-6xl font-black mb-2 tracking-tighter italic leading-none" :class="isPositive ? 'text-white' : 'text-brand-red'">
      € {{ balance.toFixed(2) }}
    </div>
    <p v-if="balance > 0" class="text-brand-red font-bold uppercase tracking-widest text-[10px] mt-4 flex items-center gap-2">
      <span class="w-2 h-2 bg-brand-red animate-pulse rounded-full"></span>
      Tegoed
    </p>
    <p v-else-if="balance < 0" class="text-white/40 font-bold uppercase tracking-widest text-[10px] mt-4 flex items-center gap-2">
      <span class="w-2 h-2 bg-white/20 rounded-full"></span>
      Schuld
    </p>
    <p v-else class="text-zinc-600 font-bold uppercase tracking-widest text-[10px] mt-4">Alles verrekend</p>
  </div>
</template>
