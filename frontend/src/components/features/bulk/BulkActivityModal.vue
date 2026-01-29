<script setup>
/**
 * BulkActivityModal - Modal for assigning multiple transactions to an activity.
 * Extracted from App.vue for better code organization.
 */
import { ref, watch } from 'vue'
import BaseModal from '@/components/shared/BaseModal.vue'
import ActivitySelector from '@/components/features/activities/ActivitySelector.vue'

const props = defineProps({
  isOpen: Boolean,
  activities: Array,
  initialActivityId: [Number, null]
})

const emit = defineEmits(['close', 'apply'])

const chosenActivityId = ref(null)

// Sync with initial value when modal opens
watch(() => props.isOpen, (open) => {
  if (open) {
    chosenActivityId.value = props.initialActivityId
  }
})

const handleApply = () => {
  emit('apply', chosenActivityId.value)
}

const updateActivityId = (value) => {
  chosenActivityId.value = (value === 'null' || value === '' || value == null) ? null : Number(value)
}
</script>

<template>
  <BaseModal 
    :is-open="isOpen" 
    title="Koppel aan activiteit"
    @close="$emit('close')"
  >
    <div class="space-y-6">
      <ActivitySelector 
        v-if="activities?.length"
        :activities="activities"
        :selected-id="chosenActivityId"
        @update:selected-id="updateActivityId"
      />
      
      <p v-else class="text-zinc-500 text-sm italic">
        Geen activiteiten beschikbaar.
      </p>
      
      <div class="flex gap-4">
        <button 
          type="button" 
          class="px-6 py-3 border border-zinc-700 text-zinc-400 font-black uppercase text-sm hover:text-white hover:border-zinc-500 transition-all" 
          @click="$emit('close')"
        >
          Annuleren
        </button>
        <button 
          type="button" 
          class="flex-1 bg-brand-red text-white py-3 font-black uppercase text-sm hover:bg-red-600 transition-all" 
          @click="handleApply"
        >
          Toepassen
        </button>
      </div>
    </div>
  </BaseModal>
</template>
