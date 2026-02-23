<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { API_BASE } from '@/config/api'

interface BalanceListPreview {
  id: number
  name: string
  currency: string
  member_count: number
  created_by_name: string | null
}

interface Props {
  inviteCode: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'login', credentials: { username: string; password: string }): void
  (e: 'register', data: { name: string; email: string; password: string; invite_code: string }): void
  (e: 'google-login', inviteCode: string): void
}>()

const preview = ref<BalanceListPreview | null>(null)
const loading = ref(true)
const error = ref('')
const mode = ref<'choice' | 'login' | 'register'>('choice')

const loginForm = ref({ username: '', password: '' })
const registerForm = ref({ name: '', email: '', password: '', confirmPassword: '' })
const formError = ref('')

const passwordsMatch = computed(() => 
  registerForm.value.password === registerForm.value.confirmPassword
)

const fetchPreview = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await fetch(`${API_BASE}/balance-lists/public-preview/${props.inviteCode}`)
    if (res.ok) {
      preview.value = await res.json()
    } else {
      const data = await res.json()
      error.value = data.error || 'Invalid invite link'
    }
  } catch {
    error.value = 'Could not connect to server'
  } finally {
    loading.value = false
  }
}

const handleLogin = () => {
  formError.value = ''
  if (!loginForm.value.username || !loginForm.value.password) {
    formError.value = 'Please fill in all fields'
    return
  }
  emit('login', loginForm.value)
}

const handleRegister = () => {
  formError.value = ''
  if (!registerForm.value.name || !registerForm.value.email || !registerForm.value.password) {
    formError.value = 'Please fill in all fields'
    return
  }
  if (registerForm.value.password.length < 6) {
    formError.value = 'Password must be at least 6 characters'
    return
  }
  if (!passwordsMatch.value) {
    formError.value = 'Passwords do not match'
    return
  }
  emit('register', {
    name: registerForm.value.name,
    email: registerForm.value.email,
    password: registerForm.value.password,
    invite_code: props.inviteCode
  })
}

const handleGoogleLogin = () => {
  emit('google-login', props.inviteCode)
}

onMounted(fetchPreview)
</script>

