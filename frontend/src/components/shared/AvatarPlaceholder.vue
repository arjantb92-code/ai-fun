<script setup lang="ts">
interface Props {
  name?: string
  size?: string
}

withDefaults(defineProps<Props>(), {
  name: undefined,
  size: 'w-10 h-10'
})
</script>

<template>
  <div :class="[size, 'bg-zinc-900 border border-zinc-800 flex items-center justify-center overflow-hidden relative group-hover:border-brand-red transition-colors']">
    <span class="text-xs font-black text-brand-red italic uppercase">{{ name ? name[0] : '?' }}</span>
  </div>
</template>
