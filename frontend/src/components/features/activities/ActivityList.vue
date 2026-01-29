<script setup>
const props = defineProps({
  activities: Array,
  selectedId: [Number, String, null]
})

const emit = defineEmits(['select', 'new', 'archive'])

const selectActivity = (id) => {
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
    <button 
      v-for="a in activities.filter(a => a.is_active)" 
      :key="a.id"
      @click="selectActivity(a.id)"
      class="w-full text-left px-4 py-3 font-black uppercase italic tracking-widest text-xs transition-all border-l-4 text-white group"
      :class="selectedId === a.id ? 'bg-industrial-gray border-brand-red' : 'border-transparent text-zinc-600 hover:text-zinc-400'"
    >
      <div class="flex items-center justify-between">
        <span>{{ a.icon || '📋' }} {{ a.name }}</span>
        <span class="text-[10px] text-zinc-500">{{ a.transaction_count || 0 }}</span>
      </div>
      <div v-if="a.total_amount" class="text-[10px] text-zinc-500 mt-1">€{{ a.total_amount.toFixed(2) }}</div>
    </button>
    <div v-if="activities.filter(a => !a.is_active).length > 0" class="pt-4 border-t border-zinc-800 mt-4">
      <div class="text-[10px] uppercase font-black tracking-widest text-zinc-600 mb-2">Gearchiveerd</div>
      <button 
        v-for="a in activities.filter(a => !a.is_active)" 
        :key="a.id"
        class="w-full text-left px-4 py-2 text-xs text-zinc-600 opacity-50"
      >
        {{ a.icon || '📋' }} {{ a.name }}
      </button>
    </div>
  </div>
</template>
