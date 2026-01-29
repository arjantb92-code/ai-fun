<script setup>
import { useAppStore } from '@/stores/appStore'
const store = useAppStore()

defineEmits(['open-profile'])
</script>

<template>
  <header class="flex flex-col md:flex-row justify-between items-center mb-8 border-b border-industrial-gray pb-6 gap-4 shrink-0">
    <div class="flex items-center gap-6">
      <h1 class="text-4xl font-bold tracking-tighter uppercase italic text-brand-red text-shadow-glow">Better WBW</h1>
      
      <div v-if="store.currentUser" @click="$emit('open-profile')" 
           class="flex items-center gap-3 cursor-pointer group bg-zinc-900/50 px-4 py-2 border border-zinc-800 hover:border-brand-red transition-all">
        <div class="w-8 h-8 bg-black border border-zinc-700 overflow-hidden flex items-center justify-center">
          <img v-if="store.currentUser.avatar_url" :src="store.currentUser.avatar_url" 
               class="w-full h-full grayscale group-hover:grayscale-0 transition-all object-cover" 
               @error="store.currentUser.avatar_url = null">
          <span v-else class="text-[10px] font-black text-brand-red italic">{{ store.currentUser.name[0] }}</span>
        </div>
        <span class="text-xs font-black uppercase tracking-widest text-white">{{ store.currentUser.name }}</span>
      </div>

      <span :class="store.backendStatus === 'Online' ? 'text-brand-red border-brand-red' : 'text-zinc-500 border-zinc-800'" 
            class="text-[10px] uppercase font-bold px-2 py-0.5 border tracking-tighter bg-black/40">
        {{ store.backendStatus }}
      </span>
    </div>

    <slot name="actions"></slot>
  </header>
</template>
