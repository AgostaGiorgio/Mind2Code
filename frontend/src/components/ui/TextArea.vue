<script setup>
defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  rows: { type: Number, default: 6 },
  error: { type: String, default: '' },
  hint: { type: String, default: '' },
  maxlength: { type: [String, Number], default: undefined },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <label class="flex w-full flex-col gap-1.5">
    <span
      v-if="label"
      class="text-[11px] font-semibold uppercase tracking-wider text-brand-textMuted"
      >{{ label }}</span
    >
    <textarea
      :value="modelValue"
      :rows="rows"
      :placeholder="placeholder"
      :maxlength="maxlength"
      :disabled="disabled"
      class="w-full resize-y rounded-app-sm border bg-brand-background px-3 py-2.5 text-sm text-brand-textMain outline-none transition-all placeholder:text-brand-textMuted/40 disabled:opacity-50"
      :class="
        error
          ? 'border-red-400/60'
          : 'border-white/10 focus:border-brand-primary focus:ring-1 focus:ring-brand-primary'
      "
      @input="emit('update:modelValue', $event.target.value)"
    />
    <span v-if="error" class="text-[11px] text-red-400">{{ error }}</span>
    <span v-else-if="hint" class="text-[11px] text-brand-textMuted">{{ hint }}</span>
  </label>
</template>
