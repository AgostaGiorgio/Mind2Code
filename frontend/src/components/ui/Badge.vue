<script setup>
defineProps({
  color: { type: String, default: '#94a3b8' },
  dot: { type: Boolean, default: false },
})
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 text-[11px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap"
    :style="{ backgroundColor: color + '22', color }"
  >
    <span v-if="dot" class="w-1.5 h-1.5 rounded-full" :style="{ backgroundColor: color }" />
    <slot />
  </span>
</template>
