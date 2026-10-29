<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  label: { type: String, default: '' },
  description: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <button
    type="button"
    role="switch"
    :aria-checked="modelValue"
    :disabled="disabled"
    class="flex w-full items-center justify-between gap-4 rounded-app-sm border border-white/10 bg-brand-background p-3 text-left transition-colors hover:border-white/20 disabled:opacity-50"
    @click="emit('update:modelValue', !modelValue)"
  >
    <span class="min-w-0">
      <span class="block text-sm font-semibold text-brand-textMain">{{ label }}</span>
      <span v-if="description" class="mt-0.5 block text-xs text-brand-textMuted">
        {{ description }}
      </span>
    </span>

    <span
      class="relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors duration-300"
      :class="modelValue ? 'bg-brand-primary' : 'bg-white/15'"
      aria-hidden="true"
    >
      <span
        class="inline-block h-4 w-4 rounded-full bg-white shadow transition-transform duration-300"
        :class="modelValue ? 'translate-x-6' : 'translate-x-1'"
      />
    </span>
  </button>
</template>
