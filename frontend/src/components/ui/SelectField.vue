<script setup>
defineProps({
  modelValue: { type: [String, Number], default: '' },
  label: { type: String, default: '' },
  options: { type: Array, default: () => [] }, // [{ value, label }]
  placeholder: { type: String, default: '' },
  error: { type: String, default: '' },
  hint: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'change'])
</script>

<template>
  <label class="flex flex-col gap-1.5 w-full">
    <span v-if="label" class="text-[11px] uppercase tracking-wider font-semibold text-brand-textMuted">{{
      label
    }}</span>
    <div class="relative">
      <select
        :value="modelValue"
        :disabled="disabled"
        @change="
          emit('update:modelValue', $event.target.value);
          emit('change', $event.target.value)
        "
        class="app-select w-full bg-brand-background border rounded-app-sm py-2.5 px-3 text-sm text-brand-textMain outline-none transition-all disabled:opacity-50"
        :class="error ? 'border-red-400/60' : 'border-white/10 focus:border-brand-primary focus:ring-1 focus:ring-brand-primary'"
      >
        <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
        <option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
    </div>
    <span v-if="error" class="text-[11px] text-red-400">{{ error }}</span>
    <span v-else-if="hint" class="text-[11px] text-brand-textMuted">{{ hint }}</span>
  </label>
</template>

<style scoped>
.app-select {
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml;charset=utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.9rem center;
  background-size: 1em;
  padding-right: 2.2rem;
}
</style>
