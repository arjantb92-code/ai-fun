<script setup>
import { ref, onMounted, watch } from 'vue'

const props = defineProps({
  history: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['undo', 'restore', 'delete', 'delete-permanent'])

const expandedIds = ref(new Set())
const tikkieStatus = ref({ enabled: false, demo_mode: true })
const sessionPayments = ref({})  // sessionId -> payments data
const loadingPayments = ref({})  // settlementId -> loading state
const creatingTikkie = ref({})   // settlementId -> creating state

onMounted(async () => {
  await fetchTikkieStatus()
})

watch(() => props.history, async (newHistory) => {
  // Fetch payment data for any expanded sessions
  for (const sessionId of expandedIds.value) {
    await fetchSessionPayments(sessionId)
  }
}, { deep: true })

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

async function fetchSessionPayments(sessionId) {
  try {
    const token = localStorage.getItem('wbw_token')
    const res = await fetch(`http://localhost:5001/settlements/history/${sessionId}/payments`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      sessionPayments.value[sessionId] = await res.json()
    }
  } catch (e) {
    console.error('Failed to fetch session payments:', e)
  }
}

function togglePosten(sessionId) {
  if (expandedIds.value.has(sessionId)) {
    expandedIds.value.delete(sessionId)
  } else {
    expandedIds.value.add(sessionId)
    // Fetch payment data when expanding
    fetchSessionPayments(sessionId)
  }
  expandedIds.value = new Set(expandedIds.value)
}

async function createTikkieLink(sessionId, settlementId) {
  creatingTikkie.value[settlementId] = true
  
  try {
    const token = localStorage.getItem('wbw_token')
    const res = await fetch('http://localhost:5001/payments/tikkie/create', {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ settlement_id: settlementId })
    })
    
    if (res.ok) {
      const data = await res.json()
      // Refresh the session payments to show the new link
      await fetchSessionPayments(sessionId)
      
      // Show the Tikkie URL
      if (data.payment_request?.tikkie_url) {
        const demoNote = data.payment_request.is_demo ? '\n\n⚠️ Dit is een demo link (geen echte betaling)' : ''
        if (confirm(`Tikkie link aangemaakt!${demoNote}\n\nURL: ${data.payment_request.tikkie_url}\n\nKopiëren naar klembord?`)) {
          navigator.clipboard.writeText(data.payment_request.tikkie_url)
        }
      }
    } else {
      const err = await res.json().catch(() => ({}))
      alert(err.error || 'Tikkie aanmaken mislukt')
    }
  } catch (e) {
    console.error('Failed to create Tikkie link:', e)
    alert('Tikkie aanmaken mislukt')
  } finally {
    creatingTikkie.value[settlementId] = false
  }
}

