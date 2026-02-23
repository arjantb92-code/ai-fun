<script setup lang="ts">
import { ref, watch } from 'vue'
import BaseModal from '@/components/common/BaseModal.vue'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', data: { name: string; currency: string }): void
}>()

const name = ref('')
const currency = ref('EUR')

const currencies = [
  { code: 'EUR', label: 'Euro (€)' },
  { code: 'USD', label: 'US Dollar ($)' },
  { code: 'GBP', label: 'Brits Pond (£)' },
  { code: 'CHF', label: 'Zwitserse Frank (Fr)' }
]

watch(() => props.isOpen, (open) => {
  if (open) {
    name.value = ''
    currency.value = 'EUR'
  }
})

const handleSubmit = () => {
  if (!name.value.trim()) return
  emit('save', {
    name: name.value.trim(),
    currency: currency.value
  })
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Nieuwe Balans" @close="emit('close')">
    <form @submit.prevent="handleSubmit" class="space-y-6">
      <div>
        <label class="block text-sm font-bold uppercase text-gray-400 mb-2">Naam</label>
        <input
          v-model="name"
          type="text"
          placeholder="bijv. Vakantie Griekenland"
          class="w-full bg-black border border-gray-700 px-4 py-3 text-white focus:border-brand-red focus:outline-none"
          required
        />
      </div>

      <div>
        <label class="block text-sm font-bold uppercase text-gray-400 mb-2">Valuta</label>
        <select
          v-model="currency"
          class="w-full bg-black border border-gray-700 px-4 py-3 text-white focus:border-brand-red focus:outline-none"
        >
          <option v-for="c in currencies" :key="c.code" :value="c.code">
            {{ c.label }}
          </option>
        </select>
      </div>

      <div class="flex gap-4 pt-4">
        <button
          type="button"
          class="flex-1 border border-gray-700 px-6 py-3 font-bold uppercase hover:bg-gray-800 transition-colors italic"
          @click="emit('close')"
        >
          Annuleren
        </button>
        <button
          type="submit"
          class="flex-1 bg-brand-red px-6 py-3 font-bold uppercase hover:bg-red-700 transition-colors italic"
          :disabled="!name.trim()"
        >
          Aanmaken
        </button>
      </div>
    </form>
  </BaseModal>
</template>
