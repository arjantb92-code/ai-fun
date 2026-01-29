<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  isOpen: Boolean,
  transaction: Object,
  users: Array,
  groupMembers: Array
})

const emit = defineEmits(['close', 'save', 'delete', 'upload-receipt'])

const localTx = ref(null)

watch(() => props.transaction, (newVal) => {
  if (newVal) localTx.value = JSON.parse(JSON.stringify(newVal))
}, { immediate: true })

const toggleUserInSplit = (userId) => {
  const idx = localTx.value.splits.findIndex(s => s.user_id === userId)
  if (idx !== -1) localTx.value.splits.splice(idx, 1)
  else localTx.value.splits.push({ user_id: userId, weight: 1 })
}

const incrementWeight = (uId) => {
  const s = localTx.value.splits.find(s => s.user_id === uId)
  if (s) s.weight++
}

const decrementWeight = (uId) => {
  const s = localTx.value.splits.find(s => s.user_id === uId)
  if (s && s.weight > 1) s.weight--
}

const handleFileUpload = (e) => {
  const file = e.target.files[0]
  if (file) emit('upload-receipt', file)
}
</script>

<template>
  <Transition name="fade">
    <div v-if="isOpen && localTx" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/95 backdrop-blur-md" @click="$emit('close')"></div>
      <div class="bg-industrial-gray w-full max-w-2xl border border-zinc-800 shadow-2xl relative animate-in fade-in zoom-in duration-300 overflow-hidden text-white">
        <div class="h-1 bg-brand-red absolute top-0 left-0 right-0 shadow-[0_0_15px_rgba(227,6,19,0.5)]"></div>
        
        <!-- Tabs -->
        <div class="flex border-b border-zinc-800">
           <button v-for="tType in ['EXPENSE', 'INCOME', 'TRANSFER']" :key="tType"
                   @click="localTx.type = tType"
                   class="flex-1 py-5 font-black uppercase italic text-[10px] tracking-[0.2em] transition-all"
                   :class="localTx.type === tType ? 'bg-brand-red text-white' : 'hover:bg-zinc-800 text-zinc-600'">
              {{ tType }}
           </button>
        </div>

        <div class="p-10">
          <div class="flex justify-between items-start mb-8">
            <h2 class="text-4xl font-black uppercase italic tracking-tighter">{{ localTx.id ? 'Edit Entry' : 'New Entry' }}</h2>
            <button @click="$emit('close')" class="text-zinc-600 hover:text-white">X</button>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
            <div class="space-y-8">
              <input v-model="localTx.description" type="text" class="w-full bg-zinc-900 border border-zinc-800 p-4 font-black uppercase outline-none italic text-sm text-white focus:border-brand-red" placeholder="Omschrijving">
              
              <div class="grid grid-cols-2 gap-6">
                <div class="relative">
                   <span class="absolute left-4 top-1/2 -translate-y-1/2 font-black text-zinc-600 italic text-xl">€</span>
                   <input v-model.number="localTx.amount" type="number" class="w-full bg-zinc-900 border border-zinc-800 p-4 pl-10 font-black text-3xl tracking-tighter italic outline-none text-white focus:border-brand-red" step="0.01">
                </div>
                <div class="relative">
                   <select v-model="localTx.payer_id" class="w-full bg-zinc-900 border border-zinc-800 p-5 font-black uppercase tracking-widest text-[10px] outline-none text-white italic focus:border-brand-red appearance-none">
                     <option v-for="u in users" :key="u.id" :value="u.id">{{ u.name }}</option>
                   </select>
                </div>
              </div>

              <div class="border-2 border-dashed border-zinc-800 p-12 text-center hover:border-brand-red hover:bg-brand-red/5 transition-all cursor-pointer relative group">
                <input type="file" @change="handleFileUpload" class="absolute inset-0 opacity-0 cursor-pointer" accept="image/*" />
                <div class="space-y-2 pointer-events-none">
                   <div class="text-2xl opacity-20">📷</div>
                   <span class="text-[10px] uppercase font-black opacity-30 tracking-widest block italic group-hover:opacity-100">Attach Receipt</span>
                </div>
              </div>
            </div>

            <div>
              <label class="block text-[10px] uppercase opacity-40 font-black mb-6 tracking-[0.2em] italic border-b border-zinc-800 pb-2">Distribution</label>
              <div class="space-y-2">
                <div v-for="u in groupMembers" :key="u.id" 
                     class="flex items-center justify-between p-4 border border-zinc-800 transition-all" 
                     :class="localTx.splits.some(s => s.user_id === u.id) ? 'bg-zinc-900 border-brand-red/50 shadow-inner' : 'opacity-20'">
                  <div @click="toggleUserInSplit(u.id)" class="flex items-center gap-4 cursor-pointer select-none">
                    <div class="w-1.5 h-4" :class="localTx.splits.some(s => s.user_id === u.id) ? 'bg-brand-red shadow-glow' : 'bg-zinc-700'"></div>
                    <span class="font-black uppercase text-[11px] italic">{{ u.name }}</span>
                  </div>
                  <div v-if="localTx.splits.some(s => s.user_id === u.id) && localTx.type !== 'TRANSFER'" class="flex items-center gap-3">
                     <button @click="decrementWeight(u.id)" class="w-6 h-6 hover:text-brand-red transition-colors font-black text-xs">-</button>
                     <span class="font-black text-brand-red italic text-sm w-4 text-center">{{ localTx.splits.find(s => s.user_id === u.id).weight }}</span>
                     <button @click="incrementWeight(u.id)" class="w-6 h-6 hover:text-brand-red transition-colors font-black text-xs">+</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="mt-12 flex gap-4">
            <button v-if="localTx.id" @click="$emit('delete', localTx.id)" class="border-2 border-zinc-800 text-zinc-600 px-8 py-5 font-black uppercase tracking-[0.2em] hover:text-red-500 hover:border-red-500 transition-all italic text-sm">Delete</button>
            <button @click="$emit('save', localTx)" class="flex-1 bg-brand-red text-white py-5 font-black uppercase tracking-[0.3em] italic text-2xl shadow-2xl transform active:scale-[0.98] transition-all">Save</button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>