async function checkTikkieStatus(sessionId, paymentId) {
  loadingPayments.value[paymentId] = true
  
  try {
    const token = localStorage.getItem('wbw_token')
    const res = await fetch(`http://localhost:5001/payments/tikkie/${paymentId}/check`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    
    if (res.ok) {
      // Refresh the session payments to show updated status
      await fetchSessionPayments(sessionId)
    }
  } catch (e) {
    console.error('Failed to check Tikkie status:', e)
  } finally {
    loadingPayments.value[paymentId] = false
  }
}

function copyToClipboard(url) {
  navigator.clipboard.writeText(url)
  alert('Link gekopieerd naar klembord!')
}

function openTikkieLink(url) {
  window.open(url, '_blank')
}

function formatDate(d, time) {
  if (!d) return ''
  const opts = { day: 'numeric', month: 'short', year: 'numeric' }
  const str = new Date(d).toLocaleDateString('nl-NL', opts)
  if (time) return `${str} ${time}`
  return str
}

function getSettlementPaymentInfo(sessionId, settlementId) {
  const data = sessionPayments.value[sessionId]
  if (!data?.settlements) return null
  return data.settlements.find(s => s.settlement_id === settlementId)
}
</script>

<template>
  <div class="bg-industrial-gray border border-zinc-800 p-8 shadow-xl">
    <div class="flex items-center justify-between mb-6">
      <h3 class="text-xs uppercase font-black tracking-[0.2em] border-b border-zinc-800 pb-2 text-brand-red">Afrekeningen</h3>
      <div v-if="tikkieStatus.enabled" class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full" :class="tikkieStatus.demo_mode ? 'bg-yellow-500' : 'bg-green-500'"></span>
        <span class="text-[9px] uppercase tracking-wider text-zinc-500">
          Tikkie {{ tikkieStatus.demo_mode ? 'Demo' : 'Actief' }}
        </span>
      </div>
    </div>
    
    <template v-if="history.length > 0">
      <div v-for="s in history" :key="s.id" class="border-b border-zinc-800/50 pb-6 mb-6 last:border-0 last:mb-0 last:pb-0">
        <div class="flex justify-between items-baseline mb-2">
          <span class="text-sm font-black uppercase italic text-white">{{ s.description || 'Afrekening' }}</span>
          <span class="text-[10px] text-zinc-500">{{ s.date ? new Date(s.date).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short', year: 'numeric' }) : '' }}</span>
        </div>
        <div class="text-[10px] text-zinc-500 mb-2">Totaal: € {{ (s.total_amount || 0).toFixed(2) }}</div>
        
        <!-- Settlement results with Tikkie integration -->
        <div v-for="(r, idx) in (s.results || [])" :key="idx" class="mb-3 last:mb-0">
          <div class="text-[11px] font-black uppercase tracking-widest border-l border-zinc-700 pl-3 py-1">
            <span class="text-zinc-400">{{ r.from_user }}</span>
            <span class="text-zinc-600 mx-1">➜</span>
            <span class="text-brand-red">{{ r.to_user }}</span>
            <span class="text-white ml-2">€ {{ (r.amount || 0).toFixed(2) }}</span>
          </div>
          
          <!-- Tikkie payment section (only for non-deleted settlements) -->
          <div v-if="!s.deleted_at && tikkieStatus.enabled && expandedIds.has(s.id)" class="ml-3 mt-2">
            <template v-if="getSettlementPaymentInfo(s.id, r.settlement_id)">
              <div class="bg-zinc-900/50 border border-zinc-800 p-3 rounded">
                <template v-if="getSettlementPaymentInfo(s.id, r.settlement_id)?.active_payment">
                  <div class="flex items-center gap-2 flex-wrap">
                    <span class="text-[9px] uppercase tracking-wider" :class="{
                      'text-yellow-500': getSettlementPaymentInfo(s.id, r.settlement_id).active_payment.is_demo,
                      'text-green-500': getSettlementPaymentInfo(s.id, r.settlement_id).active_payment.status === 'PAID',
                      'text-blue-400': getSettlementPaymentInfo(s.id, r.settlement_id).active_payment.status === 'OPEN'
                    }">
                      {{ getSettlementPaymentInfo(s.id, r.settlement_id).active_payment.is_demo ? '🔶 Demo' : 
                         getSettlementPaymentInfo(s.id, r.settlement_id).active_payment.status === 'PAID' ? '✅ Betaald' : '⏳ Wacht op betaling' }}
                    </span>
                    <button
                      @click="copyToClipboard(getSettlementPaymentInfo(s.id, r.settlement_id).active_payment.tikkie_url)"
                      class="text-[9px] font-bold uppercase tracking-wider px-2 py-1 bg-zinc-800 text-zinc-400 hover:text-white transition-colors"
                    >
                      📋 Kopieer link
                    </button>
                    <button
                      @click="openTikkieLink(getSettlementPaymentInfo(s.id, r.settlement_id).active_payment.tikkie_url)"
                      class="text-[9px] font-bold uppercase tracking-wider px-2 py-1 bg-[#00A0DF] text-white hover:bg-[#0090CF] transition-colors"
                    >
                      🔗 Open Tikkie
                    </button>
                    <button
                      v-if="!getSettlementPaymentInfo(s.id, r.settlement_id).active_payment.is_demo && getSettlementPaymentInfo(s.id, r.settlement_id).active_payment.status !== 'PAID'"
                      @click="checkTikkieStatus(s.id, getSettlementPaymentInfo(s.id, r.settlement_id).active_payment.id)"
                      :disabled="loadingPayments[getSettlementPaymentInfo(s.id, r.settlement_id).active_payment.id]"
                      class="text-[9px] font-bold uppercase tracking-wider px-2 py-1 bg-zinc-700 text-zinc-300 hover:bg-zinc-600 transition-colors disabled:opacity-50"
                    >
                      🔄 Check status
                    </button>
                  </div>
                </template>
                <template v-else-if="getSettlementPaymentInfo(s.id, r.settlement_id)?.is_paid">
                  <span class="text-[9px] uppercase tracking-wider text-green-500">✅ Betaald via Tikkie</span>
                </template>
                <template v-else>
                  <button
                    @click="createTikkieLink(s.id, r.settlement_id)"
                    :disabled="creatingTikkie[r.settlement_id]"
                    class="text-[9px] font-bold uppercase tracking-wider px-3 py-1.5 bg-[#00A0DF] text-white hover:bg-[#0090CF] transition-colors disabled:opacity-50"
                  >
                    <span v-if="creatingTikkie[r.settlement_id]">Laden...</span>
                    <span v-else>💸 Maak Tikkie</span>
                  </button>
                </template>
              </div>
            </template>
            <template v-else>
              <button
                @click="createTikkieLink(s.id, r.settlement_id)"
                :disabled="creatingTikkie[r.settlement_id]"
                class="text-[9px] font-bold uppercase tracking-wider px-3 py-1.5 bg-[#00A0DF] text-white hover:bg-[#0090CF] transition-colors disabled:opacity-50"
              >
                <span v-if="creatingTikkie[r.settlement_id]">Laden...</span>
                <span v-else>💸 Maak Tikkie</span>
              </button>
            </template>
          </div>
        </div>
        
        <div class="mt-3 flex flex-wrap gap-2">
          <button
            v-if="(s.transactions || []).length > 0"
            type="button"
            class="text-[11px] font-bold uppercase tracking-wider text-zinc-400 hover:text-brand-red transition-colors"
            @click="togglePosten(s.id)"
          >
            {{ expandedIds.has(s.id) ? 'Verberg details' : 'Toon details' }} ({{ s.transactions.length }})
          </button>
          <button
            v-else-if="!s.deleted_at && tikkieStatus.enabled"
            type="button"
            class="text-[11px] font-bold uppercase tracking-wider text-zinc-400 hover:text-[#00A0DF] transition-colors"
            @click="togglePosten(s.id)"
          >
            {{ expandedIds.has(s.id) ? 'Verberg Tikkie' : '💸 Tikkie opties' }}
          </button>
        </div>
        
        <div v-if="expandedIds.has(s.id) && (s.transactions || []).length" class="mt-3 pl-3 border-l-2 border-zinc-700 space-y-2">
          <div
            v-for="tx in s.transactions"
            :key="tx.id"
            class="flex flex-wrap items-baseline gap-x-2 gap-y-0.5 text-[11px] text-zinc-300"
          >
            <span class="truncate min-w-0 flex-1">{{ tx.description }}</span>
            <span class="text-zinc-500 shrink-0">{{ formatDate(tx.date, tx.time) }}</span>
            <span class="text-zinc-400 shrink-0">{{ tx.payer || '—' }}</span>
            <span class="text-white font-semibold shrink-0">€ {{ (tx.amount || 0).toFixed(2) }}</span>
          </div>
        </div>
        <p v-else-if="expandedIds.has(s.id) && (!s.transactions || !s.transactions.length)" class="text-[11px] text-zinc-500 italic mt-2">Geen posten bij deze afrekening.</p>
        
        <div v-if="!s.deleted_at" class="mt-3 flex gap-2">
          <button
            type="button"
            class="text-[10px] font-bold uppercase tracking-wider text-zinc-500 hover:text-brand-red transition-colors"
            @click="emit('delete', s.id)"
          >
            Ongedaan maken
          </button>
        </div>
        <div v-else class="mt-3 flex gap-2">
          <button
            type="button"
            class="text-[10px] font-bold uppercase tracking-wider text-zinc-400 hover:text-white transition-colors"
            @click="emit('restore', s.id)"
          >
            Herstel
          </button>
          <span class="text-zinc-600">·</span>
          <button
            type="button"
            class="text-[10px] font-bold uppercase tracking-wider text-zinc-500 hover:text-brand-red transition-colors"
            @click="emit('delete-permanent', s.id)"
          >
            Definitief verwijderen
          </button>
        </div>
      </div>
    </template>
    <p v-else class="text-zinc-500 text-sm italic">Nog geen afrekeningen.</p>
  </div>
</template>
