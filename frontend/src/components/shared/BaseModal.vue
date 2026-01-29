<script setup>
/**
 * BaseModal - Reusable modal wrapper with consistent styling.
 * All modals should extend this component for consistent UX.
 */
defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  maxWidth: {
    type: String,
    default: 'max-w-md'
  },
  title: {
    type: String,
    default: ''
  },
  showClose: {
    type: Boolean,
    default: true
  }
})

defineEmits(['close'])
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <!-- Backdrop -->
        <div 
          class="absolute inset-0 bg-black/95 backdrop-blur-md" 
          @click="$emit('close')"
        ></div>
        
        <!-- Modal Container -->
        <div 
          :class="[
            'bg-industrial-gray w-full border border-zinc-800 shadow-2xl relative overflow-hidden text-white',
            maxWidth
          ]"
        >
          <!-- Top accent bar -->
          <div class="h-1 bg-brand-red absolute top-0 left-0 right-0 shadow-[0_0_15px_rgba(227,6,19,0.5)]"></div>
          
          <!-- Content wrapper -->
          <div class="p-8">
            <!-- Header with title and close button -->
            <div v-if="title || showClose" class="flex justify-between items-center mb-6">
              <h2 v-if="title" class="text-2xl font-black uppercase italic tracking-tighter">
                {{ title }}
              </h2>
              <div v-else></div>
              <button 
                v-if="showClose"
                @click="$emit('close')" 
                class="text-zinc-600 hover:text-white text-xl leading-none transition-colors"
              >
                ×
              </button>
            </div>
            
            <!-- Main content slot -->
            <slot />
          </div>
          
          <!-- Optional footer slot -->
          <slot name="footer" />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
