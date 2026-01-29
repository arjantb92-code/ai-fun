<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  settlements: {
    type: Array,
    required: true
  },
  activityName: {
    type: String,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['settle'])

// Tikkie integration state
const tikkieStatus = ref({ enabled: false, demo_mode: true })
const tikkieLoading = ref({})
const tikkieLinks = ref({})

onMounted(async () => {
  await fetchTikkieStatus()
})

async function fetchTikkieStatus() {
  try {
    const token = localStorage.getItem('wbw_token')
    const res = await fetch('http://localhost:5001/payments/tikkie/status', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      tikkieStatus.value = await res.json()
    }
  } catch (e) {
    console.error('Failed to fetch Tikkie status:', e)
  }
}

function getSettlementKey(s) {
  return `${s.from_user_id}_${s.to_user_id}`
}

async function createTikkieLink(settlement) {
  // Note: For unsaved settlements (before commit), we can't create Tikkie links
  // This function is a placeholder for future implementation when settlement IDs are available
  const key = getSettlementKey(settlement)
  tikkieLoading.value[key] = true
  
  try {
    // For now, show a demo message
    alert(`Tikkie wordt beschikbaar na het afrekenen.\n\nNa afrekenen kun je voor elke betaling een Tikkie link aanmaken.`)
  } finally {
    tikkieLoading.value[key] = false
  }
}

function copyToClipboard(url) {
  navigator.clipboard.writeText(url)
  alert('Link gekopieerd!')
}
</script>

<template>
  <div class="bg-black/40 border border-brand-red/20 p-8 shadow-xl space-y-6">
    <div class="flex items-center justify-between">
      <h3 class="text-xs uppercase text-brand-red font-black tracking-[0.2em] italic">Betaalvoorstel</h3>
      <div v-if="tikkieStatus.enabled" class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full" :class="tikkieStatus.demo_mode ? 'bg-yellow-500' : 'bg-green-500'"></span>
        <span class="text-[9px] uppercase tracking-wider text-zinc-500">
          Tikkie {{ tikkieStatus.demo_mode ? 'Demo' : 'Actief' }}
        </span>
      </div>
    </div>
    
    <template v-if="settlements.length > 0">
      <div v-for="(s, idx) in settlements" :key="idx" 
           class="border-l border-zinc-800 pl-4 py-3 mb-4 group">
        <div class="text-[11px] font-black uppercase tracking-widest">
          <span class="text-white">{{ s.from_user }}</span> 
          <span class="text-zinc-600 mx-1">➜</span> 
          <span class="text-brand-red">{{ s.to_user }}</span>
        </div>
        <div class="text-lg italic text-white mt-1">€ {{ s.amount.toFixed(2) }}</div>
        
        <!-- Tikkie placeholder - shown after hover -->
        <div class="mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
          <div class="flex items-center gap-2">
            <button 
              @click.stop="createTikkieLink(s)"
              :disabled="tikkieLoading[getSettlementKey(s)]"
              class="text-[9px] font-bold uppercase tracking-wider px-3 py-1.5 bg-[#00A0DF] text-white hover:bg-[#0090CF] transition-colors disabled:opacity-50"
            >
              <span v-if="tikkieLoading[getSettlementKey(s)]">Laden...</span>
              <span v-else>💸 Tikkie na afrekening</span>
            </button>
          </div>
        </div>
      </div>
      
      <!-- Info box about Tikkie -->
      <div v-if="tikkieStatus.enabled" class="bg-zinc-900/50 border border-zinc-800 p-4 text-[10px] text-zinc-500">
        <p class="font-bold uppercase tracking-wider mb-1">💡 Tip: iDEAL / Tikkie</p>
        <p>Na het afrekenen kun je voor elke betaling een Tikkie link aanmaken. De ontvanger kan dan direct via iDEAL betalen.</p>
        <p v-if="tikkieStatus.demo_mode" class="text-yellow-500/70 mt-2">
          Demo modus actief - configureer TIKKIE_API_KEY voor echte betalingen.
        </p>
      </div>
      
      <button 
        @click="emit('settle')"
        :disabled="loading"
        class="w-full py-4 font-black uppercase italic bg-brand-red text-white hover:bg-red-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {{ loading ? 'Bezig...' : (activityName ? `Afrekenen: ${activityName}` : 'Alles afrekenen') }}
      </button>
    </template>
    <p v-else class="text-zinc-500 text-sm italic">Geen openstaande stand. Alles is vereffend.</p>
  </div>
</template>
