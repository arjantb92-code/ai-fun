<script setup lang="ts">
import { computed } from 'vue'
import type { Activity } from '@/types'

interface Props {
  activities: Activity[]
  selectedId: number | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'select', id: number | null): void
  (e: 'new'): void
  (e: 'edit', activity: Activity): void
}>()

const activeActivities = computed(() => props.activities.filter(a => a.is_active))
const archivedActivities = computed(() => props.activities.filter(a => !a.is_active))

const selectActivity = (id: number | null): void => {
  emit('select', id === props.selectedId ? null : id)
}
</script>

<template>
  <div class="space-y-2">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-xs uppercase font-black tracking-[0.2em] border-b border-zinc-800 pb-2 text-brand-red">Activiteiten</h3>
      <button @click="$emit('new')" class="text-zinc-600 hover:text-brand-red text-xl leading-none">+</button>
    </div>
    <button 
      @click="selectActivity(null)"
      class="w-full text-left px-4 py-3 font-black uppercase italic tracking-widest text-xs transition-all border-l-4 text-white"
      :class="selectedId === null ? 'bg-industrial-gray border-brand-red' : 'border-transparent text-zinc-600 hover:text-zinc-400'"
    >
      Alle transacties
    </button>
    <div
      v-for="a in activeActivities"
      :key="a.id"
      class="group relative flex items-center border-l-4 transition-all"
      :class="selectedId === a.id ? 'bg-industrial-gray border-brand-red' : 'border-transparent hover:border-zinc-700'"
    >
      <button
        type="button"
        @click="selectActivity(a.id)"
        class="flex-1 text-left px-4 py-3 font-black uppercase italic tracking-widest text-xs transition-all"
        :class="selectedId === a.id ? 'text-white' : 'text-zinc-600 hover:text-zinc-400'"
      >
        <div class="flex items-center justify-between pr-5">
          <span>{{ a.icon || '📋' }} {{ a.name }}</span>
          <span class="text-[10px] text-zinc-500">{{ a.transaction_count || 0 }}</span>
        </div>
        <div v-if="a.total_amount" class="text-[10px] text-zinc-500 mt-1">€{{ a.total_amount.toFixed(2) }}</div>
      </button>
      <button
        type="button"
        class="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 text-zinc-600 hover:text-brand-red transition-all p-1"
        title="Bewerken"
        @click.stop="$emit('edit', a)"
      >
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536M9 13l6.586-6.586a2 2 0 112.828 2.828L11.828 15.828a2 2 0 01-1.414.586H8v-2.414a2 2 0 01.586-1.414z" />
        </svg>
      </button>
    </div>
    <div v-if="archivedActivities.length > 0" class="pt-4 border-t border-zinc-800 mt-4">
      <div class="text-[10px] uppercase font-black tracking-widest text-zinc-600 mb-2">Gearchiveerd</div>
      <button 
        v-for="a in archivedActivities" 
        :key="a.id"
        class="w-full text-left px-4 py-2 text-xs text-zinc-600 opacity-50"
      >
        {{ a.icon || '📋' }} {{ a.name }}
      </button>
    </div>
  </div>
</template>
