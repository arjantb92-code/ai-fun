<script setup>
const props = defineProps({
  activities: Array,
  selectedId: [Number, String, null],
  showNone: { type: Boolean, default: true }
})

const emit = defineEmits(['update:selectedId'])

const updateSelection = (id) => {
  emit('update:selectedId', id === 'null' ? null : id)
}
</script>

<template>
  <select 
    :value="selectedId === null ? 'null' : selectedId"
    @change="updateSelection($event.target.value)"
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
