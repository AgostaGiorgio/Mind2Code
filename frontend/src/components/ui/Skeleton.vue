<script setup>
defineProps({
  lines: { type: Number, default: 3 },
  height: { type: String, default: 'h-14' },
})
</script>

<template>
  <div class="flex flex-col gap-3">
    <div
      v-for="n in lines"
      :key="n"
      class="w-full animate-pulse bg-white/5 rounded-app-sm"
      :class="height"
    />
  </div>
</template>
