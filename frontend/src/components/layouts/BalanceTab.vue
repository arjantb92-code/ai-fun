<script setup lang="ts">
import { useAppStore } from '@/stores/appStore'
import BalanceCard from '@/components/features/balance/BalanceCard.vue'
import SettlementPlan from '@/components/features/balance/SettlementPlan.vue'
import SettlementHistory from '@/components/features/balance/SettlementHistory.vue'

const store = useAppStore()

const props = defineProps<{
  settleLoading: boolean
  selectedActivityId: number | null
}>()

const emit = defineEmits<{
  (e: 'settle'): void
  (e: 'restore', sessionId: number): void
  (e: 'delete', sessionId: number): void
  (e: 'delete-permanent', sessionId: number): void
}>()

const selectedActivityLabel = () => {
  const info = store.getActivityInfo(props.selectedActivityId)
  return info ? info.name : null
}
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-12 animate-in fade-in slide-in-from-right-4 duration-500 text-white">
    <div class="space-y-8">
      <BalanceCard :balance="store.totalGroupSpend" label="Huidige Groepsbalans" />
      <div class="bg-industrial-gray p-8 shadow-xl">
        <h3 class="text-xs uppercase font-black mb-8 tracking-[0.2em] border-b border-zinc-800 pb-2 text-brand-red">Status per persoon</h3>
        <div class="space-y-6">
          <div v-for="u in store.groupMembers" :key="u.id" class="flex items-center justify-between group">
            <div class="flex items-center gap-4">
              <img :src="u.avatar_url || ''" class="w-12 h-12 border border-zinc-800 grayscale object-cover" @error="(e) => (e.target as HTMLImageElement).style.display = 'none'">
              <span class="text-lg font-black uppercase italic tracking-tight">{{ u.name }}</span>
            </div>
            <div class="text-2xl font-black italic tracking-tighter" :class="store.getBalanceForUser(u.id) >= 0 ? 'text-zinc-400' : 'text-brand-red'">
              {{ store.getBalanceForUser(u.id) >= 0 ? '+' : '' }}{{ store.getBalanceForUser(u.id).toFixed(2) }}
            </div>
          </div>
        </div>
      </div>
      <SettlementPlan
        :settlements="store.settlementsSuggestions"
        :activity-name="selectedActivityLabel()"
        :loading="settleLoading"
        @settle="emit('settle')"
      />
      <SettlementHistory
        :history="store.settlementHistory"
        @restore="emit('restore', $event)"
        @delete="emit('delete', $event)"
        @delete-permanent="emit('delete-permanent', $event)"
      />
    </div>
  </div>
</template>
