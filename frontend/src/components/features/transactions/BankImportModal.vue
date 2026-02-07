<script setup lang="ts">
import { ref, computed } from 'vue'
import type { BankImportRow, BankType } from '@/types'

interface Props {
  isOpen: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'imported', rows: BankImportRow[]): void
}>()

const bankType = ref<BankType>('ing')
const fileInput = ref<HTMLInputElement | null>(null)
const file = ref<File | null>(null)
const loading = ref(false)
const error = ref('')
const previewRows = ref<BankImportRow[]>([])
const step = ref<1 | 2>(1) // 1 = upload, 2 = preview

const handleFileChange = (e: Event): void => {
  const target = e.target as HTMLInputElement
  const f = target.files?.[0]
  file.value = f || null
  error.value = ''
  if (f && !/\.(csv|txt)$/i.test(f.name)) {
    error.value = 'Alleen CSV of TXT bestanden.'
  }
}

const getAuthHeader = (): Record<string, string> => {
  const t = localStorage.getItem('wbw_token')
  return t ? { 'Authorization': `Bearer ${t}` } : {}
}

const doUpload = async (): Promise<void> => {
  if (!file.value) return
  loading.value = true
  error.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file.value)
    formData.append('bank_type', bankType.value)
    const res = await fetch('http://localhost:5001/import/bank', {
      method: 'POST',
      headers: getAuthHeader(),
      body: formData
    })
    const data = await res.json().catch(() => ({})) as { transactions?: Array<{ date: string; time?: string; description: string; raw_description?: string; amount: number }>; error?: string }
    if (res.ok && data.transactions) {
      previewRows.value = data.transactions.map((r, i) => ({ ...r, _id: i, selected: true }))
      step.value = 2
    } else {
      error.value = data.error || 'Import mislukt'
    }
  } catch (e) {
    error.value = (e as Error).message || 'Verbinding mislukt'
  } finally {
    loading.value = false
  }
}

const toggleAll = (v: boolean): void => {
  previewRows.value.forEach(r => { r.selected = v })
}

const selectedCount = computed(() => previewRows.value.filter(r => r.selected).length)

const closeModal = (): void => {
  step.value = 1
  file.value = null
  previewRows.value = []
  error.value = ''
  if (fileInput.value) fileInput.value.value = ''
  emit('close')
}

const confirmImport = (): void => {
  emit('imported', previewRows.value.filter(r => r.selected))
  closeModal()
}
</script>

<template>
  <Transition name="fade">
    <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/95 backdrop-blur-md" @click="closeModal"></div>
      <div class="bg-industrial-gray w-full max-w-3xl max-h-[90vh] border border-zinc-800 shadow-2xl relative flex flex-col overflow-hidden text-white">
        <div class="h-1 bg-brand-red absolute top-0 left-0 right-0 shrink-0"></div>
        <div class="p-8 overflow-auto flex-1">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-2xl font-black uppercase italic tracking-tighter">Bank Import</h2>
            <button type="button" @click="closeModal" class="text-zinc-600 hover:text-white text-xl leading-none">×</button>
          </div>

          <template v-if="step === 1">
            <div class="space-y-6">
              <div>
                <label class="block text-xs font-black uppercase tracking-widest text-zinc-500 mb-2">Bestandsformaat</label>
                <select v-model="bankType" class="w-full bg-zinc-900 border border-zinc-800 p-4 font-black uppercase tracking-widest text-sm outline-none text-white focus:border-brand-red">
                  <option value="ing">ING (CSV)</option>
                  <option value="abn">ABN AMRO (TXT)</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-black uppercase tracking-widest text-zinc-500 mb-2">Bestand</label>
                <input ref="fileInput" type="file" accept=".csv,.txt" @change="handleFileChange"
                       class="w-full bg-zinc-900 border border-zinc-800 p-4 font-black uppercase text-sm text-white file:mr-4 file:py-2 file:px-4 file:border-0 file:bg-brand-red file:text-white file:font-black file:uppercase file:italic">
              </div>
              <p v-if="error" class="text-brand-red text-sm font-bold">{{ error }}</p>
              <button type="button" @click="doUpload" :disabled="!file || loading"
                      class="w-full py-4 font-black uppercase italic bg-brand-red text-white hover:bg-red-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                {{ loading ? 'Laden...' : 'Upload en preview' }}
              </button>
            </div>
          </template>

          <template v-else>
            <div class="space-y-4">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-2xl font-black italic uppercase tracking-tighter">Bank Ingestion</h3>
                <div class="flex gap-2">
                  <button type="button" @click="toggleAll(true)" class="px-3 py-1 text-[10px] font-black uppercase border border-zinc-700 text-zinc-400 hover:text-white hover:border-brand-red transition-all">Alles</button>
                  <button type="button" @click="toggleAll(false)" class="px-3 py-1 text-[10px] font-black uppercase border border-zinc-700 text-zinc-400 hover:text-white hover:border-brand-red transition-all">Niets</button>
                </div>
              </div>
              
              <div class="border-t border-zinc-800 pt-4 overflow-auto max-h-[60vh] custom-scrollbar space-y-2">
                <div v-for="r in previewRows" :key="r._id" 
                     class="flex items-start gap-4 p-3 bg-industrial-gray/40 border-l-2 border-transparent hover:bg-zinc-900 hover:border-brand-red transition-all cursor-pointer group"
                     @click="r.selected = !r.selected">
                  
                  <!-- Checkbox -->
                  <div class="w-5 h-5 flex items-center justify-center shrink-0 border transition-colors mt-1.5"
                       :class="r.selected ? 'bg-brand-red border-brand-red' : 'border-zinc-700 bg-zinc-900 group-hover:border-zinc-500'">
                    <span v-if="r.selected" class="text-white font-black text-xs">✓</span>
                  </div>

                  <!-- Date -->
                  <div class="text-zinc-500 font-bold italic w-24 shrink-0 text-xs mt-1.5">
                    {{ r.date }}
                  </div>

                  <!-- Description -->
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                      <div class="font-black uppercase italic tracking-tight text-white truncate text-base group-hover:text-brand-red transition-colors"
                           :title="r.description">
                        {{ r.description }}
                      </div>
                      <div v-if="r.time && r.time !== '00:00'" 
                           class="text-[9px] font-black text-white bg-brand-red/20 px-1.5 py-0.5 border border-brand-red/40 tracking-tighter uppercase italic">
                        {{ r.time }}
                      </div>
                    </div>
                    <div class="text-[10px] text-zinc-600 truncate uppercase italic font-bold tracking-tight mt-0.5 group-hover:text-zinc-500 transition-colors"
                         :title="r.raw_description">
                      {{ r.raw_description || r.description }}
                    </div>
                  </div>

                  <!-- Amount -->
                  <div class="font-black italic text-base tracking-tighter w-24 text-right shrink-0 mt-1.5" 
                       :class="r.amount >= 0 ? 'text-zinc-400' : 'text-brand-red'">
                    € {{ Math.abs(r.amount).toFixed(2) }}
                  </div>
                </div>
              </div>

              <div class="pt-6">
                <button type="button" @click="confirmImport" 
                        class="w-full py-5 font-black uppercase italic tracking-[0.2em] text-xl bg-brand-red text-white hover:bg-red-600 transition-all shadow-glow hover:scale-[1.01] active:scale-[0.99]">
                  Commit {{ selectedCount }} Segments
                </button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </Transition>
</template>
