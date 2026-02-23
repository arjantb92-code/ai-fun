<script setup lang="ts">
import { ref } from 'vue'
import type { LoginCredentials } from '@/types'

interface Props {
  error?: string
  requiresActivation?: boolean
  activationEmail?: string
}

defineProps<Props>()

const emit = defineEmits<{
  (e: 'login', credentials: LoginCredentials): void
  (e: 'google-login'): void
  (e: 'resend-activation', email: string): void
}>()

const credentials = ref<LoginCredentials>({ username: '', password: '' })

const handleSubmit = (): void => {
  emit('login', credentials.value)
}

const handleGoogleLogin = (): void => {
  emit('google-login')
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

      <!-- Activation Required Message -->
      <div v-if="requiresActivation" class="bg-yellow-900/20 border border-yellow-600/30 p-4 mb-6">
        <p class="text-yellow-500 text-center font-bold text-sm mb-2">
          Email verification required
        </p>
        <p class="text-zinc-400 text-center text-xs mb-3">
          Please check your email ({{ activationEmail }}) for the activation link.
        </p>
        <button
          type="button"
          class="w-full text-yellow-500 text-xs underline hover:text-yellow-400"
          @click="$emit('resend-activation', activationEmail || '')"
        >
          Resend activation email
        </button>
      </div>

      <!-- Google Sign-In -->
      <button
        type="button"
        class="w-full bg-white text-black py-4 font-bold uppercase tracking-wider hover:bg-zinc-200 transition-all flex items-center justify-center gap-3 mb-6"
        @click="handleGoogleLogin"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        Continue with Google
      </button>

      <div class="relative mb-6">
        <div class="absolute inset-0 flex items-center">
          <div class="w-full border-t border-zinc-700"></div>
        </div>
        <div class="relative flex justify-center text-xs uppercase">
          <span class="bg-industrial-gray px-3 text-zinc-500 font-black tracking-widest">or</span>
        </div>
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

        <div v-if="error && !requiresActivation" class="bg-brand-red/10 border border-brand-red/20 p-4 animate-in fade-in slide-in-from-top-1">
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
        <p class="text-[8px] text-zinc-700 mt-2">
          No account? Get an invite link from a group member.
        </p>
      </div>
    </div>
  </div>
</template>
