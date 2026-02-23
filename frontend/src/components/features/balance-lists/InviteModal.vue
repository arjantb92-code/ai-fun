<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import BaseModal from '@/components/common/BaseModal.vue'
import type { BalanceList } from '@/types'

const props = defineProps<{
  isOpen: boolean
  balanceList: BalanceList | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const copied = ref(false)
const qrCodeUrl = ref('')

const inviteUrl = computed(() => {
  if (!props.balanceList?.invite_code) return ''
  const baseUrl = window.location.origin
  return `${baseUrl}/join/${props.balanceList.invite_code}`
})

const copyToClipboard = async () => {
  if (!inviteUrl.value) return
  
  try {
    await navigator.clipboard.writeText(inviteUrl.value)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}

const generateQrCode = () => {
  if (!props.balanceList?.invite_code) return
  // Use a public QR code API
  const encodedUrl = encodeURIComponent(inviteUrl.value)
  qrCodeUrl.value = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodedUrl}&bgcolor=1A1A1A&color=FFFFFF`
}

watch(() => props.isOpen, (open) => {
  if (open && props.balanceList) {
    copied.value = false
    generateQrCode()
  }
})

onMounted(() => {
  if (props.isOpen && props.balanceList) {
    generateQrCode()
  }
})
</script>

<template>
  <BaseModal :is-open="isOpen" title="Uitnodiging Delen" @close="emit('close')">
    <div v-if="balanceList" class="space-y-6">
      <div class="text-center">
        <h3 class="text-lg font-bold mb-2">{{ balanceList.name }}</h3>
        <p class="text-gray-400 text-sm">
          Deel deze link of QR-code om anderen uit te nodigen
        </p>
      </div>

      <!-- Invite Code -->
      <div>
        <label class="block text-sm font-bold uppercase text-gray-400 mb-2">
          Uitnodigingscode
        </label>
        <div class="flex gap-2">
          <input
            :value="balanceList.invite_code"
            type="text"
            readonly
            class="flex-1 bg-black border border-gray-700 px-4 py-3 text-white font-mono text-center select-all"
          />
        </div>
      </div>

      <!-- Invite URL -->
      <div>
        <label class="block text-sm font-bold uppercase text-gray-400 mb-2">
          Uitnodigingslink
        </label>
        <div class="flex gap-2">
          <input
            :value="inviteUrl"
            type="text"
            readonly
            class="flex-1 bg-black border border-gray-700 px-4 py-3 text-white font-mono text-sm overflow-hidden text-ellipsis"
          />
          <button
            type="button"
            class="px-4 py-3 font-bold uppercase text-sm transition-colors"
            :class="copied ? 'bg-green-600 hover:bg-green-700' : 'bg-brand-red hover:bg-red-700'"
            @click="copyToClipboard"
          >
            {{ copied ? '✓ Gekopieerd' : 'Kopiëren' }}
          </button>
        </div>
      </div>

      <!-- QR Code -->
      <div class="text-center">
        <label class="block text-sm font-bold uppercase text-gray-400 mb-4">
          QR Code
        </label>
        <div class="inline-block bg-white p-4 rounded-lg">
          <img
            v-if="qrCodeUrl"
            :src="qrCodeUrl"
            alt="QR Code"
            class="w-48 h-48"
          />
          <div v-else class="w-48 h-48 flex items-center justify-center text-gray-500">
            Laden...
          </div>
        </div>
        <p class="text-gray-500 text-xs mt-2">
          Scan met je telefoon om direct deel te nemen
        </p>
      </div>

      <button
        type="button"
        class="w-full border border-gray-700 px-6 py-3 font-bold uppercase hover:bg-gray-800 transition-colors italic"
        @click="emit('close')"
      >
        Sluiten
      </button>
    </div>
  </BaseModal>
</template>
