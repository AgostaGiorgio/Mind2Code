<script setup>
defineProps({
  icon: { type: [Object, Function], default: null },
  title: { type: String, default: 'Nothing here' },
  description: { type: String, default: '' },
})
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-2 py-16 px-6 text-center">
    <component v-if="icon" :is="icon" :size="28" :stroke-width="2" class="text-brand-primary" />
    <p class="text-brand-textMain text-sm font-semibold">{{ title }}</p>
    <p v-if="description" class="text-brand-textMuted text-xs max-w-xs">{{ description }}</p>
    <div v-if="$slots.default" class="mt-2">
      <slot />
    </div>
  </div>
</template>
