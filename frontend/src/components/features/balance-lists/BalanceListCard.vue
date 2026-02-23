<script setup lang="ts">
import type { BalanceList } from '@/types'

defineProps<{
  balanceList: BalanceList
}>()

const emit = defineEmits<{
  (e: 'select'): void
}>()

const formatCurrency = (amount: number, currency: string) => {
  return new Intl.NumberFormat('nl-NL', {
    style: 'currency',
    currency: currency || 'EUR'
  }).format(amount)
}

const getBalanceClass = (balance: number) => {
  if (balance > 0.01) return 'text-green-400'
  if (balance < -0.01) return 'text-brand-red'
  return 'text-gray-400'
}
</script>

<template>
  <button
    type="button"
    class="bg-industrial-gray p-6 rounded-lg text-left hover:bg-gray-800 transition-all transform hover:scale-[1.02] active:scale-[0.98] border border-transparent hover:border-brand-red w-full"
    @click="emit('select')"
  >
    <div class="flex justify-between items-start mb-4">
      <div>
        <h3 class="text-xl font-bold uppercase italic">{{ balanceList.name }}</h3>
        <span class="text-sm text-gray-400">{{ balanceList.currency }}</span>
      </div>
      <span
        v-if="balanceList.my_role === 'owner'"
        class="text-xs bg-brand-red px-2 py-1 rounded uppercase font-bold"
      >
        Eigenaar
      </span>
    </div>

    <div class="grid grid-cols-2 gap-4 text-sm">
      <div>
        <span class="text-gray-400 block">Deelnemers</span>
        <span class="text-lg font-bold">{{ balanceList.member_count }}</span>
      </div>
      <div>
        <span class="text-gray-400 block">Transacties</span>
        <span class="text-lg font-bold">{{ balanceList.total_transactions || 0 }}</span>
      </div>
      <div>
        <span class="text-gray-400 block">Totaal</span>
        <span class="text-lg font-bold">
          {{ formatCurrency(balanceList.total_amount || 0, balanceList.currency) }}
        </span>
      </div>
      <div>
        <span class="text-gray-400 block">Mijn Balans</span>
        <span
          class="text-lg font-bold"
          :class="getBalanceClass(balanceList.my_balance || 0)"
        >
          {{ formatCurrency(balanceList.my_balance || 0, balanceList.currency) }}
        </span>
      </div>
    </div>
  </button>
</template>
