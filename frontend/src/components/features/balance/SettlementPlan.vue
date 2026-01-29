<script setup>
const props = defineProps({
  settlements: {
    type: Array,
    required: true
  }
})
</script>

<template>
  <div v-if="settlements.length > 0" class="bg-black/40 border border-brand-red/20 p-8 shadow-xl">
    <h3 class="text-xs uppercase text-brand-red font-black mb-6 tracking-[0.2em] italic">Betaalvoorstel</h3>
    <div v-for="(s, idx) in settlements" :key="idx" 
         class="text-[11px] font-black uppercase tracking-widest border-l border-zinc-800 pl-4 py-2 mb-4">
      <span class="text-white">{{ s.from_user }}</span> 
      <span class="text-zinc-600 mx-1">➜</span> 
      <span class="text-brand-red">{{ s.to_user }}</span>
      <div class="text-lg italic text-white mt-1">€ {{ s.amount.toFixed(2) }}</div>
    </div>
  </div>
</template>
