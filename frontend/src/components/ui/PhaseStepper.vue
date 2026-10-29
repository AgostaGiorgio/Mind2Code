<script setup>
defineProps({
  modelValue: { type: String, default: null },
  // [{ value, label, short?, available, done, running, error }]
  options: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue'])

function select(option) {
  if (!option.available) return
  emit('update:modelValue', option.value)
}

function dotClass(option) {
  return option.done || option.running ? 'bg-emerald-400' : 'bg-white/15'
}

function labelClass(option, selected) {
  if (option.error) return 'text-red-400'
  if (option.running || selected) return 'text-brand-textMain'
  if (option.done) return 'text-brand-textMuted'
  if (option.available) return 'text-brand-textMuted group-hover:text-brand-textMain'
  return 'text-brand-textMuted/40'
}

function stateLabel(option) {
  if (option.error) return 'error'
  if (option.running) return 'running'
  return option.done ? 'done' : 'pending'
}
</script>

<template>
  <div
    class="flex w-full items-start overflow-x-auto hide-scrollbar px-0 pt-2 sm:px-2"
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
      :aria-label="`${opt.label}: ${stateLabel(opt)}`"
      @click="select(opt)"
    >
      <!-- Connector to the previous phase -->
      <span
        v-if="index > 0"
        class="absolute left-0 top-[6px] h-px w-1/2"
        :class="options[index - 1].done ? 'bg-emerald-400/40' : 'bg-white/10'"
        aria-hidden="true"
      />
      <!-- Connector to the next phase -->
      <span
        v-if="index < options.length - 1"
        class="absolute right-0 top-[6px] h-px w-1/2"
        :class="opt.done ? 'bg-emerald-400/40' : 'bg-white/10'"
        aria-hidden="true"
      />

      <span class="relative z-10 flex h-3 w-3 shrink-0 items-center justify-center">
        <!-- Pulsing halo for the phase currently running -->
        <span
          v-if="opt.running"
          class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400/60"
          aria-hidden="true"
        />

        <span
          class="relative flex h-3 w-3 items-center justify-center rounded-full transition-all duration-300"
          :class="[
            opt.error ? 'bg-red-500' : dotClass(opt),
            opt.error
              ? 'ring-4 ring-red-500/20'
              : modelValue === opt.value
                ? 'scale-110 ring-4 ring-emerald-400/20'
                : opt.available
                  ? 'group-hover:ring-4 group-hover:ring-emerald-400/10'
                  : '',
          ]"
        >
          <span
            v-if="modelValue === opt.value && !opt.error"
            class="h-1.5 w-1.5 rounded-full bg-brand-background"
          />
        </span>
      </span>

      <span
        class="whitespace-nowrap text-[10px] font-semibold leading-tight tracking-wide transition-colors sm:text-[11px]"
        :class="labelClass(opt, modelValue === opt.value)"
      >
        <span class="sm:hidden">{{ opt.short || opt.label }}</span>
        <span class="hidden sm:inline">{{ opt.label }}</span>
      </span>
    </button>
  </div>
</template>
