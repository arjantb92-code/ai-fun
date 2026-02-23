<script setup lang="ts">
import { ref, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import BaseModal from '@/components/common/BaseModal.vue'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'join', inviteCode: string): Promise<{ success: boolean; message: string }>
}>()

const store = useAppStore()
const inviteCode = ref('')
const isLoading = ref(false)
const error = ref('')
const preview = ref<{
  id: number
  name: string
  currency: string
  member_count: number
  is_member: boolean
} | null>(null)

watch(() => props.isOpen, (open) => {
  if (open) {
    inviteCode.value = ''
    error.value = ''
    preview.value = null
  }
})

const handleLookup = async () => {
  if (!inviteCode.value.trim()) return
  
  isLoading.value = true
  error.value = ''
  preview.value = null
  
  const result = await store.lookupBalanceList(inviteCode.value.trim())
  isLoading.value = false
  
  if (result) {
    preview.value = result
  } else {
    error.value = 'Ongeldige uitnodigingscode'
  }
}

const handleJoin = async () => {
  if (!inviteCode.value.trim()) return
  
  isLoading.value = true
  error.value = ''
  
  const result = await emit('join', inviteCode.value.trim())
  isLoading.value = false
  
  if (!result.success) {
    error.value = result.message
  }
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Deelnemen aan Balans" @close="emit('close')">
    <div class="space-y-6">
      <div>
        <label class="block text-sm font-bold uppercase text-gray-400 mb-2">
          Uitnodigingscode
        </label>
        <div class="flex gap-2">
          <input
            v-model="inviteCode"
            type="text"
            placeholder="Plak hier de code"
            class="flex-1 bg-black border border-gray-700 px-4 py-3 text-white focus:border-brand-red focus:outline-none font-mono"
            @keyup.enter="handleLookup"
          />
          <button
            type="button"
            class="px-4 py-3 bg-gray-800 border border-gray-700 font-bold uppercase hover:bg-gray-700 transition-colors text-sm"
            :disabled="!inviteCode.trim() || isLoading"
            @click="handleLookup"
          >
            Zoeken
          </button>
        </div>
      </div>

      <div v-if="error" class="bg-red-900/50 border border-red-700 p-4 text-red-300">
        {{ error }}
      </div>

      <div v-if="preview" class="bg-industrial-gray p-4 rounded-lg space-y-2">
        <h4 class="font-bold text-lg">{{ preview.name }}</h4>
        <p class="text-gray-400 text-sm">
          {{ preview.member_count }} deelnemer(s) • {{ preview.currency }}
        </p>
        <div v-if="preview.is_member" class="text-yellow-400 text-sm">
          Je bent al lid van deze balans.
        </div>
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
          type="button"
          class="flex-1 bg-brand-red px-6 py-3 font-bold uppercase hover:bg-red-700 transition-colors italic disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="!preview || isLoading"
          @click="handleJoin"
        >
          <span v-if="isLoading">Bezig...</span>
          <span v-else-if="preview?.is_member">Openen</span>
          <span v-else>Deelnemen</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>
