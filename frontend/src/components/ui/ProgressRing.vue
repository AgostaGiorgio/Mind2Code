<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: Number, required: true },
  size: { type: Number, default: 40 },
  stroke: { type: Number, default: 4 },
  // 'brand' (default) or 'warning' (orange, for the finalization progress).
  tone: { type: String, default: 'brand' },
})

const arcClass = computed(() =>
  props.tone === 'warning' ? 'text-amber-400' : 'text-brand-primary',
)

const clamped = computed(() => Math.min(100, Math.max(0, props.value)))
const center = computed(() => props.size / 2)
const radius = computed(() => (props.size - props.stroke) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)
const dashOffset = computed(() => circumference.value * (1 - clamped.value / 100))
const fontSize = computed(() => Math.round(props.size * 0.26))
</script>

<template>
  <div
    class="relative inline-flex shrink-0 items-center justify-center"
    :style="{ width: `${size}px`, height: `${size}px` }"
    role="img"
    :aria-label="`${clamped}% complete`"
  >
    <svg :width="size" :height="size" class="-rotate-90" aria-hidden="true">
      <circle
        :cx="center"
        :cy="center"
        :r="radius"
        fill="none"
        stroke="currentColor"
        :stroke-width="stroke"
        class="text-white/10"
      />
      <circle
        :cx="center"
        :cy="center"
        :r="radius"
        fill="none"
        stroke="currentColor"
        :stroke-width="stroke"
        stroke-linecap="round"
        class="transition-[stroke-dashoffset] duration-300 ease-out"
        :class="arcClass"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="dashOffset"
      />
    </svg>
    <span
      class="absolute font-bold tabular-nums text-brand-textMain"
      :style="{ fontSize: `${fontSize}px` }"
    >
      {{ clamped }}
    </span>
  </div>
</template>
