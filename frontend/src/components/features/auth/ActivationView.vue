<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { API_BASE } from '@/config/api'

interface Props {
  token: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'activated', user: any): void
  (e: 'go-login'): void
}>()

const loading = ref(true)
const error = ref('')
const success = ref(false)
const showPasswordForm = ref(false)
const newPassword = ref('')
const confirmPassword = ref('')

const activateAccount = async (password?: string) => {
  loading.value = true
  error.value = ''
  
  try {
    const res = await fetch(`${API_BASE}/auth/activate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token: props.token,
        password: password || undefined
      })
    })
    
    const data = await res.json()
    
    if (res.ok) {
      success.value = true
      emit('activated', data.user)
    } else {
      if (res.status === 410) {
        error.value = 'Activation link has expired. Please request a new one.'
      } else {
        error.value = data.error || 'Activation failed'
      }
    }
  } catch {
    error.value = 'Could not connect to server'
  } finally {
    loading.value = false
  }
}

const handleSetPassword = () => {
  if (newPassword.value.length < 6) {
    error.value = 'Password must be at least 6 characters'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }
  activateAccount(newPassword.value)
}

onMounted(() => {
  showPasswordForm.value = true
  loading.value = false
})
</script>

<template>
  <div class="fixed inset-0 z-[100] bg-black flex items-center justify-center p-4">
    <div class="absolute inset-0 opacity-10">
      <div class="absolute inset-0" style="background-image: radial-gradient(circle at 50% 50%, #E30613 0%, transparent 70%);"></div>
    </div>
    
    <div class="relative z-10 w-full max-w-md bg-industrial-gray border border-zinc-800 shadow-2xl p-10">
      <div class="h-1 bg-brand-red absolute top-0 left-0 right-0 shadow-[0_0_15px_rgba(227,6,19,0.3)]"></div>
      
      <div class="text-center mb-8">
        <h1 class="text-3xl font-black uppercase italic text-white mb-2">
          Account <span class="text-brand-red">Activation</span>
        </h1>
      </div>
      
      <!-- Loading -->
      <div v-if="loading" class="text-center py-8">
        <div class="w-8 h-8 border-2 border-brand-red border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p class="text-zinc-400">Activating your account...</p>
      </div>
      
      <!-- Success -->
      <div v-else-if="success" class="text-center py-8">
        <div class="text-green-500 text-6xl mb-4">&#10003;</div>
        <h2 class="text-xl font-bold text-white mb-2">Account Activated!</h2>
        <p class="text-zinc-400 mb-6">Your email has been verified. You can now log in.</p>
        <button
          type="button"
          class="w-full bg-brand-red text-white py-4 font-black uppercase tracking-wider hover:bg-white hover:text-black transition-all"
          @click="$emit('go-login')"
        >
          Go to Login
        </button>
      </div>
      
      <!-- Error -->
      <div v-else-if="error && !showPasswordForm" class="text-center py-8">
        <div class="text-brand-red text-6xl mb-4">!</div>
        <h2 class="text-xl font-bold text-white mb-2">Activation Failed</h2>
        <p class="text-zinc-400 mb-6">{{ error }}</p>
        <button
          type="button"
          class="w-full border border-zinc-700 text-zinc-400 py-4 font-bold uppercase tracking-wider hover:border-white hover:text-white transition-all"
          @click="$emit('go-login')"
        >
          Back to Login
        </button>
      </div>
      
      <!-- Password Form -->
      <form v-else-if="showPasswordForm" class="space-y-6" @submit.prevent="handleSetPassword">
        <p class="text-zinc-400 text-sm text-center mb-6">
          Set a password to complete your account activation.
        </p>
        
        <div>
          <label class="block text-[10px] uppercase font-black text-zinc-500 mb-2 tracking-widest">New Password</label>
          <input
            v-model="newPassword"
            type="password"
            class="w-full bg-black border border-zinc-800 p-4 font-bold uppercase outline-none focus:border-brand-red text-white transition-all"
            placeholder="Min 6 characters"
          >
        </div>
        
        <div>
          <label class="block text-[10px] uppercase font-black text-zinc-500 mb-2 tracking-widest">Confirm Password</label>
          <input
            v-model="confirmPassword"
            type="password"
            class="w-full bg-black border border-zinc-800 p-4 font-bold uppercase outline-none focus:border-brand-red text-white transition-all"
          >
        </div>
        
        <div v-if="error" class="bg-brand-red/10 border border-brand-red/20 p-3 text-brand-red text-center text-sm">
          {{ error }}
        </div>
        
        <button
          type="submit"
          class="w-full bg-brand-red text-white py-4 font-black uppercase tracking-wider hover:bg-white hover:text-black transition-all"
        >
          Activate Account
        </button>
        
        <button
          type="button"
          class="w-full text-zinc-500 text-sm hover:text-white"
          @click="activateAccount()"
        >
          Skip - Activate without changing password
        </button>
      </form>
    </div>
  </div>
</template>