<template>
  <div class="fixed inset-0 z-[100] bg-black flex items-center justify-center p-4">
    <div class="absolute inset-0 opacity-10">
      <div class="absolute inset-0" style="background-image: radial-gradient(circle at 50% 50%, #E30613 0%, transparent 70%);"></div>
    </div>
    
    <div class="relative z-10 w-full max-w-md bg-industrial-gray border border-zinc-800 shadow-2xl">
      <div class="h-1 bg-brand-red absolute top-0 left-0 right-0 shadow-[0_0_15px_rgba(227,6,19,0.3)]"></div>
      
      <!-- Loading State -->
      <div v-if="loading" class="p-10 text-center">
        <div class="w-8 h-8 border-2 border-brand-red border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p class="text-zinc-400 text-sm uppercase tracking-widest">Loading...</p>
      </div>
      
      <!-- Error State -->
      <div v-else-if="error" class="p-10 text-center">
        <div class="text-brand-red text-6xl mb-4">!</div>
        <h2 class="text-xl font-black uppercase text-white mb-2">Invalid Link</h2>
        <p class="text-zinc-400 text-sm">{{ error }}</p>
      </div>
      
      <!-- Preview + Actions -->
      <template v-else-if="preview">
        <!-- Balance List Preview -->
        <div class="p-8 border-b border-zinc-800">
          <p class="text-[10px] text-zinc-500 uppercase font-black tracking-[0.3em] mb-2">You're invited to join</p>
          <h1 class="text-3xl font-black uppercase italic text-white mb-2">{{ preview.name }}</h1>
          <div class="flex items-center gap-4 text-sm text-zinc-400">
            <span class="flex items-center gap-1">
              <span class="text-brand-red">{{ preview.member_count }}</span> members
            </span>
            <span class="text-zinc-600">|</span>
            <span>{{ preview.currency }}</span>
          </div>
          <p v-if="preview.created_by_name" class="text-xs text-zinc-500 mt-2">
            Created by {{ preview.created_by_name }}
          </p>
        </div>
        
        <!-- Choice Mode -->
        <div v-if="mode === 'choice'" class="p-8 space-y-4">
          <p class="text-center text-zinc-400 text-sm mb-6">
            Log in or create an account to join this balance list
          </p>
          
          <!-- Google Sign-In -->
          <button
            type="button"
            class="w-full bg-white text-black py-4 font-bold uppercase tracking-wider hover:bg-zinc-200 transition-all flex items-center justify-center gap-3"
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
          
          <div class="relative my-6">
            <div class="absolute inset-0 flex items-center">
              <div class="w-full border-t border-zinc-700"></div>
            </div>
            <div class="relative flex justify-center text-xs uppercase">
              <span class="bg-industrial-gray px-3 text-zinc-500 font-black tracking-widest">or</span>
            </div>
          </div>
          
          <button
            type="button"
            class="w-full border-2 border-brand-red text-brand-red py-4 font-bold uppercase tracking-wider hover:bg-brand-red hover:text-white transition-all"
            @click="mode = 'login'"
          >
            Log In with Email
          </button>
          
          <button
            type="button"
            class="w-full border border-zinc-700 text-zinc-400 py-4 font-bold uppercase tracking-wider hover:border-zinc-500 hover:text-white transition-all"
            @click="mode = 'register'"
          >
            Create Account
          </button>
        </div>
        
        <!-- Login Form -->
        <form v-else-if="mode === 'login'" class="p-8 space-y-4" @submit.prevent="handleLogin">
          <button type="button" class="text-zinc-500 hover:text-white text-sm mb-4" @click="mode = 'choice'">&larr; Back</button>
          
          <div>
            <label class="block text-[10px] uppercase font-black text-zinc-500 mb-2 tracking-widest">Email / Username</label>
            <input
              v-model="loginForm.username"
              type="text"
              class="w-full bg-black border border-zinc-800 p-4 font-bold uppercase outline-none focus:border-brand-red text-white transition-all"
              placeholder="your@email.com"
            >
          </div>
          
          <div>
            <label class="block text-[10px] uppercase font-black text-zinc-500 mb-2 tracking-widest">Password</label>
            <input
              v-model="loginForm.password"
              type="password"
              class="w-full bg-black border border-zinc-800 p-4 font-bold uppercase outline-none focus:border-brand-red text-white transition-all"
              placeholder="********"
            >
          </div>
          
          <div v-if="formError" class="bg-brand-red/10 border border-brand-red/20 p-3 text-brand-red text-center text-sm">
            {{ formError }}
          </div>
          
          <button
            type="submit"
            class="w-full bg-brand-red text-white py-4 font-black uppercase tracking-wider hover:bg-white hover:text-black transition-all"
          >
            Log In & Join
          </button>
        </form>
        
        <!-- Register Form -->
        <form v-else-if="mode === 'register'" class="p-8 space-y-4" @submit.prevent="handleRegister">
          <button type="button" class="text-zinc-500 hover:text-white text-sm mb-4" @click="mode = 'choice'">&larr; Back</button>
          
          <div>
            <label class="block text-[10px] uppercase font-black text-zinc-500 mb-2 tracking-widest">Name</label>
            <input
              v-model="registerForm.name"
              type="text"
              class="w-full bg-black border border-zinc-800 p-4 font-bold uppercase outline-none focus:border-brand-red text-white transition-all"
              placeholder="Your Name"
            >
          </div>
          
          <div>
            <label class="block text-[10px] uppercase font-black text-zinc-500 mb-2 tracking-widest">Email</label>
            <input
              v-model="registerForm.email"
              type="email"
              class="w-full bg-black border border-zinc-800 p-4 font-bold outline-none focus:border-brand-red text-white transition-all"
              placeholder="your@email.com"
            >
          </div>
          
          <div>
            <label class="block text-[10px] uppercase font-black text-zinc-500 mb-2 tracking-widest">Password</label>
            <input
              v-model="registerForm.password"
              type="password"
              class="w-full bg-black border border-zinc-800 p-4 font-bold uppercase outline-none focus:border-brand-red text-white transition-all"
              placeholder="Min 6 characters"
            >
          </div>
          
          <div>
            <label class="block text-[10px] uppercase font-black text-zinc-500 mb-2 tracking-widest">Confirm Password</label>
            <input
              v-model="registerForm.confirmPassword"
              type="password"
              class="w-full bg-black border border-zinc-800 p-4 font-bold uppercase outline-none focus:border-brand-red text-white transition-all"
              :class="{ 'border-brand-red': registerForm.confirmPassword && !passwordsMatch }"
              placeholder="********"
            >
          </div>
          
          <div v-if="formError" class="bg-brand-red/10 border border-brand-red/20 p-3 text-brand-red text-center text-sm">
            {{ formError }}
          </div>
          
          <button
            type="submit"
            class="w-full bg-brand-red text-white py-4 font-black uppercase tracking-wider hover:bg-white hover:text-black transition-all"
          >
            Create Account & Join
          </button>
          
          <p class="text-[10px] text-zinc-500 text-center">
            By creating an account, you'll receive an activation email for future logins.
          </p>
        </form>
      </template>
      
      <!-- Footer -->
      <div class="p-4 border-t border-zinc-800 text-center">
        <p class="text-[8px] text-zinc-600 font-black uppercase tracking-widest">
          Better WBW - Zero-Sum Expense Management
        </p>
      </div>
    </div>
  </div>
</template>
