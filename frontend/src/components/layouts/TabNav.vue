<script setup lang="ts">
import type { TabType } from '@/types'
import type { Activity } from '@/types'
import ActivityList from '@/components/features/activities/ActivityList.vue'

defineProps<{
  currentTab: TabType
  selectedActivityId: number | null
  activities: Activity[]
}>()

const emit = defineEmits<{
  (e: 'update:currentTab', value: TabType): void
  (e: 'select-activity', id: number | null): void
  (e: 'new-activity'): void
}>()
</script>

<template>
  <nav class="lg:col-span-2 space-y-2 shrink-0">
    <button
      type="button"
      class="w-full text-left px-6 py-4 font-black uppercase italic tracking-widest text-sm transition-all border-r-4 text-white"
      :class="currentTab === 'ACTIVITY' ? 'bg-industrial-gray border-brand-red' : 'border-transparent text-zinc-600 hover:text-zinc-400'"
      @click="emit('update:currentTab', 'ACTIVITY')"
    >
      Activiteit
    </button>
    <button
      type="button"
      class="w-full text-left px-6 py-4 font-black uppercase italic tracking-widest text-sm transition-all border-r-4 text-white"
      :class="currentTab === 'BALANCE' ? 'bg-industrial-gray border-brand-red' : 'border-transparent text-zinc-600 hover:text-zinc-400'"
      @click="emit('update:currentTab', 'BALANCE')"
    >
      Balans
    </button>
    <div class="pt-4">
      <ActivityList
        :activities="activities"
        :selected-id="selectedActivityId"
        @select="emit('select-activity', $event)"
        @new="emit('new-activity')"
      />
    </div>
  </nav>
</template>
