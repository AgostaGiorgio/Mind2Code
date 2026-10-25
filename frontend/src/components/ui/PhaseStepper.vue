<script setup>
defineProps({
  modelValue: { type: String, default: null },
  // [{ value, label, short?, available }]
  options: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue'])

function select(option) {
  if (!option.available) return
  emit('update:modelValue', option.value)
}
</script>

<template>
  <div
    class="flex w-full items-start overflow-x-auto hide-scrollbar pt-1.5 sm:px-2 sm:pt-2"
    role="group"
    aria-label="Project phases"
  >
    <button
      v-for="(opt, index) in options"
      :key="opt.value"
      type="button"
      class="group relative flex min-w-0 flex-1 flex-col items-center gap-2 px-0 pb-1 disabled:cursor-not-allowed sm:px-0.5"
      :disabled="!opt.available"
      :aria-pressed="modelValue === opt.value"
      :aria-label="`${opt.label}: ${
        !opt.available ? 'not available yet' : modelValue === opt.value ? 'selected' : 'available'
      }`"
      @click="select(opt)"
    >
      <!-- Connector to the previous phase -->
      <span
        v-if="index > 0"
        class="absolute left-0 top-[6px] h-px w-1/2"
        :class="options[index - 1].available ? 'bg-emerald-400/40' : 'bg-white/10'"
        aria-hidden="true"
      />
      <!-- Connector to the next phase -->
      <span
        v-if="index < options.length - 1"
        class="absolute right-0 top-[6px] h-px w-1/2"
        :class="opt.available ? 'bg-emerald-400/40' : 'bg-white/10'"
        aria-hidden="true"
      />

      <span
        class="relative z-10 flex h-3 w-3 shrink-0 items-center justify-center rounded-full transition-all duration-300"
        :class="[
          opt.available ? 'bg-emerald-400' : 'bg-white/15',
          modelValue === opt.value
            ? 'scale-110 ring-4 ring-emerald-400/20'
            : opt.available
              ? 'group-hover:ring-4 group-hover:ring-emerald-400/10'
              : '',
        ]"
        aria-hidden="true"
      >
        <span
          v-if="modelValue === opt.value"
          class="h-1.5 w-1.5 rounded-full bg-brand-background"
        />
      </span>

      <span
        class="whitespace-nowrap text-[10px] font-semibold leading-tight tracking-wide transition-colors sm:text-[11px]"
        :class="
          modelValue === opt.value
            ? 'text-brand-textMain'
            : opt.available
              ? 'text-brand-textMuted group-hover:text-brand-textMain'
              : 'text-brand-textMuted/40'
        "
      >
        <span class="sm:hidden">{{ opt.short || opt.label }}</span>
        <span class="hidden sm:inline">{{ opt.label }}</span>
      </span>
    </button>
  </div>
</template>
