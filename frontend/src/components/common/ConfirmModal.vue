<script setup lang="ts">
import { useConfirm } from '@/composables/useConfirm'
import BaseModal from '@/components/common/BaseModal.vue'

const { isOpen, message, title, confirmOnly, resolveConfirm } = useConfirm()
</script>

<template>
  <BaseModal :is-open="isOpen" :title="title" :show-close="false" max-width="max-w-md" @close="resolveConfirm(false)">
    <p class="text-white font-industrial text-sm uppercase tracking-wide">{{ message }}</p>
    <template #footer>
      <div class="flex gap-4 justify-end border-t border-zinc-800 pt-6 p-8">
        <button
          v-if="!confirmOnly"
          type="button"
          class="px-6 py-3 font-black uppercase italic text-xs tracking-widest border border-zinc-600 text-zinc-400 hover:border-zinc-500 hover:text-white transition-all"
          @click="resolveConfirm(false)"
        >
          Annuleren
        </button>
        <button
          type="button"
          class="px-6 py-3 font-black uppercase italic text-xs tracking-widest bg-brand-red text-white hover:opacity-90 transition-all"
          @click="resolveConfirm(true)"
        >
          {{ confirmOnly ? 'OK' : 'Bevestigen' }}
        </button>
      </div>
    </template>
  </BaseModal>
</template>
