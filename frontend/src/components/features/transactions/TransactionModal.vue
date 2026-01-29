<script setup>
import { ref, watch, computed } from 'vue'
import ActivitySelector from '@/components/features/activities/ActivitySelector.vue'

const CATEGORIES = [
  { key: 'boodschappen', label: 'Boodschappen', icon: '🛒' },
  { key: 'huishoudelijk', label: 'Huishoudelijk', icon: '🏠' },
  { key: 'winkelen', label: 'Winkelen', icon: '🛍️' },
  { key: 'vervoer', label: 'Vervoer', icon: '🚗' },
  { key: 'reizen_vrije_tijd', label: 'Reizen & Vrije Tijd', icon: '✈️' },
  { key: 'overig', label: 'Overig', icon: '📦' }
]

const props = defineProps({
  isOpen: Boolean,
  transaction: Object,
  users: Array,
  groupMembers: Array,
  activities: Array
})

const getCategoryIcon = (key) => CATEGORIES.find(c => c.key === key)?.icon || '📦'

const emit = defineEmits(['close', 'save', 'delete', 'upload-receipt'])

const localTx = ref(null)

watch(() => props.transaction, (newVal) => {
  if (newVal) {
    localTx.value = JSON.parse(JSON.stringify(newVal))
    if (!localTx.value.activity_id) localTx.value.activity_id = null
    if (!localTx.value.category) localTx.value.category = 'overig'
    if (!localTx.value.time) localTx.value.time = '00:00'
  }
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
      <div class="bg-industrial-gray w-full max-w-2xl border border-zinc-800 shadow-2xl relative animate-in fade-in zoom-in duration-300 overflow-hidden text-white max-h-[90vh] flex flex-col">
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

        <div class="p-10 max-h-[85vh] overflow-y-auto">
          <div class="flex justify-between items-start mb-8">
            <h2 class="text-4xl font-black uppercase italic tracking-tighter">{{ localTx.id ? 'Edit Entry' : 'New Entry' }}</h2>
            <button @click="$emit('close')" class="text-zinc-600 hover:text-white">X</button>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
            <div class="space-y-6">
              <input v-model="localTx.description" type="text" class="w-full bg-zinc-900 border border-zinc-800 p-4 font-black uppercase outline-none italic text-sm text-white focus:border-brand-red" placeholder="Omschrijving">
              
              <!-- Date and Time -->
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-[10px] uppercase opacity-40 font-black mb-2 tracking-[0.2em] italic">Datum</label>
                  <input v-model="localTx.date" type="date" class="w-full bg-zinc-900 border border-zinc-800 p-4 font-black uppercase outline-none italic text-sm text-white focus:border-brand-red">
                </div>
                <div>
                  <label class="block text-[10px] uppercase opacity-40 font-black mb-2 tracking-[0.2em] italic">Tijd</label>
                  <input v-model="localTx.time" type="time" class="w-full bg-zinc-900 border border-zinc-800 p-4 font-black uppercase outline-none italic text-sm text-white focus:border-brand-red">
                </div>
              </div>
              
              <div>
                <label class="block text-[10px] uppercase opacity-40 font-black mb-2 tracking-[0.2em] italic">Activiteit</label>
                <ActivitySelector 
                  v-if="activities"
                  :activities="activities"
                  :selected-id="localTx.activity_id"
                  @update:selected-id="localTx.activity_id = $event"
                />
              </div>
              
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

              <div class="border-2 border-dashed border-zinc-800 p-8 text-center hover:border-brand-red hover:bg-brand-red/5 transition-all cursor-pointer relative group">
                <input type="file" @change="handleFileUpload" class="absolute inset-0 opacity-0 cursor-pointer" accept="image/*" />
                <div class="space-y-2 pointer-events-none">
                   <div class="text-2xl opacity-20">📷</div>
                   <span class="text-[10px] uppercase font-black opacity-30 tracking-widest block italic group-hover:opacity-100">Attach Receipt</span>
                </div>
              </div>
            </div>

            <div class="space-y-6">
              <!-- Category - Verplaatst naar rechts en kleiner gemaakt -->
              <div>
                <label class="block text-[10px] uppercase opacity-40 font-black mb-2 tracking-[0.2em] italic">Categorie</label>
                <div class="grid grid-cols-3 gap-1.5">
                  <button v-for="cat in CATEGORIES" :key="cat.key"
                          type="button"
                          @click="localTx.category = cat.key"
                          class="p-2 border text-center transition-all text-[10px] font-black uppercase italic"
                          :class="localTx.category === cat.key 
                            ? 'bg-brand-red border-brand-red text-white' 
                            : 'bg-zinc-900 border-zinc-800 text-zinc-500 hover:border-zinc-600'">
                    <span class="block text-sm mb-0.5">{{ cat.icon }}</span>
                    <span class="block text-[8px] tracking-tight leading-tight">{{ cat.label }}</span>
                  </button>
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
          </div>
          <div class="mt-8 flex gap-4 pt-6 border-t border-zinc-800">
            <button v-if="localTx.id" @click="$emit('delete', localTx.id)" class="border-2 border-zinc-800 text-zinc-600 px-8 py-5 font-black uppercase tracking-[0.2em] hover:text-red-500 hover:border-red-500 transition-all italic text-sm">Delete</button>
            <button @click="$emit('save', localTx)" class="flex-1 bg-brand-red text-white py-5 font-black uppercase tracking-[0.3em] italic text-2xl shadow-2xl transform active:scale-[0.98] transition-all">Save</button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>
