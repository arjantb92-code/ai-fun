<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Activity, ActivityFormData } from '@/types'

interface Props {
  isOpen: boolean
  activity: Activity | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', data: ActivityFormData): void
}>()

const name = ref('')
const description = ref('')
const startDate = ref('')
const endDate = ref('')
const color = ref('#E30613')
const icon = ref('📋')

const icons = ['📋', '🏔️', '🏖️', '✈️', '🚗', '🍕', '🎉', '🎄', '🏠', '🎮', '🎬', '🎵']

watch(() => props.activity, (a) => {
  if (a) {
    name.value = a.name || ''
    description.value = a.description || ''
    startDate.value = a.start_date || ''
    endDate.value = a.end_date || ''
    color.value = a.color || '#E30613'
    icon.value = a.icon || '📋'
  } else {
    name.value = ''
    description.value = ''
    startDate.value = ''
    endDate.value = ''
    color.value = '#E30613'
    icon.value = '📋'
  }
}, { immediate: true })

const handleSave = (): void => {
  emit('save', {
    name: name.value,
    description: description.value,
    start_date: startDate.value || null,
    end_date: endDate.value || null,
    color: color.value,
    icon: icon.value
  })
}
</script>

<template>
  <Transition name="fade">
    <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/95 backdrop-blur-md" @click="$emit('close')"></div>
      <div class="bg-industrial-gray w-full max-w-md border border-zinc-800 shadow-2xl relative overflow-hidden text-white">
        <div class="h-1 bg-brand-red absolute top-0 left-0 right-0"></div>
        <div class="p-8">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-2xl font-black uppercase italic tracking-tighter">
              {{ activity ? 'Bewerk activiteit' : 'Nieuwe activiteit' }}
            </h2>
            <button @click="$emit('close')" class="text-zinc-600 hover:text-white text-xl leading-none">×</button>
          </div>
          <div class="space-y-6">
            <div>
              <label class="block text-xs font-black uppercase tracking-widest text-zinc-500 mb-2">Naam *</label>
              <input v-model="name" type="text" class="w-full bg-zinc-900 border border-zinc-800 p-4 font-black uppercase outline-none italic text-sm text-white focus:border-brand-red" placeholder="Bijv. Weekendje Ardennen" required>
            </div>
            <div>
              <label class="block text-xs font-black uppercase tracking-widest text-zinc-500 mb-2">Beschrijving</label>
              <textarea v-model="description" rows="2" class="w-full bg-zinc-900 border border-zinc-800 p-4 font-medium outline-none text-sm text-white focus:border-brand-red" placeholder="Optionele beschrijving"></textarea>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-black uppercase tracking-widest text-zinc-500 mb-2">Start datum</label>
                <input v-model="startDate" type="date" class="w-full bg-zinc-900 border border-zinc-800 p-4 font-black uppercase outline-none italic text-sm text-white focus:border-brand-red">
              </div>
              <div>
                <label class="block text-xs font-black uppercase tracking-widest text-zinc-500 mb-2">Eind datum</label>
                <input v-model="endDate" type="date" class="w-full bg-zinc-900 border border-zinc-800 p-4 font-black uppercase outline-none italic text-sm text-white focus:border-brand-red">
              </div>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-black uppercase tracking-widest text-zinc-500 mb-2">Kleur</label>
                <input v-model="color" type="color" class="w-full h-12 bg-zinc-900 border border-zinc-800 cursor-pointer">
              </div>
              <div>
                <label class="block text-xs font-black uppercase tracking-widest text-zinc-500 mb-2">Icon</label>
                <div class="grid grid-cols-6 gap-2">
                  <button 
                    v-for="ic in icons" 
                    :key="ic"
                    type="button"
                    @click="icon = ic"
                    class="p-2 border border-zinc-700 hover:border-brand-red transition-all text-xl"
                    :class="icon === ic ? 'bg-brand-red/20 border-brand-red' : ''"
                  >
                    {{ ic }}
                  </button>
                </div>
              </div>
            </div>
            <div class="flex gap-4 pt-4">
              <button @click="$emit('close')" class="flex-1 py-4 font-black uppercase italic border border-zinc-700 text-zinc-400 hover:text-white hover:border-zinc-500 transition-all">Annuleren</button>
              <button @click="handleSave" :disabled="!name" class="flex-1 py-4 font-black uppercase italic bg-brand-red text-white hover:bg-red-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed">Opslaan</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>
