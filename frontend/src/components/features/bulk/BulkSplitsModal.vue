<script setup>
/**
 * BulkSplitsModal - Modal for applying same splits to multiple transactions.
 * Uses useSplits composable to manage split state.
 */
import { watch } from 'vue'
import BaseModal from '@/components/common/BaseModal.vue'
import { useSplits } from '@/composables/useSplits'

const props = defineProps({
  isOpen: Boolean,
  groupMembers: Array
})

const emit = defineEmits(['close', 'apply'])

const { 
  splits, 
  toggleUser, 
  incrementWeight, 
  decrementWeight, 
  isUserIncluded, 
  getWeight,
  initFromMembers 
} = useSplits()

// Initialize splits when modal opens
watch(() => props.isOpen, (open) => {
  if (open && props.groupMembers?.length) {
    initFromMembers(props.groupMembers)
  }
})

const handleApply = () => {
  if (splits.value.length) {
    emit('apply', [...splits.value])
  }
}
</script>

<template>
  <BaseModal 
    :is-open="isOpen" 
    title="Zelfde personen toepassen"
    max-width="max-w-md"
    @close="$emit('close')"
  >
    <div class="space-y-6">
      <div class="space-y-2 max-h-[50vh] overflow-y-auto">
        <div 
          v-for="user in groupMembers" 
          :key="user.id"
          class="split-row"
          :class="isUserIncluded(user.id) ? 'split-row-active' : 'split-row-inactive'"
        >
          <!-- User info with toggle -->
          <div 
            class="flex items-center gap-4 cursor-pointer" 
            @click="toggleUser(user.id)"
          >
            <div 
              class="weight-indicator"
              :class="isUserIncluded(user.id) ? 'weight-indicator-active' : 'weight-indicator-inactive'"
            ></div>
            <span class="font-black uppercase text-[11px] italic">{{ user.name }}</span>
          </div>
          
          <!-- Weight controls -->
          <div v-if="isUserIncluded(user.id)" class="flex items-center gap-2">
            <button 
              type="button" 
              class="w-6 h-6 hover:text-brand-red font-black text-xs transition-colors" 
              @click.stop="decrementWeight(user.id)"
            >
              −
            </button>
            <span class="font-black text-brand-red text-sm w-6 text-center">
              {{ getWeight(user.id) }}
            </span>
            <button 
              type="button" 
              class="w-6 h-6 hover:text-brand-red font-black text-xs transition-colors" 
              @click.stop="incrementWeight(user.id)"
            >
              +
            </button>
          </div>
        </div>
      </div>
      
      <div class="flex gap-4 pt-4 border-t border-zinc-800">
        <button 
          type="button" 
          class="px-6 py-3 border border-zinc-700 text-zinc-400 font-black uppercase text-sm hover:text-white hover:border-zinc-500 transition-all" 
          @click="$emit('close')"
        >
          Annuleren
        </button>
        <button 
          type="button" 
          class="flex-1 bg-brand-red text-white py-3 font-black uppercase text-sm hover:bg-red-600 transition-all disabled:opacity-50" 
          :disabled="!splits.length"
          @click="handleApply"
        >
          Toepassen
        </button>
      </div>
    </div>
  </BaseModal>
</template>
