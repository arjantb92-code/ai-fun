<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAppStore } from '@/stores/appStore'
import BalanceListCard from './BalanceListCard.vue'
import BalanceListModal from './BalanceListModal.vue'
import JoinBalanceListModal from './JoinBalanceListModal.vue'
import type { BalanceList } from '@/types'

const store = useAppStore()

const isCreateModalOpen = ref(false)
const isJoinModalOpen = ref(false)

const handleSelect = (balanceList: BalanceList) => {
  store.selectBalanceList(balanceList.id)
  store.fetchData()
}

const handleCreate = async (data: { name: string; currency: string }) => {
  const result = await store.createBalanceList(data)
  if (result) {
    isCreateModalOpen.value = false
  }
}

const handleJoin = async (inviteCode: string) => {
  const result = await store.joinBalanceList(inviteCode)
  if (result.success) {
    isJoinModalOpen.value = false
    if (result.balanceList) {
      store.selectBalanceList(result.balanceList.id)
      store.fetchData()
    }
  }
  return result
}

onMounted(() => {
  store.fetchBalanceLists()
})
</script>

<template>
  <div class="min-h-screen bg-trainmore-dark text-white font-industrial">
    <div class="max-w-4xl mx-auto p-6 md:p-8">
      <header class="mb-8 text-center">
        <h1 class="text-4xl md:text-5xl font-black uppercase italic tracking-tight mb-2">
          Mijn Balansen
        </h1>
        <p class="text-gray-400 text-lg">
          Kies een balans om verder te gaan
        </p>
      </header>

      <div class="flex gap-4 justify-center mb-8">
        <button
          type="button"
          class="bg-brand-red text-white px-6 py-3 font-bold uppercase hover:bg-red-700 transition-all transform active:scale-95 italic text-sm"
          @click="isCreateModalOpen = true"
        >
          + Nieuwe Balans
        </button>
        <button
          type="button"
          class="border-2 border-white text-white px-6 py-3 font-bold uppercase hover:bg-white hover:text-black transition-all transform active:scale-95 italic text-sm"
          @click="isJoinModalOpen = true"
        >
          Uitnodiging Invoeren
        </button>
      </div>

      <div v-if="store.isLoading" class="text-center py-12">
        <div class="inline-block w-8 h-8 border-4 border-brand-red border-t-transparent rounded-full animate-spin"></div>
        <p class="mt-4 text-gray-400">Laden...</p>
      </div>

      <div v-else-if="store.balanceLists.length === 0" class="text-center py-12 bg-industrial-gray rounded-lg">
        <div class="text-6xl mb-4">📋</div>
        <h2 class="text-2xl font-bold mb-2">Geen balansen gevonden</h2>
        <p class="text-gray-400 mb-6">Maak je eerste balans aan of voeg een uitnodigingscode in.</p>
      </div>

      <div v-else class="grid gap-4 md:grid-cols-2">
        <BalanceListCard
          v-for="bl in store.balanceLists"
          :key="bl.id"
          :balance-list="bl"
          @select="handleSelect(bl)"
        />
      </div>
    </div>

    <BalanceListModal
      :is-open="isCreateModalOpen"
      @close="isCreateModalOpen = false"
      @save="handleCreate"
    />

    <JoinBalanceListModal
      :is-open="isJoinModalOpen"
      @close="isJoinModalOpen = false"
      @join="handleJoin"
    />
  </div>
</template>
