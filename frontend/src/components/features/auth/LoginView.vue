<script setup lang="ts">
import { ref } from 'vue'
import type { LoginCredentials } from '@/types'

interface Props {
  error?: string
}

defineProps<Props>()

const emit = defineEmits<{
  (e: 'login', credentials: LoginCredentials): void
}>()

const credentials = ref<LoginCredentials>({ username: '', password: '' })

const handleSubmit = (): void => {
  emit('login', credentials.value)
}
</script>

<template>
  <div class="fixed inset-0 z-[100] bg-black flex items-center justify-center p-4">
    <!-- Subtle Background Effect -->
    <div class="absolute inset-0 opacity-10">
      <div class="absolute inset-0" style="background-image: radial-gradient(circle at 50% 50%, #E30613 0%, transparent 70%);"></div>
    </div>
    
    <div class="relative z-10 w-full max-w-md bg-industrial-gray border border-zinc-800 shadow-2xl p-10 md:p-14">
      <div class="h-1 bg-brand-red absolute top-0 left-0 right-0 shadow-[0_0_15px_rgba(227,6,19,0.3)]"></div>
      
      <div class="text-center mb-12">
        <h1 class="text-5xl font-black uppercase italic tracking-tighter text-white mb-2">
          Better <span class="text-brand-red">WBW</span>
        </h1>
        <p class="text-[10px] text-zinc-500 uppercase font-black tracking-[0.3em]">Sign in to your account</p>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-6">
        <div>
          <label class="block text-[10px] uppercase font-black text-zinc-500 mb-2 tracking-widest italic">Username / Email</label>
          <input v-model="credentials.username" type="text" 
                 class="w-full bg-black border border-zinc-800 p-4 font-black uppercase outline-none focus:border-brand-red italic text-white transition-all" 
                 placeholder="NAME">
        </div>
        
        <div>
          <label class="block text-[10px] uppercase font-black text-zinc-500 mb-2 tracking-widest italic">Password</label>
          <input v-model="credentials.password" type="password" 
                 class="w-full bg-black border border-zinc-800 p-4 font-black uppercase outline-none focus:border-brand-red italic text-white transition-all" 
                 placeholder="********">
        </div>

        <div v-if="error" class="bg-brand-red/10 border border-brand-red/20 p-4 animate-in fade-in slide-in-from-top-1">
          <p class="text-brand-red text-center font-black uppercase italic text-[10px] tracking-widest">
            {{ error }}
          </p>
        </div>

        <button type="submit" 
                class="w-full bg-brand-red text-white py-5 font-black uppercase tracking-[0.2em] hover:bg-white hover:text-black transition-all transform active:scale-95 italic text-xl shadow-xl">
          Enter Group
        </button>
      </form>

      <div class="mt-10 pt-8 border-t border-zinc-800 text-center">
        <p class="text-[8px] text-zinc-600 font-black uppercase tracking-widest italic">
          Zero-Sum Expense Management System
        </p>
      </div>
    </div>
  </div>
</template>
