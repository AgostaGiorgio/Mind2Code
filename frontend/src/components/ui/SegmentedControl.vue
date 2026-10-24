<script setup>
defineProps({
  modelValue: { type: [String, Number], default: null },
  options: { type: Array, default: () => [] }, // [{ value, label }]
})

const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <div
    class="bg-brand-surface/60 p-1 rounded-app-sm flex gap-1 border border-white/5 overflow-x-auto hide-scrollbar"
  >
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      @click="emit('update:modelValue', opt.value)"
      class="flex-1 whitespace-nowrap text-[11px] font-semibold py-1.5 px-3 rounded-[6px] transition-all duration-300 tracking-wide"
      :class="
        modelValue === opt.value
          ? 'bg-brand-primary text-white shadow-sm'
          : 'text-brand-textMuted hover:text-brand-textMain'
      "
    >
      {{ opt.label }}
    </button>
  </div>
</template>
