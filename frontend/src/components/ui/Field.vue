<script setup>
defineProps({
  modelValue: { type: [String, Number], default: '' },
  label: { type: String, default: '' },
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  error: { type: String, default: '' },
  inputmode: { type: String, default: undefined },
  step: { type: [String, Number], default: undefined },
  min: { type: [String, Number], default: undefined },
  max: { type: [String, Number], default: undefined },
  suffix: { type: String, default: '' },
  hint: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'blur'])
</script>

<template>
  <label class="flex flex-col gap-1.5 w-full">
    <span v-if="label" class="text-[11px] uppercase tracking-wider font-semibold text-brand-textMuted">{{
      label
    }}</span>
    <div class="relative">
      <input
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :inputmode="inputmode"
        :step="step"
        :min="min"
        :max="max"
        :disabled="disabled"
        @input="emit('update:modelValue', $event.target.value)"
        @blur="emit('blur')"
        class="w-full bg-brand-background border rounded-app-sm py-2.5 px-3 text-sm text-brand-textMain outline-none transition-all placeholder-brand-textMuted/40 disabled:opacity-50"
        :class="[
          error ? 'border-red-400/60' : 'border-white/10 focus:border-brand-primary focus:ring-1 focus:ring-brand-primary',
          suffix ? 'pr-12' : '',
        ]"
      />
      <span
        v-if="suffix"
        class="absolute right-3 top-1/2 -translate-y-1/2 text-brand-textMuted text-xs pointer-events-none"
        >{{ suffix }}</span
      >
    </div>
    <span v-if="error" class="text-[11px] text-red-400">{{ error }}</span>
    <span v-else-if="hint" class="text-[11px] text-brand-textMuted">{{ hint }}</span>
  </label>
</template>
