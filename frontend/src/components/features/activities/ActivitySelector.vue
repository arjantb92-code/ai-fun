<script setup lang="ts">
import type { Activity } from '@/types'

interface Props {
  activities: Activity[]
  selectedId: number | string | null
  showNone?: boolean
}

withDefaults(defineProps<Props>(), {
  showNone: true
})

const emit = defineEmits<{
  (e: 'update:selectedId', id: number | null): void
}>()

const updateSelection = (value: string): void => {
  emit('update:selectedId', value === 'null' ? null : Number(value))
}
</script>

<template>
  <select 
    :value="selectedId === null ? 'null' : selectedId"
    @change="updateSelection(($event.target as HTMLSelectElement).value)"
    class="w-full bg-zinc-900 border border-zinc-800 p-3 font-black uppercase tracking-widest text-xs outline-none text-white italic focus:border-brand-red appearance-none cursor-pointer"
  >
    <option v-if="showNone" value="null">Geen activiteit</option>
    <option 
      v-for="a in activities.filter(a => a.is_active)" 
      :key="a.id" 
      :value="a.id"
    >
      {{ a.icon || '📋' }} {{ a.name }}
    </option>
  </select>
</template>
