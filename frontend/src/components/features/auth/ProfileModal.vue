<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  isOpen: Boolean,
  user: Object
})

const emit = defineEmits(['close', 'save'])

const name = ref('')
const email = ref('')

watch(() => props.user, (u) => {
  if (u) {
    name.value = u.name || ''
    email.value = u.email || ''
  }
}, { immediate: true })
</script>

<template>
  <Transition name="fade">
    <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/95 backdrop-blur-md" @click="$emit('close')"></div>
      <div class="bg-industrial-gray w-full max-w-md border border-zinc-800 shadow-2xl relative overflow-hidden text-white">
        <div class="h-1 bg-brand-red absolute top-0 left-0 right-0"></div>
        <div class="p-8">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-2xl font-black uppercase italic tracking-tighter">Profiel</h2>
            <button @click="$emit('close')" class="text-zinc-600 hover:text-white text-xl leading-none">×</button>
          </div>
          <div v-if="user" class="space-y-6">
            <div class="flex justify-center">
              <div class="w-24 h-24 rounded-full border-2 border-zinc-700 overflow-hidden bg-zinc-900">
                <img v-if="user.avatar_url" :src="user.avatar_url" class="w-full h-full object-cover" @error="user.avatar_url = null">
                <span v-else class="w-full h-full flex items-center justify-center text-3xl font-black text-brand-red italic">{{ (user.name || '?')[0] }}</span>
              </div>
            </div>
            <div>
              <label class="block text-xs font-black uppercase tracking-widest text-zinc-500 mb-2">Naam</label>
              <input v-model="name" type="text" class="w-full bg-zinc-900 border border-zinc-800 p-4 font-black uppercase outline-none italic text-sm text-white focus:border-brand-red" placeholder="Naam">
            </div>
            <div>
              <label class="block text-xs font-black uppercase tracking-widest text-zinc-500 mb-2">Email</label>
              <input v-model="email" type="email" class="w-full bg-zinc-900 border border-zinc-800 p-4 font-black uppercase outline-none italic text-sm text-white focus:border-brand-red" placeholder="Email">
            </div>
            <div class="flex gap-4 pt-4">
              <button @click="$emit('close')" class="flex-1 py-4 font-black uppercase italic border border-zinc-700 text-zinc-400 hover:text-white hover:border-zinc-500 transition-all">Annuleren</button>
              <button @click="$emit('save', { name, email })" class="flex-1 py-4 font-black uppercase italic bg-brand-red text-white hover:bg-red-600 transition-all">Opslaan</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>
